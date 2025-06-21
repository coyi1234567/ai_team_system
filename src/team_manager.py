import yaml
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import TeamMember, Project, ProjectTask, ProjectPhase, TaskStatus, ProjectReport
from .llm_client import LLMClient

console = Console()

class TeamManager:
    """团队管理器"""
    
    def __init__(self, config_path: str = "config/team_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.team_members = self._create_team_members()
        self.llm_client = LLMClient()
        self.projects: Dict[str, Project] = {}
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]配置文件 {self.config_path} 不存在[/red]")
            return {}
    
    def _create_team_members(self) -> Dict[str, TeamMember]:
        """创建团队成员"""
        members = {}
        config_members = self.config.get('members', {})
        
        for member_id, member_config in config_members.items():
            members[member_id] = TeamMember(
                id=member_id,
                name=member_config['name'],
                role=member_config['role'],
                skills=member_config['skills'],
                responsibilities=member_config['responsibilities'],
                personality=member_config['personality']
            )
        
        return members
    
    def create_project(self, name: str, description: str, requirements: str, 
                      client: str = None, budget: float = None) -> Project:
        """创建新项目"""
        project_id = str(uuid.uuid4())[:8]
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            requirements=requirements,
            client=client,
            budget=budget,
            start_date=datetime.now(),
            team_members=list(self.team_members.keys())
        )
        
        self.projects[project_id] = project
        console.print(f"[green]项目 '{name}' 创建成功，ID: {project_id}[/green]")
        
        return project
    
    def execute_project(self, project_id: str) -> ProjectReport:
        """执行项目"""
        if project_id not in self.projects:
            raise ValueError(f"项目 {project_id} 不存在")
        
        project = self.projects[project_id]
        console.print(f"\n[bold blue]🚀 开始执行项目: {project.name}[/bold blue]")
        
        # 获取项目流程
        workflow_phases = self.config.get('workflow', {}).get('phases', [])
        
        project_context = f"""
项目名称: {project.name}
项目描述: {project.description}
项目需求: {project.requirements}
        """
        
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for i, phase in enumerate(workflow_phases):
                phase_name = phase['name']
                participants = phase['participants']
                deliverables = phase['deliverables']
                
                task = progress.add_task(f"执行阶段: {phase_name}", total=len(participants))
                
                console.print(f"\n[bold yellow]📋 阶段 {i+1}: {phase_name}[/bold yellow]")
                console.print(f"⏱️  预计时长: {phase.get('duration', '1天')}")
                console.print(f"👥 参与人员: {', '.join(participants)}")
                
                phase_results = []
                
                for participant in participants:
                    if participant in self.team_members:
                        member = self.team_members[participant]
                        
                        # 生成任务提示
                        prompt = self._generate_phase_prompt(phase_name, project.requirements, deliverables)
                        
                        # 获取LLM响应
                        response = self.llm_client.generate_response(
                            role=participant,
                            prompt=prompt,
                            context=project_context
                        )
                        
                        console.print(f"\n[bold]{member.name} ({member.role}):[/bold]")
                        console.print(f"  {response.content}")
                        
                        phase_results.append({
                            'member': member.name,
                            'role': participant,
                            'response': response.content,
                            'deliverables': deliverables
                        })
                        
                        progress.update(task, advance=1)
                        time.sleep(1)  # 模拟处理时间
                
                # 更新项目状态
                project.current_phase = ProjectPhase(phase_name.lower().replace(' ', '_'))
                project.deliverables.update({phase_name: str(phase_results)})
                
                all_results.extend(phase_results)
                
                console.print(f"\n[green]✅ 阶段 '{phase_name}' 完成[/green]")
        
        # 生成项目报告
        report = self._generate_project_report(project, all_results)
        
        console.print(f"\n[bold green]🎉 项目 '{project.name}' 执行完成！[/bold green]")
        
        return report
    
    def _generate_phase_prompt(self, phase_name: str, requirements: str, deliverables: List[str]) -> str:
        """生成阶段提示"""
        prompts = {
            "需求分析": f"""
基于以下项目需求进行详细的需求分析：
{requirements}

请提供：
1. 功能需求列表
2. 非功能需求分析
3. 用户故事设计
4. 业务流程图
5. 项目风险评估

交付物：{', '.join(deliverables)}
            """,
            
            "技术设计": f"""
基于需求分析结果，设计技术方案：
{requirements}

请提供：
1. 系统架构设计
2. 技术栈选型
3. 数据库设计
4. API接口设计
5. 部署方案

交付物：{', '.join(deliverables)}
            """,
            
            "开发实现": f"""
基于技术设计方案进行开发实现：
{requirements}

请提供：
1. 代码实现方案
2. 核心功能代码
3. 数据库脚本
4. 配置文件
5. 开发文档

交付物：{', '.join(deliverables)}
            """,
            
            "测试验证": f"""
对开发完成的系统进行测试验证：
{requirements}

请提供：
1. 测试计划
2. 测试用例
3. 测试执行结果
4. 缺陷报告
5. 质量评估

交付物：{', '.join(deliverables)}
            """,
            
            "部署运维": f"""
对系统进行部署和运维配置：
{requirements}

请提供：
1. 部署方案
2. 环境配置
3. 监控配置
4. 运维文档
5. 应急预案

交付物：{', '.join(deliverables)}
            """,
            
            "项目验收": f"""
对项目进行最终验收：
{requirements}

请提供：
1. 验收标准
2. 验收结果
3. 交付清单
4. 项目总结
5. 后续建议

交付物：{', '.join(deliverables)}
            """
        }
        
        return prompts.get(phase_name, f"请完成{phase_name}阶段的任务。")
    
    def _generate_project_report(self, project: Project, results: List[Dict]) -> ProjectReport:
        """生成项目报告"""
        completed_tasks = [result['member'] for result in results]
        pending_tasks = []
        
        # 分析结果，提取关键信息
        summary_parts = []
        for result in results:
            summary_parts.append(f"{result['member']}({result['role']}): {result['response'][:100]}...")
        
        summary = "\n".join(summary_parts)
        
        return ProjectReport(
            project_id=project.id,
            phase=project.current_phase,
            summary=summary,
            progress=100.0,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            issues=[],
            next_steps=["项目交付", "客户培训", "运维支持"]
        )
    
    def list_projects(self):
        """列出所有项目"""
        if not self.projects:
            console.print("[yellow]暂无项目[/yellow]")
            return
        
        table = Table(title="项目列表")
        table.add_column("项目ID", style="cyan")
        table.add_column("项目名称", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("当前阶段", style="blue")
        table.add_column("创建时间", style="magenta")
        
        for project in self.projects.values():
            table.add_row(
                project.id,
                project.name,
                project.status.value,
                project.current_phase.value,
                project.start_date.strftime("%Y-%m-%d %H:%M") if project.start_date else "N/A"
            )
        
        console.print(table)
    
    def show_team_info(self):
        """显示团队信息"""
        table = Table(title="团队成员信息")
        table.add_column("姓名", style="cyan")
        table.add_column("角色", style="green")
        table.add_column("技能", style="yellow")
        table.add_column("性格", style="blue")
        
        for member in self.team_members.values():
            skills_str = ", ".join(member.skills[:3]) + ("..." if len(member.skills) > 3 else "")
            table.add_row(
                member.name,
                member.role,
                skills_str,
                member.personality
            )
        
        console.print(table)
    
    def show_knowledge_base(self):
        with open("config/knowledge_base.yaml", "r", encoding="utf-8") as f:
            kb = yaml.safe_load(f)
        for role, docs in kb.items():
            print(f"【{role}】")
            for doc in docs:
                print(f"- {doc['title']}: {doc['url']}") 