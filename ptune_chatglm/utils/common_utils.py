# -*- coding: utf-8 -*-
"""
common_utils.py

目的：定义数据类型转换类、时间格式转换函数以及模型保存函数。
"""
# 导入 PyTorch 及相关模块
import torch  # PyTorch 核心包，用于张量运算和自动求导
import torch.nn as nn  # 神经网络模块，包含常用层定义

# 导入项目配置类，以获取超参数配置
from glm_config import ProjectConfig
# 导入 copy 模块，用于深度复制模型
import copy

# 实例化配置对象，方便获取 LoRA 参数以及保存路径等设置
pc = ProjectConfig()


class CastOutputToFloat(nn.Sequential):
    """
    CastOutputToFloat 继承自 nn.Sequential，目的是将模块输出统一转为 float32。
    在启用了混合精度（FP16）训练时，部分操作可能输出 FP16 张量，
    通过此类可以在输出阶段统一转换为更高精度，方便后续计算。
    """
    def forward(self, x):
        # 调用父类 forward 计算输出，并使用 to() 方法强制转换为 torch.float32
        return super().forward(x).to(torch.float32)


def second2time(seconds: int) -> str:
    """
    将给定的秒数转换为 "HH:MM:SS" 格式的字符串。

    Args:
        seconds (int): 总的秒数

    Returns:
        str: 格式化后的时:分:秒 字符串，时、分、秒均为两位数，
             不足两位时补零。
    """
    # divmod 可同时返回商和余数，先计算分钟和剩余秒数
    m, s = divmod(seconds, 60)
    # 再计算小时和剩余分钟
    h, m = divmod(m, 60)
    # 使用格式化字符串，保证两位输出
    return "%02d:%02d:%02d" % (h, m, s)


def save_model(
        model: nn.Module,
        cur_save_dir: str
    ) -> None:
    """
    根据配置，将当前模型保存到指定目录。
    如果开启了 LoRA，则先合并 LoRA 参数再保存；否则直接保存原模型。

    Args:
        model (nn.Module): 待保存的模型对象，可能包含 LoRA 子模块
        cur_save_dir (str): 保存目录路径，需要提前存在或可写
    """
    # 判断是否启用了 LoRA 微调
    if pc.use_lora:
        # 1. 深度拷贝模型，避免在合并时修改原模型结构
        merged_model = copy.deepcopy(model)
        # 2. 调用 merge_and_unload() 方法，将所有 LoRA 参数融合回原模型权重，
        #    并卸载 LoRA 子模块，得到一个普通的 Transformer 模型
        merged_model = merged_model.merge_and_unload()
        # 3. 将合并后的模型按 Hugging Face 格式保存
        merged_model.save_pretrained(cur_save_dir)
    else:
        # 未启用 LoRA，直接调用 save_pretrained 保存当前模型权重
        model.save_pretrained(cur_save_dir)
