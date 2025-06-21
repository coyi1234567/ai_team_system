#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd):
    """运行命令并打印输出"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def main():
    print("正在修复VLLM依赖问题...")
    
    # 卸载可能冲突的包
    print("\n1. 卸载冲突的包...")
    run_command("pip uninstall -y transformers vllm")
    
    # 安装兼容版本的transformers
    print("\n2. 安装兼容版本的transformers...")
    if not run_command("pip install transformers==4.36.2"):
        print("安装transformers失败")
        return
    
    # 安装vllm
    print("\n3. 安装vllm...")
    if not run_command("pip install vllm==0.2.5"):
        print("安装vllm失败")
        return
    
    # 安装其他必要的依赖
    print("\n4. 安装其他依赖...")
    run_command("pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pandas==2.1.4")
    
    print("\n✅ 依赖修复完成！")
    print("现在可以运行: uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main() 