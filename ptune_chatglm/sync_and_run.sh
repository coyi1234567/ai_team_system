#!/usr/bin/env bash

# 1. 同步本地代码到服务器
rsync -avz \
  --iconv=UTF-8-MAC,UTF-8 \
  --exclude='preprocess.py' \
  --exclude='data/' \
  --exclude='*.pkl' \
  /Users/coyi/Downloads/cursor/ptune_chatglm/ \
  ubuntu@my32gpu_2:/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/

# 2. 远程登录并激活环境、运行训练脚本
ssh ubuntu@my32gpu_2 << 'EOF'
source /home/ubuntu/miniconda/bin/activate dl_env
cd /home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm
accelerate launch train_zero3_deepseep_2.py 2>&1 | tee txt_log_$(date +%Y%m%d_%H%M%S)
EOF 