#!/bin/bash

# 远程服务器信息
REMOTE_HOST="my32gpu_2"
REMOTE_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm"

echo "🚀 远程启动VLLM服务器..."

# 检查服务器连接
echo "🔍 检查服务器连接..."
if ! ssh -o ConnectTimeout=5 "${REMOTE_HOST}" "echo '连接成功'" > /dev/null 2>&1; then
    echo "❌ 无法连接到远程服务器: ${REMOTE_HOST}"
    echo "请检查SSH配置和网络连接"
    exit 1
fi

echo "✅ 服务器连接正常"

# 远程启动命令
REMOTE_START_COMMANDS="
cd ${REMOTE_PATH}
echo '🚀 启动VLLM服务器...'
echo '服务器将在 http://0.0.0.0:8000 启动'
echo 'API文档: http://0.0.0.0:8000/docs'
echo ''
echo '按 Ctrl+C 停止服务器'
echo ''
source /home/ubuntu/miniconda/bin/activate dl_env
uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000
"

# 执行远程启动
echo "🌐 正在启动VLLM服务器..."
ssh -t "${REMOTE_HOST}" "${REMOTE_START_COMMANDS}" 