@echo off
chcp 65001 >nul
echo 🚀 AI团队系统本地部署脚本
echo ================================

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo ✅ 检测到Python环境

REM 检查是否已安装conda
conda --version >nul 2>&1
if not errorlevel 1 (
    echo ✅ 检测到conda环境
    
    REM 创建新的conda环境
    set env_name=ai_team_env
    echo 🔧 创建conda环境: %env_name%
    conda create -n %env_name% python=3.10 -y
    
    REM 激活环境
    echo 🔄 激活conda环境...
    call conda activate %env_name%
    
) else (
    echo ⚠️  未检测到conda，使用系统Python
)

REM 安装依赖
echo 📦 安装项目依赖...
pip install -r requirements.txt

REM 创建必要的目录
echo 📁 创建项目目录...
if not exist "projects" mkdir projects
if not exist "logs" mkdir logs

REM 检查配置文件
if not exist "config\team_config.yaml" (
    echo ❌ 配置文件不存在: config\team_config.yaml
    pause
    exit /b 1
)

if not exist "config\knowledge_base.yaml" (
    echo ❌ 知识库配置不存在: config\knowledge_base.yaml
    pause
    exit /b 1
)

REM 设置环境变量
echo 🔧 设置环境变量...
set PYTHONPATH=%PYTHONPATH%;%CD%

REM 检查OpenAI API配置
if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  未设置OPENAI_API_KEY环境变量
    echo 请设置您的OpenAI API密钥:
    echo set OPENAI_API_KEY=your-api-key-here
)

if "%OPENAI_API_BASE%"=="" (
    echo ⚠️  未设置OPENAI_API_BASE环境变量
    echo 使用默认代理地址: https://api.openai-proxy.org/v1
    set OPENAI_API_BASE=https://api.openai-proxy.org/v1
)

echo.
echo ✅ 部署完成！
echo.
echo 🎯 使用方法：
echo 1. 激活环境: conda activate ai_team_env
echo 2. 运行系统: python main.py
echo 3. 或者直接运行: python -m src.team_manager
echo.
echo 📁 项目文件将保存在 projects\ 目录下
echo 📝 日志文件将保存在 logs\ 目录下
echo.
echo 🔗 相关命令：
echo - 查看团队信息: python main.py --show-team
echo - 创建项目: python main.py --create-project
echo - 执行项目: python main.py --execute-project ^<project_id^>
echo - 列出项目: python main.py --list-projects
echo.
pause 