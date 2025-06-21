# -*- coding: utf-8 -*-
"""
train.py —— ChatGLM-3/6B LoRA 微调脚本（单机多卡 · DeepSpeed ZeRO-3 版）

❖ 设计目标
--------------------------------------------------------------------------
1. 彻底摆脱 nn.DataParallel OOM —— 换用 Accelerate + DeepSpeed ZeRO-3。
2. 代码零侵入：行数不超百，逻辑与原单卡脚本保持一致。
3. 行级中文注释，能直接当"教学版"阅读。
4. 通过 `python -m py_compile train.py` 语法检查。

使用流程
--------------------------------------------------------------------------
# 第一次
accelerate config     # 交互式 → multi-GPU / DeepSpeed / 指向 ds_config_zero2.json
# 训练
accelerate launch train_zero3_deepseep_3.py --do_train
# 合并LoRA权重
python train_zero3_deepseep_3.py --merge_lora

依赖
--------------------------------------------------------------------------
pip install torch>=2.2.0 deepspeed>=0.14 accelerate peft transformers==4.41.0
"""

# -------------------- 依赖导入 --------------------
from accelerate import Accelerator, DeepSpeedPlugin, DistributedType  # 分布式训练核心库
from transformers import AutoTokenizer, AutoModel, AdamW, get_scheduler  # HuggingFace核心工具
from torch.utils.data import DataLoader  # 数据加载
import torch  # PyTorch
import peft  # LoRA微调库
from utils.common_utils import CastOutputToFloat, second2time, save_model  # 项目自定义工具
from data_handle.data_loader import get_data  # 数据加载函数
from glm_config import ProjectConfig  # 超参数配置
from torch.utils.tensorboard import SummaryWriter  # 日志
from transformers.trainer_pt_utils import get_parameter_names  # 参数分组工具
from torch import nn
import time
import os
import traceback
import argparse

# -------------------- 超参数配置 --------------------
pc = ProjectConfig()  # 实例化配置对象，集中管理所有超参数

# -------------------- 构建核心对象 --------------------
def build_objects(resume_lora_dir=None, batch_size=None, epochs=None, learning_rate=None):
    """
    构建tokenizer、模型、优化器、数据集等核心对象，支持断点续训和超参数覆盖。
    参数：
        resume_lora_dir: 断点续训时LoRA Adapter目录
        batch_size/epochs/learning_rate: 可选，命令行覆盖超参数
    返回：tokenizer, model, optimizer, scheduler, train_dl, dev_dl
    """
    # 1. 加载分词器和原始模型
    tokenizer = AutoTokenizer.from_pretrained(pc.pre_model, trust_remote_code=True)
    model = AutoModel.from_pretrained(pc.pre_model, trust_remote_code=True)
    model = model.half()  # 半精度节省显存
    model.gradient_checkpointing_enable()  # 启用梯度检查点，进一步省显存
    model.enable_input_require_grads()  # 允许输入梯度（P-Tuning等需要）
    model.config.use_cache = False  # 关闭KV-cache，节省显存

    # 2. 命令行参数覆盖超参数
    if batch_size is not None:
        pc.batch_size = batch_size
    if epochs is not None:
        pc.epochs = epochs
    if learning_rate is not None:
        pc.learning_rate = learning_rate

    # 3. 注入LoRA结构，并支持断点续训
    if pc.use_lora:
        model.transformer.output_layer = CastOutputToFloat(model.transformer.output_layer)
        lora_cfg = peft.LoraConfig(
            task_type=peft.TaskType.CAUSAL_LM,
            r=pc.lora_rank,
            lora_alpha=32,
            lora_dropout=0.1,
            inference_mode=False,
        )
        model = peft.get_peft_model(model, lora_cfg)
        # 断点续训：自动加载已有LoRA权重
        lora_ckpt = resume_lora_dir or os.path.join(pc.save_dir, "best", "lora")
        if os.path.exists(lora_ckpt) and os.path.exists(os.path.join(lora_ckpt, "adapter_model.bin")):
            print(f"[LOG] 检测到已有LoRA权重，自动加载: {lora_ckpt}")
            model = peft.PeftModel.from_pretrained(model, lora_ckpt)

    # 4. 加载数据集
    train_dl, dev_dl = get_data()

    # 5. 优化器参数分组（是否weight decay）
    decay_keys = get_parameter_names(model, [nn.LayerNorm, nn.RMSNorm])
    decay_keys = [n for n in decay_keys if "bias" not in n]
    optim_groups = [
        {
            "params": [p for n, p in model.named_parameters() if n in decay_keys and p.requires_grad],
            "weight_decay": pc.weight_decay,
        },
        {
            "params": [p for n, p in model.named_parameters() if n not in decay_keys and p.requires_grad],
            "weight_decay": 0.0,
        },
    ]
    optim_groups = [g for g in optim_groups if g["params"]]
    optimizer = AdamW(optim_groups, lr=pc.learning_rate)

    # 6. 学习率调度器
    warmup_steps = int(pc.warmup_ratio * len(train_dl) * pc.epochs)
    scheduler = get_scheduler(
        "linear", optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=len(train_dl) * pc.epochs,
    )

    return tokenizer, model, optimizer, scheduler, train_dl, dev_dl

# -------------------- 验证集评估 --------------------
def evaluate(engine, dl):
    """
    计算验证集平均loss。
    参数：engine: 模型；dl: 验证集DataLoader
    返回：平均loss
    """
    engine.eval()
    losses = []
    with torch.no_grad():
        for batch in dl:
            out = engine(
                input_ids=batch["input_ids"],
                labels=batch["labels"],
            )
            losses.append(out.loss.item())
    engine.train()
    return sum(losses) / len(losses)

# -------------------- 训练主流程 --------------------
def train_main(args):
    """
    训练主流程，支持分布式、断点续训、超参数覆盖。
    参数：args: 命令行参数对象
    """
    # 1. 创建Accelerator对象，配置分布式/混合精度/DeepSpeed
    ds_plugin = DeepSpeedPlugin(zero_stage=3)
    accelerator = Accelerator(
        log_with="tensorboard",
        project_dir=pc.log_dir,
        mixed_precision="fp16",
        deepspeed_plugin=ds_plugin
    )

    # 2. 分布式诊断
    if accelerator.distributed_type == DistributedType.DEEPSPEED:
        print(f"✅ running with DeepSpeed, world size = {accelerator.num_processes}")
    else:
        raise RuntimeError(f"unexpected distributed backend: {accelerator.distributed_type}")

    writer = None
    try:
        # 3. 构建核心对象（支持断点续训/超参数覆盖）
        tok, model, optim, sched, train_dl, dev_dl = build_objects(
            resume_lora_dir=args.resume_lora_dir,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate
        )

        # 4. 只在主进程写日志
        if accelerator.is_main_process:
            writer = SummaryWriter(log_dir=pc.log_dir)

        # 5. Accelerator准备分布式环境
        model, optim, sched, train_dl, dev_dl = accelerator.prepare(
            model, optim, sched, train_dl, dev_dl
        )

        steps_per_epoch = len(train_dl)
        total_steps = steps_per_epoch * pc.epochs

        best_loss = float("inf")  # 最优loss
        global_step = 0
        tic = time.time()

        optim.zero_grad(set_to_none=True)  # 清初始梯度
        for epoch in range(1, pc.epochs + 1):
            epoch_step = 0
            for batch in train_dl:
                with accelerator.accumulate(model):  # 支持梯度累积
                    epoch_step += 1
                    outputs = model(
                        input_ids=batch["input_ids"],
                        labels=batch["labels"],
                    )
                    loss = outputs.loss
                    accelerator.backward(loss)

                    if accelerator.sync_gradients:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0, norm_type=2.0)
                        optim.step()
                        sched.step()
                        optim.zero_grad()

                    if accelerator.sync_gradients:
                        global_step += 1
                        # 日志与进度条
                        if global_step % pc.logging_steps == 0:
                            speed = pc.logging_steps / (time.time() - tic)
                            left = total_steps - global_step
                            eta = second2time(int(left / speed)) if speed else "∞"
                            pct = global_step / total_steps * 100
                            text = (f"[E{epoch}] "
                                    f"step {epoch_step}/{steps_per_epoch} | "
                                    f"global {global_step}/{total_steps} ({pct:5.2f}%) | "
                                    f"loss {loss.item():.4f} | {speed:.2f} step/s | ETA {eta} s")
                            if writer is not None:
                                writer.add_scalar("train/loss", loss.item(), global_step)
                                writer.add_scalar("train/speed", speed, global_step)
                                writer.add_scalar("train/pct", pct, global_step)
                            print(text)
                            tic = time.time()

                        # 保存与评估
                        if global_step % pc.save_freq == 0:
                            model.eval()
                            eval_loss_local = evaluate(model, dev_dl)
                            model.train()

                            loss_tensor = torch.tensor([eval_loss_local], device=accelerator.device)
                            eval_loss = accelerator.gather(loss_tensor).mean().item()

                            accelerator.wait_for_everyone()

                            if accelerator.is_main_process and eval_loss < best_loss:
                                print("[LOG] 开始保存 best checkpoint ...")
                                best_loss = eval_loss
                                base_path = os.path.join(pc.save_dir, "best")
                                unwrapped = accelerator.unwrap_model(model)

                                # 保存P-Tuning前缀
                                if pc.use_ptuning:
                                    ptune_dir = os.path.join(base_path, "ptuning")
                                    print(f"[LOG] 开始保存 Prefix Encoder 到 {ptune_dir}")
                                    os.makedirs(ptune_dir, exist_ok=True)
                                    torch.save(
                                        unwrapped.transformer.prefix_encoder.state_dict(),
                                        os.path.join(ptune_dir, "prefix_encoder.bin")
                                    )
                                    print(f"[LOG] Prefix Encoder 保存完成")

                                # 保存LoRA Adapter
                                if pc.use_lora:
                                    lora_dir = os.path.join(base_path, "lora")
                                    print(f"[LOG] 开始保存 LoRA Adapter 到 {lora_dir}")
                                    os.makedirs(lora_dir, exist_ok=True)
                                    accelerator.unwrap_model(model).save_pretrained(lora_dir)
                                    tok.save_pretrained(lora_dir)
                                    print(f"[LOG] LoRA Adapter 保存完成")

                            accelerator.wait_for_everyone()

        # 训练循环结束后，强制保存一次最终模型，防止遗漏
        if accelerator.is_main_process:
            print("[LOG] 训练结束，强制保存最终 best checkpoint ...")
            base_path = os.path.join(pc.save_dir, "best")
            unwrapped = accelerator.unwrap_model(model)
            if pc.use_lora:
                lora_dir = os.path.join(base_path, "lora")
                print(f"[LOG] 训练结束，保存 LoRA Adapter 到 {lora_dir}")
                os.makedirs(lora_dir, exist_ok=True)
                accelerator.unwrap_model(model).save_pretrained(lora_dir)
                tok.save_pretrained(lora_dir)
                print(f"[LOG] LoRA Adapter 保存完成")

    except Exception as e:
        if accelerator.is_main_process:
            print("训练过程中发生异常：", e)
            traceback.print_exc()
            # 异常时也尝试保存当前模型，最大程度保留成果
            try:
                base_path = os.path.join(pc.save_dir, "best")
                unwrapped = accelerator.unwrap_model(model)
                if pc.use_lora:
                    lora_dir = os.path.join(base_path, "lora")
                    print(f"[LOG] 异常退出，保存 LoRA Adapter 到 {lora_dir}")
                    os.makedirs(lora_dir, exist_ok=True)
                    accelerator.unwrap_model(model).save_pretrained(lora_dir)
                    tok.save_pretrained(lora_dir)
                    print(f"[LOG] LoRA Adapter 保存完成")
            except Exception as e2:
                print("[LOG] 异常保存模型时再次出错：", e2)
        raise
    finally:
        if writer is not None:
            writer.close()

# -------------------- LoRA权重合并 --------------------
def merge_and_unload_lora(base_model_dir, lora_dir, merged_save_dir):
    """
    合并LoRA权重到原始模型，并保存为单一模型。
    参数：
        base_model_dir: 原始模型目录
        lora_dir: LoRA Adapter目录
        merged_save_dir: 融合后模型保存目录
    """
    print(f"[LOG] 开始合并并保存完整模型到 {merged_save_dir}")
    os.makedirs(merged_save_dir, exist_ok=True)
    from peft import PeftModel
    from transformers import AutoModel, AutoTokenizer
    # 1. 加载原始模型
    base_model = AutoModel.from_pretrained(
        base_model_dir,
        trust_remote_code=True
    )
    # 2. 加载LoRA Adapter
    peft_model = PeftModel.from_pretrained(
        base_model,
        lora_dir
    )
    # 3. 合并权重
    print("[LOG] merge_and_unload 开始")
    merged_model = peft_model.merge_and_unload()
    print("[LOG] merge_and_unload 完成，开始 save_pretrained")
    # 4. 保存融合后模型
    merged_model.save_pretrained(merged_save_dir)
    # 5. 保存tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_dir, trust_remote_code=True)
    tokenizer.save_pretrained(merged_save_dir)
    print(f"[LOG] 完整模型保存完成: {merged_save_dir}")

# -------------------- 脚本主入口 --------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--do_train', action='store_true', help='执行训练')
    parser.add_argument('--merge_lora', action='store_true', help='合并LoRA权重')
    parser.add_argument('--base_model_dir', type=str, default=pc.pre_model, help='原始模型目录')
    parser.add_argument('--lora_dir', type=str, default=os.path.join(pc.save_dir, "best", "lora"), help='LoRA Adapter目录')
    parser.add_argument('--merged_save_dir', type=str, default=os.path.join(pc.save_dir, "best", "merged"), help='融合后模型保存目录')
    # 新增断点续训和超参数覆盖
    parser.add_argument('--resume_lora_dir', type=str, default=None, help='断点续训LoRA权重目录')
    parser.add_argument('--batch_size', type=int, default=None, help='覆盖批次大小')
    parser.add_argument('--epochs', type=int, default=None, help='覆盖训练轮数')
    parser.add_argument('--learning_rate', type=float, default=None, help='覆盖学习率')
    args = parser.parse_args()

    if args.do_train:
        train_main(args)
    if args.merge_lora:
        merge_and_unload_lora(args.base_model_dir, args.lora_dir, args.merged_save_dir)

# 训练（分布式/多卡）：
#   accelerate launch train_zero3_deepseep_3.py --do_train
# 合并LoRA权重（单机即可）：
#   python train_zero3_deepseep_3.py --merge_lora
# 可选参数：
#   --base_model_dir 原始模型路径 --lora_dir LoRA路径 --merged_save_dir 融合后模型保存路径