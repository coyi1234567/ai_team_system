#!/usr/bin/env python3
"""
代理配置文件 - 提供多种HF镜像和代理方案
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent

def setup_hf_mirrors():
    """设置HF镜像源"""
    
    # 国内镜像源列表
    mirrors = [
        "https://hf-mirror.com",  # 官方镜像
        "https://huggingface.co",  # 原始地址
        "https://hf-mirror.com",   # 备用镜像
    ]
    
    # 设置环境变量
    os.environ["HF_ENDPOINT"] = mirrors[0]
    os.environ["HF_HUB_URL"] = mirrors[0]
    os.environ["HF_HOME"] = str(BASE_DIR / "models")
    os.environ["TRANSFORMERS_CACHE"] = str(BASE_DIR / "models")
    os.environ["HF_DATASETS_CACHE"] = str(BASE_DIR / "models")
    
    # 离线模式设置
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    
    print(f"✅ 已设置HF镜像: {mirrors[0]}")
    print(f"✅ 已启用离线模式")

def setup_http_proxy(proxy_url: str = None):
    """设置HTTP代理"""
    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        print(f"✅ 已设置HTTP代理: {proxy_url}")
    else:
        # 常见的代理地址（需要根据实际情况修改）
        common_proxies = [
            "http://127.0.0.1:7890",  # Clash默认端口
            "http://127.0.0.1:1080",  # 常见代理端口
            "http://127.0.0.1:8080",  # 常见代理端口
        ]
        
        for proxy in common_proxies:
            try:
                import requests
                response = requests.get("https://huggingface.co", 
                                      proxies={"http": proxy, "https": proxy}, 
                                      timeout=5)
                if response.status_code == 200:
                    os.environ["HTTP_PROXY"] = proxy
                    os.environ["HTTPS_PROXY"] = proxy
                    print(f"✅ 自动检测到可用代理: {proxy}")
                    break
            except:
                continue

def setup_offline_mode():
    """强制设置离线模式"""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    print("✅ 已强制设置离线模式")

def get_proxy_config():
    """获取当前代理配置"""
    return {
        "HF_ENDPOINT": os.environ.get("HF_ENDPOINT"),
        "HF_HUB_URL": os.environ.get("HF_HUB_URL"),
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        "HTTP_PROXY": os.environ.get("HTTP_PROXY"),
        "HTTPS_PROXY": os.environ.get("HTTPS_PROXY"),
        "TRANSFORMERS_CACHE": os.environ.get("TRANSFORMERS_CACHE"),
    }

if __name__ == "__main__":
    print("🔧 代理配置工具")
    print("1. 设置HF镜像")
    print("2. 设置HTTP代理")
    print("3. 设置离线模式")
    print("4. 显示当前配置")
    
    choice = input("请选择 (1-4): ")
    
    if choice == "1":
        setup_hf_mirrors()
    elif choice == "2":
        proxy_url = input("请输入代理地址 (如 http://127.0.0.1:7890): ")
        setup_http_proxy(proxy_url if proxy_url else None)
    elif choice == "3":
        setup_offline_mode()
    elif choice == "4":
        config = get_proxy_config()
        for key, value in config.items():
            print(f"  {key}: {value}")
    else:
        print("无效选择") 