#!/bin/bash

# 远程服务器信息
REMOTE_HOST="my32gpu_2"
REMOTE_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm"

echo "🔍 检查远程服务器配置..."

# 检查连接
echo "1. 检查SSH连接..."
if ssh -o ConnectTimeout=5 "${REMOTE_HOST}" "echo 'SSH连接正常'" > /dev/null 2>&1; then
    echo "✅ SSH连接正常"
else
    echo "❌ SSH连接失败"
    echo "请检查SSH配置或服务器地址"
    exit 1
fi

# 检查环境
echo "2. 检查conda环境..."
ssh "${REMOTE_HOST}" "source /home/ubuntu/miniconda/bin/activate && conda env list | grep dl_env" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ dl_env环境存在"
else
    echo "❌ dl_env环境不存在"
    echo "请先创建dl_env环境"
    exit 1
fi

# 检查模型路径
echo "3. 检查模型路径..."
MODEL_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3/best/merged"
if ssh "${REMOTE_HOST}" "[ -d '${MODEL_PATH}' ]"; then
    echo "✅ 模型路径存在: ${MODEL_PATH}"
else
    echo "❌ 模型路径不存在: ${MODEL_PATH}"
    echo "请检查模型路径配置"
fi

# 检查GPU
echo "4. 检查GPU状态..."
ssh "${REMOTE_HOST}" "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits"

# 检查依赖
echo "5. 检查Python依赖..."
ssh "${REMOTE_HOST}" "source /home/ubuntu/miniconda/bin/activate dl_env && pip list | grep -E '(transformers|vllm|fastapi)'"

echo "✅ 配置检查完成！" 