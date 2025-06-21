#!/usr/bin/env python3
"""
LoRA模型合并脚本
用于将训练好的LoRA adapter合并到基础模型中
"""

import os
import torch
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
from glm_config import ProjectConfig
import argparse

pc = ProjectConfig()

def merge_lora_model(lora_path, output_path, base_model_path=None):
    """
    合并LoRA模型到基础模型
    
    Args:
        lora_path: LoRA adapter路径
        output_path: 合并后的模型保存路径
        base_model_path: 基础模型路径，如果为None则使用配置文件中的路径
    """
    if base_model_path is None:
        base_model_path = pc.pre_model
    
    print(f"🔧 开始合并LoRA模型...")
    print(f"   基础模型: {base_model_path}")
    print(f"   LoRA路径: {lora_path}")
    print(f"   输出路径: {output_path}")
    
    # 加载基础模型
    print("📥 加载基础模型...")
    base_model = AutoModel.from_pretrained(
        base_model_path,
        trust_remote_code=True,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # 加载tokenizer
    print("📥 加载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
    
    # 加载LoRA adapter
    print("📥 加载LoRA adapter...")
    peft_model = PeftModel.from_pretrained(
        model=base_model,
        model_id=lora_path
    )
    
    # 合并模型
    print("🔗 合并LoRA到基础模型...")
    merged_model = peft_model.merge_and_unload()
    
    # 保存合并后的模型
    print(f"💾 保存合并后的模型到 {output_path}...")
    os.makedirs(output_path, exist_ok=True)
    merged_model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    
    print("✅ LoRA模型合并完成!")
    print(f"   合并后的模型已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="合并LoRA模型")
    parser.add_argument("--lora_path", type=str, required=True, help="LoRA adapter路径")
    parser.add_argument("--output_path", type=str, required=True, help="合并后的模型保存路径")
    parser.add_argument("--base_model_path", type=str, default=None, help="基础模型路径（可选）")
    
    args = parser.parse_args()
    
    # 检查LoRA路径是否存在
    if not os.path.exists(args.lora_path):
        print(f"❌ 错误: LoRA路径不存在: {args.lora_path}")
        return
    
    try:
        merge_lora_model(args.lora_path, args.output_path, args.base_model_path)
    except Exception as e:
        print(f"❌ 合并过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 