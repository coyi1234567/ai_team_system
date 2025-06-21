#!/bin/bash

# 远程服务器信息
REMOTE_HOST="my32gpu_2"
REMOTE_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm"

echo "🔧 远程修复VLLM依赖问题..."

# 创建远程修复命令
REMOTE_COMMANDS="
cd ${REMOTE_PATH}
source /home/ubuntu/miniconda/bin/activate dl_env
echo '正在修复VLLM依赖问题...'
pip uninstall -y transformers vllm
pip install transformers==4.36.2
pip install vllm==0.2.5
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pandas==2.1.4
echo '依赖修复完成！'
echo '现在可以运行: uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000'
"

# 执行远程命令
ssh "${REMOTE_HOST}" "${REMOTE_COMMANDS}"

echo "✅ 远程修复完成！" 