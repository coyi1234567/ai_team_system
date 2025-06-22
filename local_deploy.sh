#!/bin/bash

echo "🚀 AI团队系统本地部署脚本"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "📋 检测到Python版本: $python_version"

# 检查是否已安装conda
if command -v conda &> /dev/null; then
    echo "✅ 检测到conda环境"
    
    # 创建新的conda环境
    env_name="ai_team_env"
    echo "🔧 创建conda环境: $env_name"
    conda create -n $env_name python=3.10 -y
    
    # 激活环境
    echo "🔄 激活conda环境..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $env_name
    
else
    echo "⚠️  未检测到conda，使用系统Python"
fi

# 安装依赖
echo "📦 安装项目依赖..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p projects
mkdir -p logs

# 检查配置文件
if [ ! -f "config/team_config.yaml" ]; then
    echo "❌ 配置文件不存在: config/team_config.yaml"
    exit 1
fi

if [ ! -f "config/knowledge_base.yaml" ]; then
    echo "❌ 知识库配置不存在: config/knowledge_base.yaml"
    exit 1
fi

# 设置环境变量
echo "🔧 设置环境变量..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 检查OpenAI API配置
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  未设置OPENAI_API_KEY环境变量"
    echo "请设置您的OpenAI API密钥:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
fi

if [ -z "$OPENAI_API_BASE" ]; then
    echo "⚠️  未设置OPENAI_API_BASE环境变量"
    echo "使用默认代理地址: https://api.openai-proxy.org/v1"
    export OPENAI_API_BASE="https://api.openai-proxy.org/v1"
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "🎯 使用方法："
echo "1. 激活环境: conda activate ai_team_env"
echo "2. 运行系统: python main.py"
echo "3. 或者直接运行: python -m src.team_manager"
echo ""
echo "📁 项目文件将保存在 projects/ 目录下"
echo "📝 日志文件将保存在 logs/ 目录下"
echo ""
echo "🔗 相关命令："
echo "- 查看团队信息: python main.py --show-team"
echo "- 创建项目: python main.py --create-project"
echo "- 执行项目: python main.py --execute-project <project_id>"
echo "- 列出项目: python main.py --list-projects" 