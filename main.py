#!/usr/bin/env python3
"""
AI团队系统 - 主程序
一个基于LLM的智能开发团队协作系统
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.team_manager import TeamManager
from src.models import ProjectReport

# 加载环境变量
load_dotenv()

app = typer.Typer(help="AI团队系统 - 智能开发团队协作")
console = Console()

@app.command()
def init():
    """初始化系统"""
    console.print(Panel.fit(
        "[bold blue]AI团队系统[/bold blue]\n"
        "一个基于LLM的智能开发团队协作系统\n"
        "支持从需求分析到部署运维的全流程自动化",
        title="欢迎使用"
    ))
    
    # 检查配置文件
    config_path = Path("config/team_config.yaml")
    if not config_path.exists():
        console.print("[red]配置文件不存在，请确保config/team_config.yaml文件存在[/red]")
        return
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[yellow]警告: 未设置OPENAI_API_KEY环境变量，将使用模拟模式[/yellow]")
    
    console.print("[green]✅ 系统初始化完成[/green]")

@app.command()
def team():
    """显示团队信息"""
    try:
        manager = TeamManager()
        manager.show_team_info()
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")

@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="项目名称"),
    description: str = typer.Option(..., "--description", "-d", help="项目描述"),
    requirements: str = typer.Option(..., "--requirements", "-r", help="项目需求"),
    client: str = typer.Option(None, "--client", "-c", help="客户名称"),
    budget: float = typer.Option(None, "--budget", "-b", help="项目预算")
):
    """创建新项目"""
    try:
        manager = TeamManager()
        project = manager.create_project(
            name=name,
            description=description,
            requirements=requirements,
            client=client,
            budget=budget
        )
        
        console.print(f"\n[bold green]项目创建成功！[/bold green]")
        console.print(f"项目ID: [cyan]{project.id}[/cyan]")
        console.print(f"项目名称: [green]{project.name}[/green]")
        console.print(f"项目描述: {project.description}")
        
    except Exception as e:
        console.print(f"[red]创建项目失败: {e}[/red]")

@app.command()
def execute(
    project_id: str = typer.Option(..., "--id", "-i", help="项目ID")
):
    """执行项目"""
    try:
        manager = TeamManager()
        
        # 检查项目是否存在
        if project_id not in manager.projects:
            console.print(f"[red]项目 {project_id} 不存在[/red]")
            return
        
        # 执行项目
        report = manager.execute_project(project_id)
        
        # 显示项目报告
        console.print("\n" + "="*60)
        console.print("[bold blue]📊 项目执行报告[/bold blue]")
        console.print("="*60)
        
        console.print(f"项目ID: {report.project_id}")
        console.print(f"当前阶段: {report.phase.value}")
        console.print(f"完成进度: {report.progress}%")
        console.print(f"完成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        console.print(f"\n[bold]已完成任务:[/bold]")
        for task in report.completed_tasks:
            console.print(f"  ✅ {task}")
        
        console.print(f"\n[bold]下一步计划:[/bold]")
        for step in report.next_steps:
            console.print(f"  📋 {step}")
        
    except Exception as e:
        console.print(f"[red]执行项目失败: {e}[/red]")

@app.command()
def list():
    """列出所有项目"""
    try:
        manager = TeamManager()
        manager.list_projects()
    except Exception as e:
        console.print(f"[red]获取项目列表失败: {e}[/red]")

@app.command()
def demo():
    """运行演示项目"""
    console.print("[bold blue]🎬 运行演示项目[/bold blue]")
    
    try:
        manager = TeamManager()
        
        # 创建演示项目
        demo_project = manager.create_project(
            name="在线图书管理系统",
            description="一个功能完整的图书管理平台",
            requirements="""
开发一个在线图书管理系统，功能包括：
1. 用户注册和登录
2. 图书信息管理（增删改查）
3. 图书借阅和归还
4. 用户借阅历史查询
5. 图书搜索和分类
6. 管理员后台管理

技术要求：
- 前端使用React + TypeScript
- 后端使用Python FastAPI
- 数据库使用PostgreSQL
- 部署使用Docker + Nginx
- 支持响应式设计
            """,
            client="演示客户",
            budget=50000.0
        )
        
        console.print(f"\n[green]演示项目创建成功，ID: {demo_project.id}[/green]")
        
        # 执行项目
        report = manager.execute_project(demo_project.id)
        
        console.print(f"\n[bold green]🎉 演示项目执行完成！[/bold green]")
        
    except Exception as e:
        console.print(f"[red]演示项目执行失败: {e}[/red]")

@app.command()
def help():
    """显示帮助信息"""
    help_text = """
# AI团队系统使用指南

## 基本命令

### 初始化系统
```bash
python main.py init
```

### 查看团队信息
```bash
python main.py team
```

### 创建项目
```bash
python main.py create --name "项目名称" --description "项目描述" --requirements "项目需求"
```

### 执行项目
```bash
python main.py execute --id "项目ID"
```

### 列出项目
```bash
python main.py list
```

### 运行演示
```bash
python main.py demo
```

## 环境配置

1. 创建 `.env` 文件
2. 设置 `OPENAI_API_KEY=your-api-key`
3. 确保 `config/team_config.yaml` 配置文件存在

## 项目流程

1. **需求分析** - 产品经理分析客户需求
2. **技术设计** - 技术负责人设计架构
3. **开发实现** - 开发团队编写代码
4. **测试验证** - 测试团队验证质量
5. **部署运维** - 运维团队部署系统
6. **项目验收** - 项目总监最终验收

## 团队成员

- **张总** - 项目总监
- **李产品** - 产品经理
- **王架构** - 技术负责人
- **陈前端** - 前端开发
- **刘后端** - 后端开发
- **赵测试** - 测试工程师
- **孙运维** - DevOps工程师
    """
    
    console.print(Markdown(help_text))

if __name__ == "__main__":
    app() 