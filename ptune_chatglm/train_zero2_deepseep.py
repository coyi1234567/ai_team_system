# -*- coding: utf-8 -*-
"""
train.py —— ChatGLM-3/6B LoRA 微调脚本（单机多卡 · DeepSpeed ZeRO-2 版）

❖ 设计目标
--------------------------------------------------------------------------
1. 彻底摆脱 nn.DataParallel OOM —— 换用 Accelerate + DeepSpeed ZeRO-2。
2. 代码零侵入：行数不超百，逻辑与原单卡脚本保持一致。
3. 行级中文注释，能直接当“教学版”阅读。
4. 通过 `python -m py_compile train.py` 语法检查。

使用流程
--------------------------------------------------------------------------
# 第一次
accelerate config     # 交互式 → multi-GPU / DeepSpeed / 指向 ds_config_zero2.json
# 训练
accelerate launch train.py

依赖
--------------------------------------------------------------------------
pip install torch>=2.2.0 deepspeed>=0.14 accelerate peft transformers==4.41.0
"""
from torch.utils.tensorboard import SummaryWriter
import os
from tqdm import tqdm
import traceback
import time
import argparse
from typing import Tuple, List
from transformers.trainer_pt_utils import get_parameter_names
from torch import nn
import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoConfig,
    AutoModel,
    get_scheduler,
)

import peft
# import deepspeed
from accelerate import Accelerator,DeepSpeedPlugin
from accelerate import DistributedType

# 项目自定义工具 & 配置
from utils.common_utils import CastOutputToFloat, second2time, save_model
from data_handle.data_loader import get_data
from glm_config import ProjectConfig

# ---------------------------------------------------------------------
# 一、统一超参数入口 —— ProjectConfig
# ---------------------------------------------------------------------
pc = ProjectConfig()  # 实例化后可从脚本外直接修改超参


# ---------------------------------------------------------------------
# 二、将模型 / TOKENIZER / 优化器 / 数据加载独立出函数
#    方便单元测试，保证主逻辑 main() 清爽
# ---------------------------------------------------------------------
def build_objects() -> Tuple[
    AutoTokenizer, torch.nn.Module, torch.optim.Optimizer, torch.optim.lr_scheduler.LRScheduler,
    DataLoader, DataLoader
]:
    """构造 tokenizer、模型、优化器、数据集等核心对象"""

    # 1) Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(pc.pre_model, trust_remote_code=True)

    # 2) Config（注入 p-tuning 前缀信息）
    config = AutoConfig.from_pretrained(pc.pre_model, trust_remote_code=True)
    if pc.use_ptuning:
        config.pre_seq_len = pc.pre_seq_len
        config.prefix_projection = pc.prefix_projection

    # 3) Model
    model = AutoModel.from_pretrained(pc.pre_model, config=config, trust_remote_code=True)
    # model = model.float()                                 # LoRA 需 fp32 权重
    model = model.half()                                 # LoRA 需 fp32 权重
    model.gradient_checkpointing_enable()                # 节省激活显存
    model.enable_input_require_grads()                   # 允许输入梯度（p-tuning）
    model.config.use_cache = False                       # 关闭 KV-cache 减显存
    if pc.use_ptuning:
        model.transformer.prefix_encoder.float()         # 前缀编码器也转 fp32

    # 4) 注入 LoRA
    if pc.use_lora:
        # ChatGLM3-6B 的 lm_head 在 transformer.output_layer
        model.transformer.output_layer = CastOutputToFloat(
            model.transformer.output_layer
        )
        lora_cfg = peft.LoraConfig(
            task_type=peft.TaskType.CAUSAL_LM,
            r=pc.lora_rank,
            lora_alpha=32,
            lora_dropout=0.1,
            inference_mode=False,
        )
        model = peft.get_peft_model(model, lora_cfg)

    # 5) DataLoader（train / dev）
    train_dl, dev_dl = get_data()

    # 6) Optimizer（按是否 weight-decay 分两组参数）
    # -------------------- 6) Optimizer --------------------

    # ① 利用 HF 官方工具，获取“所有不在指定归一化层（LayerNorm、RMSNorm）内”的参数名列表
    #    这些参数名将候选做 weight decay
    #    ——— 来源：transformers.trainer_pt_utils.get_parameter_names 实现文档  [oai_citation:0‡huggingface.co](https://huggingface.co/transformers/v4.5.1/_modules/transformers/trainer_pt_utils.html?utm_source=chatgpt.com)
    decay_keys = get_parameter_names(model, [nn.LayerNorm, nn.RMSNorm])

    # ② 再把名字包含 “bias” 的参数剔除掉，因为通常不对偏置做 weight decay
    #    （参见 AdamW 正则化原理及实践）  [oai_citation:1‡medium.com](https://medium.com/%40mridulrao674385/language-modelling-on-mps-using-pytorch-044a2dfd9f62?utm_source=chatgpt.com)
    decay_keys = [n for n in decay_keys if "bias" not in n]

    # ③ 构造两个参数组：
    optim_groups = [
        {
            # 3.1) 第一组：做 weight decay。
            #      条件：参数名在 decay_keys 中，且 requires_grad=True
            "params": [
                p for n, p in model.named_parameters()
                if n in decay_keys and p.requires_grad
            ],
            "weight_decay": pc.weight_decay,  # 例如 0.01
        },
        {
            # 3.2) 第二组：不做 weight decay
            #      条件：参数名不在 decay_keys 中，且 requires_grad=True
            "params": [
                p for n, p in model.named_parameters()
                if n not in decay_keys and p.requires_grad
            ],
            "weight_decay": 0.0,  # 对这些参数设 0 衰减
        },
    ]

    # ④ 深度学习框架或 DeepSpeed 在内部可能再次 flatten param groups
    #    若某组“params”列表为空，就会导致 torch.cat([], …) 报错：
    #    “torch.cat(): expected a non-empty list of Tensors”  [oai_citation:2‡discuss.huggingface.co](https://discuss.huggingface.co/t/why-get-parameter-names/76475?utm_source=chatgpt.com)
    #    因此在外层先把空组过滤掉，彻底消除此类错误
    optim_groups = [g for g in optim_groups if g["params"]]

    # ⑤ 用 AdamW 构造优化器，传入上述分组
    #    这样就能同时对“做衰减”和“不做衰减”的参数分别处理
    #    ——Hugging Face Trainer 也是类似分组策略  [oai_citation:3‡docs.oracle.com](https://docs.oracle.com/javase/7/docs/api/javax/xml/transform/Transformer.html?utm_source=chatgpt.com)
    optimizer = torch.optim.AdamW(optim_groups, lr=pc.learning_rate)
    # ------------------------------------------------------

    # 7) Scheduler
    warmup_steps = int(pc.warmup_ratio * len(train_dl) * pc.epochs)
    scheduler = get_scheduler(
        "linear", optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=len(train_dl) * pc.epochs,
    )

    return tokenizer, model, optimizer, scheduler, train_dl, dev_dl


# ---------------------------------------------------------------------
# 三、训练 & 评估
# ---------------------------------------------------------------------
def evaluate(engine, dl) -> float:
    """计算验证集平均 loss"""
    engine.eval()
    losses: List[float] = []
    with torch.no_grad():
        for batch in tqdm(dl, desc="Evaluating", leave=False):
            out = engine(
                input_ids=batch["input_ids"],
                labels=batch["labels"],
            )
            losses.append(out.loss.item())
    engine.train()
    return sum(losses) / len(losses)


def main() -> None:
    # 0) 创建 Accelerator（mixed_precision 可选 "fp16" / "bf16" / None）V100 只支持 FP16 A100 可选BF16
    # v0.20.x 开始 不再接受 config_file 参数
    ds_plugin = DeepSpeedPlugin(zero_stage=2)
    accelerator = Accelerator(
        log_with="tensorboard",
        project_dir=pc.log_dir,
        mixed_precision="fp16",
        deepspeed_plugin=ds_plugin
    )

    # 诊断
    if accelerator.distributed_type == DistributedType.DEEPSPEED:
        print(f"✅ running with DeepSpeed, world size = {accelerator.num_processes}")

    else:
        raise RuntimeError(f"unexpected distributed backend: {accelerator.distributed_type}")

    try:

        # 1) 准备对象
        tok, model, optim, sched, train_dl, dev_dl = build_objects()

        # 只在主进程打开 SummaryWriter，并算总步数用于 ETA
        writer = None
        if accelerator.is_main_process:
            writer = SummaryWriter(log_dir=pc.log_dir)


        # # 2) 配置 accelerator ZeRO-2

        # 3) Accelerator.prepare —— 负责 DDP 进程组、eRO-2 包装，amp、device 放置
        model, optim, sched, train_dl, dev_dl = accelerator.prepare(
            model, optim, sched, train_dl, dev_dl
        )

        #prepare(train_dl) 之后再计算；否则 DataLoader 被子进程分片(sharding)后长度会变化。
        steps_per_epoch = len(train_dl)
        total_steps = steps_per_epoch * pc.epochs

        # 4. 训练循环：自动梯度累积
        best_loss = float("inf")
        global_step = 0 # ← 全局步数
        tic = time.time()

        # 训练循环前：只清一次初始梯度，防止第一次 forward/backward 时累积到旧梯度。
        optim.zero_grad(set_to_none=True)  # ← 挪到最外层
        for epoch in range(1, pc.epochs + 1):
            # train_dl.sampler.set_epoch(epoch)  # ★ 保证各 rank 随 epoch 同步洗牌
            epoch_step = 0  # ← 每个 epoch 一开始就重置

            for batch in train_dl:
            # with accelerator.accumulate(model):
                epoch_step += 1

                # 前向 & 损失（ZeRO-2 + bf16 已自动混合精度）
                outputs = model(
                    input_ids=batch["input_ids"],
                    labels=batch["labels"],
                )
                # loss = outputs.loss / pc.grad_accum
                # 梯度累积达到 grad_accum 再更新
                loss = outputs.loss # DeepSpeed 已做必要缩放
                accelerator.backward(loss)  # AMP + all-reduce

                if accelerator.sync_gradients:  # 只有同步步进来
                    # 在优化器 step 之前裁剪梯度，防止梯度过大
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0, norm_type=2.0)
                    optim.step();
                    sched.step();
                    optim.zero_grad()  # 每批都调用，DS 内部判定跳过

                # 只有 DeepSpeed 判定到“累积够 k 步，已同步梯度”时才会返回 True
                if accelerator.sync_gradients:

                    global_step += 1

                    # 日志
                    if global_step % pc.logging_steps == 0:
                        # 1) 计算速度和 ETA
                        speed = pc.logging_steps / (time.time() - tic)
                        left = total_steps - global_step
                        eta = second2time(int(left / speed)) if speed else "∞"
                        pct = global_step / total_steps * 100

                        # 2) 构造并打印文本
                        text = (f"[E{epoch}] "
                                f"step {epoch_step}/{steps_per_epoch} | "
                                f"global {global_step}/{total_steps} ({pct:5.2f}%) | "
                                f"loss {loss.item():.4f} | {speed:.2f} step/s | ETA {eta} s")
                        # 1) 写入tensorboard
                        # 确保只有主进程有且仅有一个 SummaryWriter：
                        # 标量
                        if writer is not None:
                            writer.add_scalar("train/loss", loss.item(), global_step)
                            writer.add_scalar("train/speed", speed, global_step)
                            writer.add_scalar("train/pct", pct, global_step)


                            # 文本
                            if global_step % 100 == 0:
                                writer.add_text("train/log", text, global_step)
                        # 2) 同时打印到控制台
                        print(text)
                        tic = time.time()

                    # 保存 + 评估
                    # 所有进程在这里同步屏障，确保不会出现死锁
                    if global_step % pc.save_freq == 0:
                        accelerator.wait_for_everyone()  # ① 评估起点屏障

                        # 仅主进程进行评估与保存
                        # if accelerator.is_main_process:
                        model.eval()
                        eval_loss_local = evaluate(model, dev_dl)  # ② 每个 rank 都跑 forward
                        model.train()

                        # 将各 rank 的损失聚合到主进程并求全局平均
                        loss_tensor = torch.tensor([eval_loss_local], device=accelerator.device)
                        eval_loss = accelerator.gather(loss_tensor).mean().item()

                        accelerator.wait_for_everyone()  # ② 评估结束屏障

                        if accelerator.is_main_process and eval_loss < best_loss:  # ④ 只有 rank0 写磁盘
                            best_loss = eval_loss
                            base_path = os.path.join(pc.save_dir, "best")
                            unwrapped = accelerator.unwrap_model(model) # 只主进程 unwrap & 保存

                            # 1. 保存 P-Tuning 前缀
                            if pc.use_ptuning:
                                ptune_dir = os.path.join(base_path, "ptuning")
                                os.makedirs(ptune_dir, exist_ok=True)
                                torch.save(
                                    unwrapped.transformer.prefix_encoder.state_dict(),
                                    os.path.join(ptune_dir, "prefix_encoder.bin")
                                )
                                print(f"✔ Saved Prefix Encoder to {ptune_dir}")

                            # 2. 保存 LoRA Adapter
                            if pc.use_lora:
                                lora_dir = os.path.join(base_path, "lora")
                                os.makedirs(lora_dir, exist_ok=True)
                                accelerator.unwrap_model(model).save_pretrained(lora_dir)  # adapter_config.json + adapter_model.bin
                                tok.save_pretrained(lora_dir)  # tokenizer 文件
                                print(f"✔ Saved LoRA Adapter to {lora_dir}")

                            # 3. 合并 LoRA 并保存完整模型
                            merged_dir = os.path.join(base_path, "merged")
                            os.makedirs(merged_dir, exist_ok=True)

                            from peft import PeftModel
                            if pc.use_lora:
                                # ① 重新加载纯 base model
                                base_model = AutoModel.from_pretrained(
                                    pc.pre_model,
                                    trust_remote_code=True,
                                    config=unwrapped.config
                                )

                                # ② 把 LoRA adapter 挂回去 ----★
                                peft_model = PeftModel.from_pretrained(
                                    model=base_model,  # ★ 第一位必须显式写关键词，避免位置冲突
                                    model_id=lora_dir  # ★ 第二位是 adapter 路径
                                )

                                # ③ 合并后卸载 LoRA ----★
                                merged_model = peft_model.merge_and_unload()
                            else:
                                merged_model = unwrapped  # 纯 P-Tuning 时复用原模型

                            # 保存最终模型
                            merged_model.save_pretrained(merged_dir)  # config.json + pytorch_model.bin
                            tok.save_pretrained(merged_dir)
                            print(f"✔ Saved merged model to {merged_dir}")
                            text1 = f"✔ Saved best checkpoint to {merged_dir} (eval loss={eval_loss:.4f})"
                            # 文本
                            if writer is not None:
                                writer.add_text("dev/log", text1, global_step)
                            print(text1)

                        # —— 所有进程在这里再次同步，防止 Rank1 跳过去出现 deadlock
                        accelerator.wait_for_everyone()

    except Exception as e:
        if accelerator.is_main_process:
            print("训练过程中发生异常：", e)
            traceback.print_exc()
        raise
    finally:
        # 无论中途退出还是跑完，都能安全执行
        if writer is not None:
            writer.close()
        # 如果需要，也可显式释放 accelerator 相关资源（通常不必）
        # accelerator.end_training()  # 若有此方法可调用

# ---------------------------------------------------------------------
# 四、脚本入口
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()