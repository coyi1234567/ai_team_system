# debug_convert.py
from data_handle.data_preprocess import convert_example
from transformers import AutoTokenizer
from glm_config import ProjectConfig

cfg = ProjectConfig()
tok = AutoTokenizer.from_pretrained(cfg.pre_model, trust_remote_code=True)

# 只取前 3 条原始字符串
with open(cfg.train_path, 'r', encoding='utf-8') as f:
    raws = [l.strip() for l in f if l.strip()][:3]

out = convert_example(
    {'text': raws},
    tok,
    cfg.max_source_seq_len,
    cfg.max_target_seq_len
)
print("输出 shapes:", {k: v.shape for k, v in out.items()})