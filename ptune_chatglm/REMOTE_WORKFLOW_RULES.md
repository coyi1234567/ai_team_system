# 远程服务器工作流程规则

## 🚨 重要规则

### 远程服务器操作必须遵循以下规则之一：

#### 规则1: 先同步脚本到服务器，再执行
```bash
# 1. 同步脚本到服务器
rsync -avz --progress *.sh *.py *.txt *.md my32gpu_2:/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/

# 2. 在服务器上执行脚本
ssh my32gpu_2 "cd /home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm && ./script_name.sh"
```

#### 规则2: 在命令前面加上SSH连接命令
```bash
# 直接在SSH命令中执行
ssh my32gpu_2 "source /home/ubuntu/miniconda/bin/activate dl_env && python script.py"
```

## 📋 服务器信息

- **SSH配置**: `ssh my32gpu_2`
- **远程路径**: `/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm`
- **Conda环境**: `dl_env` (路径: `/home/ubuntu/miniconda/bin/activate dl_env`)

## 🔧 常用命令模板

### 同步文件
```bash
rsync -avz --progress 文件名 my32gpu_2:/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/
```

### 远程执行Python脚本
```bash
ssh my32gpu_2 "source /home/ubuntu/miniconda/bin/activate dl_env && cd /home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm && python script.py"
```

### 远程执行Shell脚本
```bash
ssh my32gpu_2 "cd /home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm && chmod +x script.sh && ./script.sh"
```

### 检查服务器状态
```bash
ssh my32gpu_2 "source /home/ubuntu/miniconda/bin/activate dl_env && nvidia-smi"
```

## 📝 注意事项

1. **始终使用正确的conda激活路径**: `/home/ubuntu/miniconda/bin/activate dl_env`
2. **确保脚本有执行权限**: `chmod +x script.sh`
3. **检查文件是否同步成功**: 使用 `rsync` 的 `--progress` 参数
4. **使用绝对路径**: 避免路径问题
5. **测试连接**: 先测试SSH连接是否正常

## 🎯 最佳实践

1. **开发阶段**: 在本地修改脚本，然后同步到服务器测试
2. **生产环境**: 直接在服务器上执行，或使用远程脚本
3. **调试**: 使用SSH直接连接服务器进行调试
4. **日志**: 重定向输出到文件便于查看

## 📚 相关脚本

- `sync_and_run.sh` - 同步并执行脚本
- `remote_fix.sh` - 远程修复依赖
- `remote_start.sh` - 远程启动服务器
- `remote_test.sh` - 远程测试服务器
- `check_config.sh` - 检查服务器配置 