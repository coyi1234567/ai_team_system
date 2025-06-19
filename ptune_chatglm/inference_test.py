from transformers import AutoTokenizer, AutoModel
device = 'cuda:1'
model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune/model_800"

tokenizer = AutoTokenizer.from_pretrained(
    model_path, trust_remote_code=True
)
model = AutoModel.from_pretrained(
    model_path, trust_remote_code=True
).half().to(device)
model = model.eval()
# 单轮对话
response, history = model.chat(tokenizer, "你好，ChatGLM3！", history=[])
print(response)  # 会输出模型的回复