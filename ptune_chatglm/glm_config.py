# -*- coding:utf-8 -*-
import torch


class ProjectConfig(object):
    """
    项目配置类，用于集中管理模型微调与训练相关的超参数和文件路径。
    """
    def __init__(self):
        # 设备选择：优先使用CUDA，如果不可用则回退到CPU
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device_ids = list(range(torch.cuda.device_count()))  # [0,1]

        # 预训练模型路径：指定 ChatGLM-3 6B 模型所在本地目录
        self.pre_model = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/data/models/chatglm3-6b'

        # 训练与验证数据路径：jsonl 格式的数据文件
        self.train_path = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/data/mixed_train_dataset.jsonl'
        self.dev_path   = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/data/mixed_dev_dataset.jsonl'

        # ——LoRA / P-Tuning 相关配置——
        # 是否启用 LoRA 技术
        self.use_lora    = True
        # LoRA 低秩分解的秩大小，控制可训练参数量
        self.lora_rank   = 8
        # 是否启用 P-Tuning 模式
        self.use_ptuning = False
        # P-Tuning 中 prompt 前缀长度
        self.pre_seq_len = 64

        # ——训练超参数——
        # 微调时的批次大小
        self.batch_size      = 2
        # 训练轮数（epoch）
        self.epochs          = 2
        # 梯度累积步数
        self.grad_accum          = 8
        # 学习率
        # self.learning_rate   = 3e-5
        self.learning_rate   = 1e-5
        # 权重衰减（L2 正则化）系数
        self.weight_decay    = 0
        # 学习率预热比例，用于生成 warmup steps
        self.warmup_ratio    = 0.06

        # 文本序列最大长度设置
        # 输入（prompt）部分允许的最大 token 数
        self.max_source_seq_len = 300
        # 输出（target）部分允许的最大 token 数
        self.max_target_seq_len = 400

        # 日志与模型保存相关设置
        # 每训练多少步打印一次日志
        self.logging_steps = 10
        # 每训练多少步保存一次模型
        self.save_freq     = 200
        # P-Tuning v2 中是否使用前缀投影
        self.prefix_projection = False  # False: 经典 P-Tuning；True: P-Tuning v2

        # 微调后模型检查点保存目录
        self.save_dir = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3'
        # self.save_dir = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/train_half_duo'
        # 给 Accelerator 添 logging_dir Accelerate 0.20 起强制要求log_with="tensorboard" 两者成对出现。
        self.log_dir = '/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/logs'


if __name__ == '__main__':
    # 测试配置是否正确加载与打印保存目录
    pc = ProjectConfig()
    print(pc.save_dir)  # 输出：'/home/ubuntu/data/.../checkpoints/ptune'
