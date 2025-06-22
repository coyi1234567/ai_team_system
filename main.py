#!/usr/bin/env python3
"""
AI团队系统 - 基于CrewAI的多Agent协作系统
支持11个专业角色的智能团队协作
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.crew import AiTeamCrew

# 加载环境变量
load_dotenv()

app = typer.Typer(help="AI团队系统 - 基于CrewAI的多Agent协作系统")
console = Console()

@app.command()
def init():
    """初始化系统"""
    console.print(Panel.fit(
        "[bold blue]AI团队系统 - CrewAI版本[/bold blue]\n"
        "基于CrewAI框架的多Agent协作系统\n"
        "支持11个专业角色的智能团队协作\n"
        "集成MCP工具，实现标准化Agent协作",
        title="欢迎使用"
    ))
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[yellow]警告: 未设置OPENAI_API_KEY环境变量[/yellow]")
        console.print("请设置环境变量: export OPENAI_API_KEY='your-api-key'")
        return
    
    console.print("[green]✅ 系统初始化完成[/green]")
    console.print(f"API密钥状态: {'✅ 已设置' if api_key else '❌ 未设置'}")

@app.command()
def team():
    """显示团队成员信息"""
    console.print(Panel.fit(
        """[bold]团队成员 (11人):[/bold]

👔 [cyan]张总[/cyan] - 项目总监 (15年经验)
📋 [cyan]李产品[/cyan] - 产品经理 (8年经验)  
🏗️ [cyan]王技术[/cyan] - 技术总监 (12年经验)
🧠 [cyan]陈算法[/cyan] - 算法工程师 (10年经验)
🎨 [cyan]林设计[/cyan] - UI设计师 (7年经验)
💻 [cyan]陈前端[/cyan] - 前端开发 (6年经验)
⚙️ [cyan]刘后端[/cyan] - 后端开发 (8年经验)
📊 [cyan]赵数据[/cyan] - 数据分析师 (5年经验)
🔍 [cyan]赵测试[/cyan] - 测试工程师 (7年经验)
🚀 [cyan]孙运维[/cyan] - DevOps工程师 (6年经验)
📝 [cyan]王文员[/cyan] - 项目文员 (4年经验)""",
        title="团队信息"
    ))

@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="项目名称"),
    description: str = typer.Option(..., "--description", "-d", help="项目描述"),
    requirements: str = typer.Option(..., "--requirements", "-r", help="项目需求")
):
    """创建并执行新项目"""
    try:
        console.print(f"[bold blue]🚀 开始执行项目: {name}[/bold blue]")
        console.print(f"项目描述: {description}")
        console.print(f"项目需求: {requirements}")
        console.print()
        
        inputs = {
            'project_name': name,
            'project_description': description,
            'requirements': requirements
        }
        
        result = AiTeamCrew().kickoff(inputs=inputs)
        
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 项目执行完成！[/bold green]")
        console.print("="*60)
        console.print(result)
        
    except Exception as e:
        console.print(f"[red]项目执行失败: {e}[/red]")

@app.command()
def demo():
    """运行演示项目"""
    console.print("[bold blue]🎬 运行演示项目[/bold blue]")
    
    demo_inputs = {
        'project_name': '智能待办事项管理系统',
        'project_description': '一个功能完整的智能待办事项管理平台',
        'requirements': """开发一个智能待办事项管理系统，具体需求如下：

1. 用户功能：
   - 用户注册、登录、个人信息管理
   - 任务创建、编辑、删除、完成状态切换
   - 任务分类管理（工作、生活、学习、健康等）
   - 任务优先级设置（高、中、低）
   - 任务标签系统
   - 任务搜索和筛选

2. 智能功能：
   - 智能任务提醒（基于截止时间和优先级）
   - 任务完成时间预测
   - 个人效率统计分析
   - 智能任务建议
   - 习惯养成追踪

3. 协作功能：
   - 任务分享和协作
   - 团队任务管理
   - 任务评论和讨论

4. 技术需求：
   - 前端：React + TypeScript + Ant Design
   - 后端：Python FastAPI + SQLAlchemy
   - 数据库：PostgreSQL
   - 缓存：Redis
   - 消息队列：Celery + Redis
   - 部署：Docker + Nginx
   - 监控：Prometheus + Grafana

5. 性能要求：
   - 支持1000+并发用户
   - 响应时间 < 200ms
   - 99.9%可用性
   - 数据备份和恢复机制

6. 安全要求：
   - JWT身份认证
   - 数据加密存储
   - API访问限制
   - 日志审计"""
    }
    
    try:
        result = AiTeamCrew().kickoff(inputs=demo_inputs)
        console.print(f"\n[bold green]🎉 演示项目执行完成！[/bold green]")
        console.print(result)
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

### 运行演示
```bash
python main.py demo
```

## 环境配置

1. 创建 `.env` 文件
2. 设置 `OPENAI_API_KEY=your-api-key`
3. 可选：设置 `OPENAI_API_BASE=https://api.openai-proxy.org/v1`

## 项目流程

1. **需求分析** - 产品经理分析用户需求
2. **技术设计** - 技术总监设计系统架构
3. **UI设计** - UI设计师设计用户界面
4. **算法设计** - 算法工程师设计智能算法
5. **前端开发** - 前端工程师实现界面
6. **后端开发** - 后端工程师实现服务
7. **数据分析** - 数据分析师提供数据洞察
8. **测试验证** - 测试工程师验证质量
9. **部署运维** - DevOps工程师部署系统
10. **文档整理** - 项目文员整理文档
11. **项目验收** - 项目总监最终验收

## 特色功能

- 🤖 **11个专业角色**: 覆盖产品、技术、设计、开发、测试、运维等全流程
- 🧠 **智能算法**: 集成机器学习算法，提供智能解决方案
- 🎨 **专业设计**: UI设计师确保产品美观易用
- 📊 **数据分析**: 数据分析师提供数据洞察
- 📝 **文档管理**: 项目文员确保信息有序管理
- 🔧 **MCP工具**: 集成MCP协议，支持标准化工具调用
    """
    
    console.print(help_text)

if __name__ == "__main__":
    app() 