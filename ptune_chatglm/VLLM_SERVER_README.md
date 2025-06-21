# VLLM 服务器设置指南

## 🚀 快速开始（远程服务器）

### 方法1: 一键解决方案（推荐）
```bash
./one_click_solution.sh
```
这个脚本会自动完成：配置检查 → 依赖修复 → 服务器启动 → 功能测试

### 方法2: 分步操作

#### 1. 检查服务器配置
```bash
./check_config.sh
```

#### 2. 远程修复依赖
```bash
./remote_fix.sh
```

#### 3. 远程启动服务器
```bash
./remote_start.sh
```

#### 4. 远程测试服务器
```bash
./remote_test.sh
```

#### 5. 完整同步和修复
```bash
./sync_and_run.sh
```

### 方法3: 手动SSH操作
```bash
# 1. 连接到服务器
ssh my32gpu_2

# 2. 激活环境并修复依赖
cd /home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm
conda activate dl_env
pip uninstall -y transformers vllm
pip install transformers==4.36.2
pip install vllm==0.2.5
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pandas==2.1.4

# 3. 启动服务器
uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000
```

---

## 脚本说明

### 远程操作脚本
- `one_click_solution.sh` - 一键解决方案（推荐）
- `check_config.sh` - 检查服务器配置
- `remote_fix.sh` - 远程修复依赖
- `remote_start.sh` - 远程启动服务器
- `remote_test.sh` - 远程测试服务器
- `sync_and_run.sh` - 同步文件并修复

### 本地脚本
- `fix_vllm_deps.sh` - 本地依赖修复脚本
- `fix_vllm_deps.py` - Python版本修复脚本
- `start_vllm_server.sh` - 本地启动脚本
- `test_vllm_server.py` - 本地测试脚本

---

## 问题描述
运行 `uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000` 时遇到以下错误：
```
ImportError: cannot import name 'CLIPVisionModel' from 'transformers'
```

这是因为 `transformers` 库版本与 `vllm` 不兼容导致的。

## 解决方案

### 方法1: 使用修复脚本（推荐）

#### Bash脚本
```bash
# 在dl_env环境中运行
./fix_vllm_deps.sh
```

#### Python脚本
```bash
# 在dl_env环境中运行
python fix_vllm_deps.py
```

### 方法2: 手动修复

1. 卸载冲突的包：
```bash
pip uninstall -y transformers vllm
```

2. 安装兼容版本的transformers：
```bash
pip install transformers==4.36.2
```

3. 安装vllm：
```bash
pip install vllm==0.2.5
```

4. 安装其他依赖：
```bash
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pandas==2.1.4
```

## 启动服务器

### 方法1: 使用启动脚本（推荐）
```bash
./start_vllm_server.sh
```

### 方法2: 直接启动
```bash
uvicorn vllm_server:app --reload --host 0.0.0.0 --port 8000
```

## 测试服务器

启动服务器后，可以运行测试脚本验证功能：
```bash
python test_vllm_server.py
```

## API接口

### 1. 批量推理接口
- **URL**: `POST /api/generate`
- **参数**:
  - `prompts`: 字符串列表
  - `max_new_tokens`: 最大生成长度（默认512）
  - `temperature`: 温度参数（默认0.95）
  - `top_p`: top_p参数（默认0.7）

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "prompts": ["你好，请介绍一下自己"],
       "max_new_tokens": 100,
       "temperature": 0.7,
       "top_p": 0.9
     }'
```

### 2. 文件上传推理接口
- **URL**: `POST /api/uploadfile/`
- **支持格式**: txt, csv
- **参数**:
  - `file`: 上传的文件
  - `max_new_tokens`: 最大生成长度（默认128）
  - `temperature`: 温度参数（默认0.95）
  - `top_p`: top_p参数（默认0.7）

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/uploadfile/" \
     -F "file=@test_prompts.txt" \
     -F "max_new_tokens=100" \
     -F "temperature=0.7" \
     -F "top_p=0.9"
```

### 3. API文档
访问 `http://localhost:8000/docs` 查看完整的API文档。

## 文件说明

- `vllm_server.py`: 主服务器文件
- `fix_vllm_deps.sh`: 依赖修复脚本（Bash版本）
- `fix_vllm_deps.py`: 依赖修复脚本（Python版本）
- `start_vllm_server.sh`: 服务器启动脚本
- `test_vllm_server.py`: 服务器测试脚本
- `requirements_vllm.txt`: 兼容的依赖版本列表

## 注意事项

1. 确保模型路径正确：`/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune_zero3/best/merged`

2. 服务器配置了2个GPU的tensor并行：`tensor_parallel_size=2`

3. 如果遇到CUDA内存不足，可以调整 `tensor_parallel_size` 或使用更小的模型

4. 首次启动可能需要较长时间来加载模型

5. 确保在 `dl_env` 环境中运行所有命令

## 故障排除

### 常见问题

1. **ImportError: cannot import name 'CLIPVisionModel'**
   - 解决方案：运行 `./fix_vllm_deps.sh`

2. **CUDA out of memory**
   - 解决方案：减少 `tensor_parallel_size` 或使用更小的模型

3. **模型路径不存在**
   - 解决方案：检查并更新 `vllm_server.py` 中的模型路径

4. **服务器启动失败**
   - 解决方案：检查端口是否被占用，尝试使用其他端口 