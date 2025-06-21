import os
from transformers import AutoModel, AutoTokenizer
from peft import PeftModel

base_model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/data/models/chatglm3-6b"
lora_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3/best/lora"
merged_model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3/best/merged"

# 判断是否已融合（支持 bin 和 safetensors）
def is_merged_model_exist(merged_model_path):
    if not os.path.exists(merged_model_path):
        return False
    for fname in os.listdir(merged_model_path):
        if fname.endswith(".safetensors") or fname == "pytorch_model.bin":
            return True
    return False

if is_merged_model_exist(merged_model_path):
    print(f"检测到已融合模型: {merged_model_path}，无需重复融合。")
else:
    # 加载 base model
    base_model = AutoModel.from_pretrained(base_model_path, trust_remote_code=True)
    # 加载 LoRA adapter
    model = PeftModel.from_pretrained(base_model, lora_path)
    # 融合
    merged_model = model.merge_and_unload()
    # 保存
    os.makedirs(merged_model_path, exist_ok=True)
    merged_model.save_pretrained(merged_model_path)
    # 保存 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
    tokenizer.save_pretrained(merged_model_path)
    print("融合完成，已保存到：", merged_model_path)