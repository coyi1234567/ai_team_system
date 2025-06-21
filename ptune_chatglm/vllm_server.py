import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from vllm import LLM, SamplingParams
import pandas as pd
import tempfile

app = FastAPI()

# 允许跨域，方便前端本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模型加载
merged_model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3/best/merged"
llm = LLM(
    model=merged_model_path,
    trust_remote_code=True,
    dtype="float16",
    tensor_parallel_size=2
    # 没有写 tensor_parallel_size，默认用所有可见卡 tensor_parallel_size=2
)

class BatchInferRequest(BaseModel):
    prompts: List[str]
    max_tokens: int = 512
    temperature: float = 0.95
    top_p: float = 0.7

@app.post("/api/generate")
async def generate(req: BatchInferRequest):
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p
    )
    outputs = llm.generate(req.prompts, sampling_params)
    results = [out.outputs[0].text for out in outputs]
    return {"results": results}

@app.post("/api/uploadfile/")
async def upload_file(file: UploadFile = File(...), max_tokens: int = Form(128), temperature: float = Form(0.95), top_p: float = Form(0.7)):
    # 支持 txt/csv 文件
    suffix = file.filename.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    prompts = []
    if suffix == "txt":
        with open(tmp_path, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    elif suffix == "csv":
        df = pd.read_csv(tmp_path)
        # 假设第一列为 prompt
        prompts = df.iloc[:, 0].dropna().astype(str).tolist()
    else:
        return {"error": "仅支持 txt/csv 文件"}

    os.remove(tmp_path)
    # 推理
    sampling_params = SamplingParams(
        max_tokens=int(max_tokens),
        temperature=float(temperature),
        top_p=float(top_p)
    )
    outputs = llm.generate(prompts, sampling_params)
    results = [out.outputs[0].text for out in outputs]
    return {"results": results, "prompts": prompts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)