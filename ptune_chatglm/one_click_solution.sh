#!/bin/bash

echo "🎯 VLLM服务器一键解决方案"
echo "================================"

# 检查配置
echo "1️⃣ 检查服务器配置..."
./check_config.sh

if [ $? -ne 0 ]; then
    echo "❌ 配置检查失败，请先解决配置问题"
    exit 1
fi

echo ""
echo "2️⃣ 修复依赖问题..."
./remote_fix.sh

if [ $? -ne 0 ]; then
    echo "❌ 依赖修复失败"
    exit 1
fi

echo ""
echo "3️⃣ 启动VLLM服务器..."
echo "服务器将在后台启动，请等待模型加载..."
echo ""

# 在后台启动服务器
./remote_start.sh &
SERVER_PID=$!

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 30

# 检查服务器是否启动成功
echo "4️⃣ 检查服务器状态..."
if curl -s "http://my32gpu_2:8000/docs" > /dev/null 2>&1; then
    echo "✅ 服务器启动成功！"
    echo ""
    echo "🌐 服务器信息："
    echo "   - 地址: http://my32gpu_2:8000"
    echo "   - API文档: http://my32gpu_2:8000/docs"
    echo "   - 进程ID: $SERVER_PID"
    echo ""
    echo "5️⃣ 运行测试..."
    ./remote_test.sh
    
    echo ""
    echo "🎉 一键解决方案完成！"
    echo "服务器正在运行，按 Ctrl+C 停止服务器"
    
    # 等待用户中断
    wait $SERVER_PID
else
    echo "❌ 服务器启动失败"
    echo "请检查错误日志或手动启动: ./remote_start.sh"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi 