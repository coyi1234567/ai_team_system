#!/usr/bin/env python3
import requests
import json
import time

# 服务器配置
SERVER_URL = "http://localhost:8000"

def test_server_health():
    """测试服务器是否启动"""
    try:
        response = requests.get(f"{SERVER_URL}/docs")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        return False

def test_batch_generate():
    """测试批量推理接口"""
    print("\n🧪 测试批量推理接口...")
    
    test_prompts = [
        "你好，请介绍一下自己",
        "今天天气怎么样？",
        "请写一首关于春天的诗"
    ]
    
    payload = {
        "prompts": test_prompts,
        "max_new_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 批量推理成功")
            print(f"输入提示数量: {len(test_prompts)}")
            print(f"输出结果数量: {len(result['results'])}")
            
            # 显示部分结果
            for i, (prompt, result_text) in enumerate(zip(test_prompts, result['results'])):
                print(f"\n--- 测试 {i+1} ---")
                print(f"输入: {prompt}")
                print(f"输出: {result_text[:100]}...")
        else:
            print(f"❌ 批量推理失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，可能是模型加载时间较长")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_single_generate():
    """测试单个推理"""
    print("\n🧪 测试单个推理...")
    
    payload = {
        "prompts": ["请简单介绍一下人工智能"],
        "max_new_tokens": 50,
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
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    print("🚀 VLLM服务器测试开始...")
    print(f"服务器地址: {SERVER_URL}")
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(3)
    
    # 测试服务器健康状态
    if not test_server_health():
        print("\n💡 请先启动服务器:")
        print("uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # 测试单个推理
    test_single_generate()
    
    # 测试批量推理
    test_batch_generate()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 