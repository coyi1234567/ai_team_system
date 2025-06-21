#!/bin/bash

# 远程服务器信息
REMOTE_HOST="my32gpu_2"
REMOTE_PATH="/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm"
SERVER_URL="http://118.89.243.20:8000"  # 使用服务器的公网IP

echo "🧪 远程测试VLLM服务器..."

# 检查服务器是否运行
echo "🔍 检查服务器状态..."
if curl -s "${SERVER_URL}/docs" > /dev/null 2>&1; then
    echo "✅ 服务器运行正常"
else
    echo "❌ 服务器未运行或无法访问"
    echo "请先启动服务器: ./remote_start.sh"
    exit 1
fi

# 创建测试脚本
cat > temp_test.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time

SERVER_URL = "http://118.89.243.20:8000"  # 使用服务器的公网IP

def test_server_health():
    try:
        response = requests.get(f"{SERVER_URL}/docs")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return False

def test_single_generate():
    print("\n🧪 测试单个推理...")
    
    payload = {
        "prompts": ["请简单介绍一下人工智能"],
        "max_tokens": 50,
        "temperature": 0.8,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 单个推理成功")
            print(f"输入: {payload['prompts'][0]}")
            print(f"输出: {result['results'][0]}")
        else:
            print(f"❌ 单个推理失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    print("🚀 VLLM服务器远程测试开始...")
    print(f"服务器地址: {SERVER_URL}")
    
    if not test_server_health():
        return
    
    test_single_generate()
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
EOF

# 运行测试
echo "🧪 执行测试..."
python temp_test.py

# 清理临时文件
rm temp_test.py

echo "✅ 远程测试完成！" 