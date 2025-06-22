import typer
from .crew import AiTeamCrew
import traceback
import sys
import os
from dotenv import load_dotenv

# 自动加载.env环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

def run(
    project_name: str = typer.Option("智能待办事项管理系统", help="项目名称"),
    requirements: str = typer.Option("开发一个智能待办事项管理系统，支持任务分类、优先级管理、智能提醒、数据统计等功能。", help="项目需求")
):
    """运行AI团队多Agent协作项目"""
    inputs = {
        'project_name': project_name,
        'requirements': requirements
    }
    try:
        result = AiTeamCrew().kickoff(inputs=inputs)
        print("\n=== 项目执行结果 ===\n")
        print(result)

        # === 自动部署逻辑 ===
        print("\n[AI团队] 正在自动部署项目...\n")
        from mcp_server import MCPServer
        mcp = MCPServer(workspace_path="../projects")
        # 自动检测最新项目目录
        projects_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../projects'))
        # 以项目名为目录名
        project_dir = os.path.join(projects_root, project_name)
        if not os.path.exists(project_dir):
            # 兜底：取projects下最新目录
            all_dirs = [os.path.join(projects_root, d) for d in os.listdir(projects_root) if os.path.isdir(os.path.join(projects_root, d))]
            if all_dirs:
                project_dir = max(all_dirs, key=os.path.getmtime)
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
        log_path = os.path.join(os.path.dirname(__file__), '../logs/conversation.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(err_msg + '\n')
        sys.exit(1)

if __name__ == "__main__":
    typer.run(run) 