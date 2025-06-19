# -*- coding:utf-8 -*-
import os  # 操作系统接口，用于处理文件路径等
import time  # 时间管理，用于计算训练耗时和 ETA
import copy  # 对模型进行深拷贝，避免修改原模型
import argparse  # 解析命令行参数（可选扩展）
from functools import partial  # 用于将函数部分参数固定
import peft  # PEFT（Parameter-Efficient Fine-Tuning）库，用于 LoRA
import torch
import torch.nn as nn
from utils.common_utils import CastOutputToFloat

# autocast 是 PyTorch 混合精度训练的上下文管理器
# 在 GPU 上开启混合精度可加速训练并节省显存，CPU 上无效果
from torch.cuda.amp import autocast as autocast

# Transformers 一体化接口
from transformers import (
    AutoTokenizer,       # 自动加载 tokenizer
    AutoConfig,          # 自动加载模型配置
    AutoModel,           # 自动加载预训练模型
    get_scheduler        # 学习率调度器
)

# 引入自定义工具函数：时间格式转换、保存模型等
from utils.common_utils import second2time, save_model
# 引入数据加载函数
from data_handle.data_loader import get_data
# 项目配置类，集中管理路径及超参数
from glm_config import ProjectConfig

# 实例化配置，读取预训练模型路径、LoRA/P-tuning 选项、超参等
pc = ProjectConfig()


def model2train():
    """
    构建模型、优化器及调度器，执行训练循环，并在指定频率保存模型和评估。
    """
    # 1. 加载 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        pc.pre_model,
        trust_remote_code=True  # 允许加载自定义实现
    )

    # 2. 加载模型配置
    config = AutoConfig.from_pretrained(
        pc.pre_model,
        trust_remote_code=True
    )

    # 3. 如果使用 P-tuning，则在 config 中注入前缀长度与投影方式
    if pc.use_ptuning:
        config.pre_seq_len = pc.pre_seq_len
        config.prefix_projection = pc.prefix_projection

    # 4. 加载预训练模型
    model = AutoModel.from_pretrained(
        pc.pre_model,
        config=config,
        trust_remote_code=True
    )

    # 5. 转为 float32 精度（确保兼容 LoRA/PEFT） .half()
    model = model.float()
    # >>> torch.int8   (GPTQ 用 int4/int8 打包在 char = int8)
    # 6. 开启梯度检查点以节省显存
    model.gradient_checkpointing_enable()
    # 7. 允许输入 embedding 计算梯度，用于 P-tuning
    model.enable_input_require_grads()
    # 8. 禁用自带缓存，降低显存使用
    model.config.use_cache = False

    # 9. 如果使用 P-tuning，需要将前缀编码器也转为 float
    if pc.use_ptuning:
        model.transformer.prefix_encoder.float()

    # 10. 如果使用 LoRA 微调：封装 lm_head，使其输出为 float32；构建 LoRA 配置并应用 PEFT
    if pc.use_lora:
        # a. lm_head 输出转 float

        # model.lm_head = CastOutputToFloat(model.lm_head)
        # ChatGLM3-6B 正确写法
        model.transformer.output_layer = CastOutputToFloat(model.transformer.output_layer)

        # b. 构造 LoRA 配置
        peft_config = peft.LoraConfig(
            task_type=peft.TaskType.CAUSAL_LM,  # 因果语言建模任务
            inference_mode=False,               # 训练阶段关闭推理优化
            r=pc.lora_rank,                     # LoRA 低秩矩阵秩
            lora_alpha=32,                      # LoRA 缩放系数
            lora_dropout=0.1,                   # LoRA dropout 比例
        )
        # c. 获取 LoRA 微调后的模型
        model = peft.get_peft_model(model, peft_config)

    # 11. 将模型移动到指定设备（GPU/CPU）
    model = model.to(pc.device)
    # 11a. 多卡并行
    model = nn.DataParallel(model)

    # print('22222')
    # print(model.transformer.layers[0].attention.query_key_value.weight.dtype)
    # >>> torch.int8   (GPTQ 用 int4/int8 打包在 char = int8)
    print(f'model--》{model}')
    # 打印可训练参数信息
    #print('模型训练参数：', model.print_trainable_parameters())
    # 打印可训练参数信息（兼容 DataParallel）
    real_model = model.module if isinstance(model, nn.DataParallel) else model
    print('模型训练参数：', real_model.print_trainable_parameters())

    # —— 构造优化器 & 学习率调度器 —— #
    # 12. 按是否衰减参数分组：bias 与 LayerNorm.weight 不进行 weight decay
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [
                p for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": pc.weight_decay,
        },
        {
            "params": [
                p for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]
    optimizer = torch.optim.AdamW(
        optimizer_grouped_parameters,
        lr=pc.learning_rate
    )

    # 13. 加载训练/验证数据
    train_dataloader, dev_dataloader = get_data()
    # 14. 计算总训练步数与 warmup 步数
    num_update_steps_per_epoch = len(train_dataloader)
    max_train_steps = pc.epochs * num_update_steps_per_epoch
    warm_steps = int(pc.warmup_ratio * max_train_steps)
    # 15. 构造线性学习率调度器
    lr_scheduler = get_scheduler(
        name='linear',
        optimizer=optimizer,
        num_warmup_steps=warm_steps,
        num_training_steps=max_train_steps,
    )

    # —— 训练循环 —— #
    loss_list = []
    tic_train = time.time()
    global_step = 0
    best_eval_loss = float('inf')

    for epoch in range(1, pc.epochs + 1):
        for batch in train_dataloader:
            # 16. 前向 + loss 计算
            if pc.use_lora:
                # LoRA 时启用混合精度
                with autocast():
                    outputs = model(
                        input_ids=batch['input_ids'].to(device=pc.device, dtype=torch.long),
                        labels=batch['labels'].to(device=pc.device, dtype=torch.long)
                    )
                    loss = outputs.loss
            else:
                outputs = model(
                    input_ids=batch['input_ids'].to(device=pc.device, dtype=torch.long),
                    labels=batch['labels'].to(device=pc.device, dtype=torch.long)
                )
                loss = outputs.loss

            # 17. 反向 + 参数更新 + 学习率更新
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            lr_scheduler.step()

            # 18. 记录 loss 并推进 global_step
            loss_list.append(loss.item())
            global_step += 1

            # 19. 日志输出：每 logging_steps 步打印一次平均 loss、训练速度与 ETA
            if global_step % pc.logging_steps == 0:
                time_diff = time.time() - tic_train
                loss_avg = sum(loss_list) / len(loss_list)
                eta = second2time(
                    int((max_train_steps - global_step)
                        / (pc.logging_steps / time_diff))
                )
                print(
                    f"global step {global_step} "
                    f"({global_step/max_train_steps*100:02.2f}%), "
                    f"epoch {epoch}, loss {loss_avg:.5f}, "
                    f"speed {pc.logging_steps/time_diff:.2f} step/s, "
                    f"ETA {eta}"
                )
                tic_train = time.time()
                loss_list.clear()

            # 20. 定期保存模型 & 在验证集上评估
            if global_step % pc.save_freq == 0:
                cur_save_dir = os.path.join(pc.save_dir, f"model_{global_step}")
                # save_model(model, cur_save_dir)
                # tokenizer.save_pretrained(cur_save_dir)
                print(f"Model has saved at {cur_save_dir}.")

                eval_loss = evaluate_model(model, dev_dataloader)
                print(f"Evaluation Loss: {eval_loss:.5f}")

                if eval_loss < best_eval_loss:
                    print(
                        f"Min eval loss updated: "
                        f"{best_eval_loss:.5f} --> {eval_loss:.5f}"
                    )
                    best_eval_loss = eval_loss
                    best_dir = os.path.join(pc.save_dir, "model_best")
                    # 保存时取底层 module
                    #real_model = model.module if isinstance(model, nn.DataParallel) else model
                    save_model(real_model, cur_save_dir)
                    tokenizer.save_pretrained(cur_save_dir)
                    print(f"Best model has saved at {best_dir}.")

                tic_train = time.time()



def evaluate_model(model, dev_dataloader):
    """
    在验证集上计算平均 loss，用于模型评估与早停判断。

    Args:
        model: 训练中的模型实例
        dev_dataloader: 验证集 DataLoader

    Returns:
        float: 验证集上的平均 loss
    """
    model.eval()  # 切换到评估模式（关闭 dropout 等）
    loss_list = []

    # 禁用梯度计算，加速并节省显存
    with torch.no_grad():
        for batch in dev_dataloader:
            if pc.use_lora:
                with autocast():
                    outputs = model(
                        input_ids=batch['input_ids'].to(device=pc.device, dtype=torch.long),
                        labels=batch['labels'].to(device=pc.device, dtype=torch.long)
                    )
                    loss = outputs.loss
            else:
                outputs = model(
                    input_ids=batch['input_ids'].to(device=pc.device, dtype=torch.long),
                    labels=batch['labels'].to(device=pc.device, dtype=torch.long)
                )
                loss = outputs.loss

            loss_list.append(loss.item())

    model.train()  # 恢复到训练模式
    return sum(loss_list) / len(loss_list)


if __name__ == '__main__':
    # 脚本入口：直接调用训练函数
    model2train()