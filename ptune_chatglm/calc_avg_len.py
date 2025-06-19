# calc_avg_len.py
# -*- coding:utf-8 -*-
import json
from transformers import AutoTokenizer
from glm_config import ProjectConfig

def main():
    # 1. 加载配置和 tokenizer
    pc = ProjectConfig()
    tokenizer = AutoTokenizer.from_pretrained(
        pc.pre_model,
        trust_remote_code=True
    )

    # 2. 逐行读取训练集 jsonl
    total_src, total_tgt, count = 0, 0, 0
    with open(pc.train_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            context = obj['context']
            target  = obj['target']

            # 3. 分别编码并累加长度
            src_ids = tokenizer.encode(context, add_special_tokens=False)
            tgt_ids = tokenizer.encode(target,  add_special_tokens=False)
            total_src += len(src_ids)
            total_tgt += len(tgt_ids)
            count += 1

    # 4. 计算平均并输出
    avg_src = total_src / count
    avg_tgt = total_tgt / count
    print(f"avg_source_len = {avg_src:.2f}")
    print(f"avg_target_len = {avg_tgt:.2f}")
    print(f"avg_source_len + avg_target_len = {avg_src + avg_tgt:.2f}")

if __name__ == "__main__":
    main()