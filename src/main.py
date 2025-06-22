import os
import sys
import time
import json
import traceback
import typer
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crew import AiTeamCrew, ProgressManager

# 自动加载.env环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

# 检查OPENAI_API_KEY是否加载成功
if not os.getenv('OPENAI_API_KEY'):
    print("[FATAL] 未检测到OPENAI_API_KEY环境变量，请检查.ai_team_system/.env文件并确保主程序有权限读取！")
    sys.exit(1)

PROJECTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../projects'))
LOGS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs'))
ARCHIVE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../archive'))
INDEX_FILE = os.path.join(PROJECTS_ROOT, 'project_index.json')

# 生成需求ID（默认用项目名，可自定义）
def get_project_id(project_name):
    return project_name.strip().replace(' ', '_')

def archive_and_clean(project_id, project_name):
    # 暂时禁用归档功能
    print(f"[AI团队] 跳过归档，直接使用现有目录")
    # 清理日志
    log_file = os.path.join(LOGS_ROOT, f"{project_id}.log")
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"[AI团队] 已清理旧日志: {log_file}")
    # 清理同名Docker容器
    try:
        from mcp_server import MCPServer
        mcp = MCPServer(workspace_path=PROJECTS_ROOT)
        container_name = f"{project_id}-container"
        stop_result = mcp.stop_container(container_name)
        print(f"[AI团队] Docker容器清理: {stop_result.message}")
    except Exception as e:
        print(f"[AI团队] Docker容器清理异常: {e}")

def update_project_index(project_id, project_name, requirements):
    index = {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            try:
                index = json.load(f)
            except Exception:
                index = {}
    index[project_id] = {
        "project_name": project_name,
        "requirements": requirements,
        "last_run": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"[AI团队] 已记录需求ID与内容到: {INDEX_FILE}")

app = typer.Typer()

@app.command()
def main(
    project_name: str = typer.Option(..., "--project-name", "-p", help="项目名称"),
    requirements: str = typer.Option(..., "--requirements", "-r", help="项目需求描述"),
    resume_from: Optional[str] = typer.Option(None, "--resume-from", help="从指定阶段继续执行"),
    show_progress: bool = typer.Option(False, "--show-progress", help="显示项目进度"),
    reset_progress: bool = typer.Option(False, "--reset-progress", help="重置项目进度")
):
    """
    AI团队系统 - 多Agent协作开发平台
    
    支持断点续传功能：
    - 使用 --resume-from <阶段名> 从指定阶段继续
    - 使用 --show-progress 查看当前进度
    - 使用 --reset-progress 重置进度重新开始
    
    可用阶段：requirement_analysis, technical_design, ui_design, 
    frontend_development, frontend_code, backend_development, backend_code,
    data_analysis, testing, deployment, documentation, acceptance, auto_execution
    """
    
    # 设置项目目录
    project_dir = os.path.join("projects", project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    # 初始化进度管理器
    progress_manager = ProgressManager(project_dir)
    
    # 显示进度
    if show_progress:
        summary = progress_manager.get_progress_summary()
        print(f"\n=== 项目进度摘要 ===")
        print(f"项目名称: {project_name}")
        print(f"完成进度: {summary['completed']}/{summary['total']} ({summary['percentage']}%)")
        print(f"已完成阶段: {', '.join(summary['completed_stages'])}")
        print(f"下一阶段: {summary['next_stage']}")
        
        if summary['completed'] > 0:
            print(f"\n=== 阶段详情 ===")
            progress = progress_manager.load_progress()
            for stage, data in progress.items():
                if data.get("status") == "completed":
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.get("timestamp", 0)))
                    print(f"✓ {stage}: {timestamp}")
        return
    
    # 重置进度
    if reset_progress:
        progress_manager.reset_progress()
        print(f"[AI团队] 已重置项目 '{project_name}' 的进度")
        return
    
    # 检查是否从指定阶段继续
    if resume_from:
        if resume_from not in progress_manager.stages:
            print(f"错误：无效的阶段名 '{resume_from}'")
            print(f"可用阶段：{', '.join(progress_manager.stages)}")
            return
        
        if not progress_manager.is_stage_completed(resume_from):
            print(f"错误：阶段 '{resume_from}' 尚未完成，无法从此处继续")
            return
    
    try:
        # 初始化AI团队
        crew = AiTeamCrew(project_dir=project_dir)
        
        # 设置项目目录到所有Agent
        for agent in crew.crew.agents:
            agent._project_dir = project_dir
        
        # 启动项目
        inputs = {
            "project_name": project_name,
            "requirements": requirements
        }
        
        print(f"[AI团队] 开始执行项目：{project_name}")
        if resume_from:
            print(f"[AI团队] 从阶段 '{resume_from}' 继续执行...")
        
        results = crew.kickoff(inputs, resume_from=resume_from)
        
        print(f"\n=== 项目执行结果 ===")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"[错误] 项目执行失败：{str(e)}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    app() 