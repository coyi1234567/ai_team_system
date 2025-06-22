import typer
from .crew import AiTeamCrew

def run(
    project_name: str = typer.Option("智能待办事项管理系统", help="项目名称"),
    requirements: str = typer.Option("开发一个智能待办事项管理系统，支持任务分类、优先级管理、智能提醒、数据统计等功能。", help="项目需求")
):
    """运行AI团队多Agent协作项目"""
    inputs = {
        'project_name': project_name,
        'requirements': requirements
    }
    result = AiTeamCrew().kickoff(inputs=inputs)
    print("\n=== 项目执行结果 ===\n")
    print(result)

if __name__ == "__main__":
    typer.run(run) 