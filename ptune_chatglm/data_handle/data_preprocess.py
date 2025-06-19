import json
# 返回的字符串包含有关异常的详细信
import traceback
import numpy as np
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer
from functools import partial
import sys
sys.path.append('..')  # 将上级目录加入路径，方便导入 glm_config

from glm_config import *  # 项目配置类（包含 tokenizer 路径等）


def convert_example(
        examples: dict,
        tokenizer,
        max_source_seq_len: int,
        max_target_seq_len: int,
    ):
    """
    将原始样本转换为模型可接受的输入格式，包括 input_ids 和 labels。

    Args:
        examples (dict): 批量样本，形如 { 'text': ['{"context":..., "target":...}', ...] }
        tokenizer: 预训练分词器实例
        max_source_seq_len (int): 输入部分最大 token 长度（含特殊符号）
        max_target_seq_len (int): 输出部分最大 token 长度（含特殊符号）

    Returns:
        dict: 包含 'input_ids' 和 'labels' 两个键，对应 numpy 数组
    """
    # 初始化存储结构
    tokenized_output = {
        'input_ids': [],  # 存储每条样本的输入 token id 列表
        'labels': []      # 存储每条样本的标签 token id 列表
    }

    # 总序列长度限制 = 输入 + 输出
    max_seq_length = max_source_seq_len + max_target_seq_len

    # 遍历每条原始样本
    for example in examples['text']:
        try:
            # 将 JSON 字符串转为 dict
            example = json.loads(example)
            context = example["context"]  # Prompt 文本
            target = example["target"]    # 模型应生成的文本

            # 对 context 部分进行编码（不自动添加特殊 token）
            prompts_ids = tokenizer.encode(
                text=context,
                add_special_tokens=False
            )

            # 对 target 部分进行编码
            target_ids = tokenizer.encode(
                text=target,
                add_special_tokens=False
            )

            # 如果 prompt 超长，保留前 max_source_seq_len-1 个 token，为后面留出 [gMASK]
            if len(prompts_ids) >= max_source_seq_len:
                prompts_ids = prompts_ids[:max_source_seq_len - 1]

            # 如果 target 超长，保留前 max_target_seq_len-2 个 token，为 <sop> 和 <eop> 留位
            if len(target_ids) >= max_target_seq_len - 1:
                target_ids = target_ids[:max_target_seq_len - 2]

            # 构建带有特殊 token 的完整输入序列： prompts + [gMASK] + target
            print("-----前")
            input_ids = tokenizer.build_inputs_with_special_tokens(prompts_ids, target_ids)
            print("input_ids:", input_ids)
            print("-----后")
            # 找到 BOS（<sop>）在 input_ids 中的位置，用于后续 labels 切分
            # context_length = input_ids.index(tokenizer.bos_token_id) # ❶ 旧写法（chatglm3-6b会报错）
            SOP_ID = tokenizer.get_command("sop")  # ❶ 获取 <sop>
            context_length = input_ids.index(SOP_ID)  # ❷ 用 <sop> 找分界
            # mask_position 指向 [gMASK] 的位置
            mask_position = context_length - 1

            # 构建 labels：
            # 前 context_length 个位置全为 -100（忽略），后面是真实的 target token
            labels = [-100] * context_length + input_ids[mask_position + 1:]

            # 计算需要的 padding 长度，以对齐到 max_seq_length
            pad_len = max_seq_length - len(input_ids)

            # 在 input_ids 和 labels 尾部添加 pad 或 -100
            input_ids = input_ids + [tokenizer.pad_token_id] * pad_len
            labels     = labels + [-100] * pad_len

            # 收集当前样本的结果
            tokenized_output['input_ids'].append(input_ids)
            tokenized_output['labels'].append(labels)

        except Exception:
            # 打印异常并跳过当前样本
            print(f'"{example}" -> {traceback.format_exc()}')
            continue

    # 将列表转换为 numpy 数组，方便后续 DataLoader 使用
    for k, v in tokenized_output.items():
        tokenized_output[k] = np.array(v)

    return tokenized_output


def get_max_length(
        tokenizer,
        dataset_file: str
    ):
    """
    统计数据集中 context 和 target 两部分的 token 长度分布，打印最大、平均和中位数。

    Args:
        tokenizer: 预训练分词器
        dataset_file (str): 数据文件路径，JSONL 格式
    """
    source_seq_len_list = []
    target_seq_len_list = []

    # 逐行读取文件并统计长度
    with open(dataset_file, 'r') as f:
        for line in tqdm(f.readlines()):
            line = json.loads(line)

            # 编码 context 部分并记录长度
            source_len = tokenizer.encode(line['context'])
            source_seq_len_list.append(len(source_len))

            # 编码 target 部分并记录长度
            target_len = tokenizer.encode(line['target'])
            target_seq_len_list.append(len(target_len))

    # 打印统计结果：最大、平均、中位
    print(dataset_file)
    print(f"【Source Sequence】 Max: {max(source_seq_len_list)}, Avg: {int(sum(source_seq_len_list) / len(source_seq_len_list))}, Middle: {sorted(source_seq_len_list)[len(source_seq_len_list)//2] }.")
    print(f"【Target Sequence】 Max: {max(target_seq_len_list)}, Avg: {int(sum(target_seq_len_list) / len(target_seq_len_list))}, Middle: {sorted(target_seq_len_list)[len(target_seq_len_list)//2] }.")
