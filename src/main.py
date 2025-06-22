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