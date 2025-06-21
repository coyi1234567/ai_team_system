#!/bin/bash

echo "正在修复VLLM依赖问题..."

# 卸载可能冲突的包
pip uninstall -y transformers vllm

# 安装兼容版本的transformers
pip install transformers==4.36.2

# 安装vllm
pip install vllm==0.2.5

# 安装其他必要的依赖
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pandas==2.1.4

echo "依赖修复完成！"
echo "现在可以运行: uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000" 