import requests

SERVER_URL = "http://127.0.0.1:8000"  # 替换为你的服务器地址

def call_generate():
    url = f"{SERVER_URL}/api/generate"
    data = {
        "prompts": ["你好，介绍一下你自己", "什么是人工智能？"],
        "max_tokens": 128,  # 修复：max_new_tokens -> max_tokens
        "temperature": 0.95,
        "top_p": 0.7
    }
    resp = requests.post(url, json=data)
    print("状态码：", resp.status_code)
    print("原始返回内容：", resp.text)
    try:
        print("生成接口返回：", resp.json())
    except Exception as e:
        print("解析JSON失败：", e)

def call_uploadfile(file_path):
    url = f"{SERVER_URL}/api/uploadfile/"
    files = {'file': open(file_path, 'rb')}
    data = {
        "max_tokens": 128,  # 修复：max_new_tokens -> max_tokens
        "temperature": 0.95,
        "top_p": 0.7
    }
    resp = requests.post(url, files=files, data=data)
    print("状态码：", resp.status_code)
    print("原始返回内容：", resp.text)
    try:
        print("文件上传接口返回：", resp.json())
    except Exception as e:
        print("解析JSON失败：", e)

if __name__ == "__main__":
    # 调用文本生成接口
    print("=== 测试文本生成接口 ===")
    call_generate()
    
    print("\n=== 测试文件上传接口 ===")
    # 调用文件上传接口（请替换为你的 txt 或 csv 文件路径）
    call_uploadfile("test.txt") 