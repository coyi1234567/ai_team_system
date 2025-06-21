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

from src.team_manager import TeamManager, create_demo_team
from src.models import ProjectReport
from src.knowledge_manager import KnowledgeManager, search_knowledge_base, get_learning_path

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

def main():
    """主程序入口"""
    print("🤖 AI团队系统")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请设置环境变量或使用 .env 文件")
        print("示例: export OPENAI_API_KEY='your-api-key'")
        print()
    
    # 创建团队管理器
    manager = TeamManager()
    
    while True:
        print("\n📋 功能菜单:")
        print("1. 查看团队信息")
        print("2. 搜索知识库")
        print("3. 获取学习路径")
        print("4. 团队成本估算")
        print("5. 运行项目演示")
        print("6. 查看可用角色")
        print("7. 知识库分类浏览")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-7): ").strip()
        
        if choice == '0':
            print("👋 再见！")
            break
            
        elif choice == '1':
            show_team_info(manager)
            
        elif choice == '2':
            search_knowledge(manager)
            
        elif choice == '3':
            show_learning_path(manager)
            
        elif choice == '4':
            estimate_team_cost(manager)
            
        elif choice == '5':
            run_project_demo(manager)
            
        elif choice == '6':
            show_available_roles(manager)
            
        elif choice == '7':
            browse_knowledge_categories(manager)
            
        else:
            print("❌ 无效选择，请重试")


def show_team_info(manager: TeamManager):
    """显示团队信息"""
    print("\n👥 团队信息")
    print("-" * 30)
    manager.display_team_info()


def search_knowledge(manager: TeamManager):
    """搜索知识库"""
    print("\n🔍 知识库搜索")
    print("-" * 30)
    
    query = input("请输入搜索关键词: ").strip()
    if not query:
        print("❌ 搜索关键词不能为空")
        return
    
    print(f"\n搜索 '{query}' 的结果:")
    print("=" * 50)
    
    results = manager.search_knowledge(query)
    print(results)


def show_learning_path(manager: TeamManager):
    """显示学习路径"""
    print("\n📚 学习路径")
    print("-" * 30)
    
    print("可用角色:")
    roles = manager.list_available_roles()
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role}")
    
    try:
        choice = int(input("\n请选择角色 (输入数字): ")) - 1
        if 0 <= choice < len(roles):
            role = roles[choice]
            print(f"\n📖 {role} 学习路径:")
            print("=" * 50)
            path = manager.get_learning_path_for_role(role)
            print(path)
        else:
            print("❌ 无效选择")
    except ValueError:
        print("❌ 请输入有效数字")


def estimate_team_cost(manager: TeamManager):
    """估算团队成本"""
    print("\n💰 团队成本估算")
    print("-" * 30)
    
    print("可用角色:")
    roles = manager.list_available_roles()
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role}")
    
    print("\n请选择角色 (输入数字，用逗号分隔，如: 1,3,5):")
    try:
        choices = input("选择: ").strip().split(',')
        selected_roles = []
        for choice in choices:
            idx = int(choice.strip()) - 1
            if 0 <= idx < len(roles):
                selected_roles.append(roles[idx])
        
        if not selected_roles:
            print("❌ 未选择任何角色")
            return
        
        duration = int(input("项目周期 (月): ") or "3")
        
        print(f"\n📊 成本估算结果:")
        print("=" * 50)
        cost_estimate = manager.get_team_cost_estimate(selected_roles, duration)
        
        print(f"项目周期: {duration} 个月")
        print(f"团队成员: {', '.join(selected_roles)}")
        print(f"月薪范围: ¥{cost_estimate['total_monthly']['min']:,} - ¥{cost_estimate['total_monthly']['max']:,}")
        print(f"项目总成本: ¥{cost_estimate['total_project']['min']:,} - ¥{cost_estimate['total_project']['max']:,}")
        
        print("\n详细成本:")
        for role, costs in cost_estimate['roles'].items():
            print(f"  {role}: ¥{costs['min_monthly']:,} - ¥{costs['max_monthly']:,}/月")
            
    except ValueError:
        print("❌ 输入格式错误")


def run_project_demo(manager: TeamManager):
    """运行项目演示"""
    print("\n🚀 项目演示")
    print("-" * 30)
    
    # 检查是否安装了CrewAI
    try:
        import crewai
        print("✅ CrewAI 已安装")
    except ImportError:
        print("❌ CrewAI 未安装，无法运行项目演示")
        print("请安装: pip install crewai")
        return
    
    # 检查API密钥
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 未设置 OPENAI_API_KEY，无法运行演示")
        return
    
    print("开始运行智能客服系统项目演示...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        project_name = "智能客服系统"
        roles = ['project_manager', 'product_manager', 'tech_lead', 'backend_developer', 'ai_engineer']
        
        project_description = """
        开发一个基于大语言模型的智能客服系统，具备以下功能：
        1. 多轮对话能力
        2. 知识库检索
        3. 情感分析
        4. 多语言支持
        5. 人工客服转接
        6. 对话记录管理
        
        技术栈：Python + FastAPI + PostgreSQL + Redis + OpenAI API
        开发周期：3个月
        """
        
        print(f"\n项目: {project_name}")
        print(f"团队: {', '.join([manager.config['agents'][role]['name'] for role in roles])}")
        print(f"描述: {project_description.strip()}")
        
        result = manager.run_project(project_name, roles, project_description)
        
        print("\n📋 项目执行结果:")
        print("=" * 50)
        print(result)
        
    except Exception as e:
        print(f"❌ 项目执行失败: {e}")


def show_available_roles(manager: TeamManager):
    """显示可用角色"""
    print("\n👤 可用角色")
    print("-" * 30)
    
    roles = manager.list_available_roles()
    for i, role in enumerate(roles, 1):
        info = manager.get_agent_info(role)
        print(f"{i}. {info['name']} ({role})")
        print(f"   目标: {info['goal']}")
        print(f"   工具: {', '.join(info['tools'])}")
        print()


def browse_knowledge_categories(manager: TeamManager):
    """浏览知识库分类"""
    print("\n📚 知识库分类浏览")
    print("-" * 30)
    
    km = KnowledgeManager()
    categories = km.get_all_categories()
    
    print("可用分类:")
    for i, category in enumerate(categories, 1):
        resources = km.get_resources_by_category(category)
        print(f"{i}. {category} ({len(resources)} 个资源)")
    
    try:
        choice = int(input("\n请选择分类 (输入数字): ")) - 1
        if 0 <= choice < len(categories):
            category = categories[choice]
            resources = km.get_resources_by_category(category)
            
            print(f"\n📖 {category} 分类资源:")
            print("=" * 50)
            formatted = km.format_resources_for_agent(resources)
            print(formatted)
        else:
            print("❌ 无效选择")
    except ValueError:
        print("❌ 请输入有效数字")


def demo_knowledge_base():
    """知识库功能演示"""
    print("🧠 知识库功能演示")
    print("=" * 50)
    
    km = KnowledgeManager()
    
    # 1. 搜索Python相关资源
    print("\n1. 搜索Python相关资源:")
    python_resources = search_knowledge_base("Python")
    print(python_resources[:500] + "..." if len(python_resources) > 500 else python_resources)
    
    # 2. 获取开发工程师学习路径
    print("\n2. 开发工程师学习路径:")
    dev_path = get_learning_path("developer")
    print(dev_path)
    
    # 3. 获取AI工程师资源
    print("\n3. AI工程师学习资源:")
    ai_resources = km.get_ai_ml_resources()
    formatted = km.format_resources_for_agent(ai_resources[:3])  # 只显示前3个
    print(formatted)
    
    # 4. 团队成本估算
    print("\n4. 团队成本估算:")
    manager = TeamManager()
    roles = ['project_manager', 'tech_lead', 'backend_developer', 'ai_engineer']
    cost_estimate = manager.get_team_cost_estimate(roles, 3)
    print(f"3个月项目总成本: ¥{cost_estimate['total_project']['min']:,} - ¥{cost_estimate['total_project']['max']:,}")


if __name__ == "__main__":
    # 如果直接运行，显示知识库演示
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_knowledge_base()
    else:
        main() 