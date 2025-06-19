# coding:utf-8
# 导入 PyTorch 的 DataLoader，用于批量加载数据
from torch.utils.data import DataLoader
# 导入 Hugging Face 提供的默认数据拼接器和分词器工具
from transformers import default_data_collator, AutoTokenizer
# 导入之前编写的数据预处理函数
from data_handle.data_preprocess import *
# 导入项目配置类，集中管理路径及超参
from glm_config import ProjectConfig
from datasets import load_dataset  # 加载数据集
from functools import partial  # 用于函数柯里化/固定参数
import os
# 实例化项目配置，获取模型路径、数据路径及超参数
pc = ProjectConfig()

# 加载预训练分词器，trust_remote_code=True 允许加载模型仓库中的自定义 tokenizer 实现
tokenizer = AutoTokenizer.from_pretrained(
    pc.pre_model,
    trust_remote_code=True
)

def get_data():
    """
    构建并返回训练与验证数据加载器。

    Returns:
        train_dataloader: 训练集的 DataLoader
        dev_dataloader: 验证集的 DataLoader
    """
    # 使用 Hugging Face datasets 加载本地 JSONL 数据，返回一个包含 train 和 dev 集的 DatasetDict

    # """	•	load_dataset('text', …)
    # 使用 Hugging Face datasets 库的“通用文本”加载器（text），它会将每行当作一个字符串读取。
    #     •	data_files 参数
    # 通过一个字典指定两个不同的文件路径：
    #     •	'train': 训练集的 JSONL 文件路径
    #     •	'dev'  : 验证集（开发集）的 JSONL 文件路径
    #     •	返回值：DatasetDict
    # dataset 是一个包含两个键（'train'、'dev'）的字典，值分别是对应的 Dataset 对象。此时每条记录只有一个字段 text，其中存放了原始的 JSON 串。
    # """

    dataset = load_dataset(
        'text',
        data_files={
            'train': pc.train_path,
            'dev': pc.dev_path
        }
    )

    #     """	•	convert_example
    # 是你在 data_preprocess.py 中定义的函数，用于将原始 JSON 串解析成模型可用的 input_ids 和 labels 两个数组。
    #     •	functools.partial
    # 它的作用是“预绑定”或“柯里化”函数的部分参数，生成一个新函数 new_func，调用时只需提供剩下的 examples 参数。
    #     •	为什么要这么做？
    # 这样在后续调用 dataset.map(new_func, batched=True) 时，就能一次性传入批量数据，由 datasets 库自动给 convert_example 补上 tokenizer、max_source_seq_len、max_target_seq_len 这三个固定参数。"""

    # 使用 functools.partial 将 convert_example 函数封装，固定 tokenizer 和序列长度参数
    new_func = partial(
        convert_example,
        tokenizer=tokenizer,
        max_source_seq_len=pc.max_source_seq_len,
        max_target_seq_len=pc.max_target_seq_len
    )

    # 对 train 和 dev 数据分别执行 map 操作，batched=True 按批次调用 new_func
    # """	•	dataset.map(...)
    # 对字典中每个子集（train 和 dev）分别调用一次。
    #     •	batched=True
    # 表示传给 new_func 的不是一条一条的示例，而是一批（batch）示例。datasets 会把若干行的 text 放到一个列表中，作为 examples['text'] 传入。
    #     •	new_func
    # 就是上一步用 partial 得到的、已经绑定了分词器和最大长度参数的 convert_example。
    #     •	remove_columns=['text']
    # 执行完映射后，把原来的 text 列删除，只保留预处理后产生的 input_ids 和 labels 列。
    #
    # 结果：dataset 仍是一个 DatasetDict，但每个分支中的元素变成了：{
    #   'input_ids': [...],   # numpy array 或列表
    #   'labels':    [...],   # numpy array 或列表
    #   # 可能还有其他你在 convert_example 中返回的字段
    # }"""
    dataset = dataset.map(
        new_func,
        batched=True,
        remove_columns=['text']  # map 后移除原始 text 列，保留 input_ids/labels
        # load_from_cache_file = False  # 每次都强制重新执行 convert_example
    )

    # 分别获取处理后的训练集与验证集
    train_dataset = dataset['train']
    dev_dataset   = dataset['dev']
    print(">> 映射后训练集样本数：", len(dataset['train']))
    print(">> 映射后验证集样本数：", len(dataset['dev']))

    # 创建训练用 DataLoader
    # shuffle=True 随机打乱，collate_fn 使用默认的批量拼接器自动处理 padding
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=pc.batch_size,
        shuffle=True,
        drop_last=True,
        collate_fn=default_data_collator,
        num_workers=os.cpu_count() // 2,  # 根据机器性能可调整，用于并行加载# 推荐用一半逻辑核数
        pin_memory=True  # 提升 GPU 数据拷贝效率
    )

    # 创建验证用 DataLoader，不打乱，其他设置与训练相同
    dev_dataloader = DataLoader(
        dev_dataset,
        drop_last=False,
        batch_size=pc.batch_size,
        shuffle=False,
        collate_fn=default_data_collator,
        num_workers=0,
        pin_memory=False  # 提升 GPU 数据拷贝效率
    )

    return train_dataloader, dev_dataloader

if __name__ == '__main__':
    # 仅在脚本直接执行时运行以下测试代码
    train_loader, dev_loader = get_data()

    # 打印每个 epoch 的步骤数
    print("训练集 batch 数:", len(train_loader))
    print("验证集 batch 数:", len(dev_loader))

    # 取训练集第一个 batch，打印其键与张量形状，验证数据结构
    for batch in train_loader:
        print("Batch keys:", batch.keys())
        print("input_ids shape:", batch['input_ids'].shape)
        print("labels    shape:", batch['labels'].shape)
        # 只打印第一个 batch
        break
