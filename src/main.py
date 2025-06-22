import typer
from .crew import AiTeamCrew
import traceback
import sys
import os
import shutil
import json
import time
from dotenv import load_dotenv

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

def run(
    project_name: str = typer.Option("智能待办事项管理系统", help="项目名称"),
    requirements: str = typer.Option("开发一个智能待办事项管理系统，支持任务分类、优先级管理、智能提醒、数据统计等功能。", help="项目需求")
):
    """运行AI团队多Agent协作项目"""
    project_id = get_project_id(project_name)
    # 1. 归档并清理历史环境
    archive_and_clean(project_id, project_name)
    # 2. 记录需求ID与内容
    update_project_index(project_id, project_name, requirements)
    # 3. 创建产出目录
    project_dir = os.path.join(PROJECTS_ROOT, project_id)
    os.makedirs(project_dir, exist_ok=True)
    inputs = {
        'project_name': project_name,
        'requirements': requirements
    }
    try:
        result = AiTeamCrew(project_id=project_id, project_dir=project_dir).kickoff(inputs=inputs)
        print("\n=== 项目执行结果 ===\n")
        print(result)

        # === 自动部署逻辑 ===
        print("\n[AI团队] 正在自动部署项目...\n")
        from mcp_server import MCPServer
        mcp = MCPServer(workspace_path=PROJECTS_ROOT)
        # 自动部署前校验产出目录和Dockerfile
        if not os.path.exists(project_dir):
            print(f"[FATAL] 产出目录不存在: {project_dir}")
            sys.exit(1)
        dockerfile_path = os.path.join(project_dir, 'Dockerfile')
        if not os.path.exists(dockerfile_path):
            print(f"[FATAL] Dockerfile不存在: {dockerfile_path}")
            sys.exit(1)
        deploy_result = mcp.deploy_project(project_dir, "python", 8000)
        print("\n=== 自动部署结果 ===\n")
        print(deploy_result.message)
        print(deploy_result.logs)
        print("\n[AI团队] 项目已自动部署完毕！\n")
    except Exception as e:
        err_msg = f"[FATAL] {str(e)}\n" + traceback.format_exc()
        print("\n=== 发生致命错误 ===\n")
        print(err_msg)
        # 追加写入日志
        log_file = os.path.join(LOGS_ROOT, f"{project_id}.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(err_msg + '\n')
        sys.exit(1)

if __name__ == "__main__":
    typer.run(run) 