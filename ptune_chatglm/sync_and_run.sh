#!/bin/bash

# 远程服务器配置
REMOTE_HOST="my32gpu_2"
REMOTE_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm"

echo "🚀 同步文件到远程服务器并执行修复..."

# 同步文件到远程服务器
echo "📤 同步文件到远程服务器..."
rsync -avz --progress \
    fix_vllm_deps.sh \
    fix_vllm_deps.py \
    start_vllm_server.sh \
    test_vllm_server.py \
    requirements_vllm.txt \
    VLLM_SERVER_README.md \
    "${REMOTE_HOST}:${REMOTE_PATH}/"

if [ $? -eq 0 ]; then
    echo "✅ 文件同步成功"
else
    echo "❌ 文件同步失败"
    exit 1
fi

# 在远程服务器上执行修复
echo "🔧 在远程服务器上执行依赖修复..."
ssh "${REMOTE_HOST}" "cd ${REMOTE_PATH} && chmod +x fix_vllm_deps.sh && ./fix_vllm_deps.sh"

if [ $? -eq 0 ]; then
    echo "✅ 依赖修复完成"
    echo ""
    echo "🎉 现在可以在远程服务器上启动VLLM服务器："
    echo "ssh ${REMOTE_HOST}"
    echo "cd ${REMOTE_PATH}"
    echo "./start_vllm_server.sh"
else
    echo "❌ 依赖修复失败"
    exit 1
fi 