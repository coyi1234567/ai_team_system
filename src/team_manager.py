"""
AI团队管理器
基于AutoGen和CrewAI的多Agent协作系统
"""

import os
import yaml
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Table = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None

try:
    import autogen
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None
    Process = None

from .models import TeamMember, Project, ProjectTask, ProjectPhase, TaskStatus, ProjectReport
from .llm_client import LLMClient
from .knowledge_manager import KnowledgeManager, get_role_specific_resources, search_knowledge_base, get_learning_path

if RICH_AVAILABLE:
    console = Console()
else:
    console = None


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    role: str
    goal: str
    backstory: str
    tools: Optional[List[str]] = None
    verbose: bool = True
    allow_delegation: bool = True


class TeamManager:
    """AI团队管理器"""
    
    def __init__(self, config_path: str = "config/team_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.llm_client = LLMClient()
        self.knowledge_manager = KnowledgeManager()
        self.agents = {}
        self.crews = {}
        
        # 初始化原有功能
        self.team_members = self._create_team_members()
        self.projects: Dict[str, Project] = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'openai_base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'model': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 4000,
            'agents': {
                'project_manager': {
                    'name': '项目经理',
                    'role': 'project_manager',
                    'goal': '确保项目按时交付，管理团队协作，控制项目风险',
                    'backstory': '经验丰富的项目经理，擅长敏捷开发和团队管理',
                    'tools': ['project_management', 'communication', 'risk_management']
                },
                'product_manager': {
                    'name': '产品经理',
                    'role': 'product_manager', 
                    'goal': '定义产品需求，优化用户体验，确保产品价值',
                    'backstory': '资深产品经理，精通用户研究和产品设计',
                    'tools': ['user_research', 'product_design', 'market_analysis']
                },
                'tech_lead': {
                    'name': '技术负责人',
                    'role': 'tech_lead',
                    'goal': '制定技术方案，确保代码质量，指导技术团队',
                    'backstory': '全栈技术专家，擅长系统架构和技术选型',
                    'tools': ['system_design', 'code_review', 'architecture']
                },
                'frontend_developer': {
                    'name': '前端开发',
                    'role': 'frontend_developer',
                    'goal': '开发用户界面，优化前端性能，提升用户体验',
                    'backstory': '前端技术专家，精通React、Vue等现代框架',
                    'tools': ['frontend_development', 'ui_optimization', 'performance']
                },
                'backend_developer': {
                    'name': '后端开发',
                    'role': 'backend_developer',
                    'goal': '开发后端服务，设计数据库，确保系统稳定性',
                    'backstory': '后端架构师，擅长高并发和分布式系统',
                    'tools': ['backend_development', 'database_design', 'api_design']
                },
                'ai_engineer': {
                    'name': 'AI工程师',
                    'role': 'ai_engineer',
                    'goal': '开发AI功能，优化模型性能，集成机器学习服务',
                    'backstory': '机器学习专家，精通深度学习和大模型应用',
                    'tools': ['ml_development', 'model_optimization', 'ai_integration']
                },
                'qa_engineer': {
                    'name': '测试工程师',
                    'role': 'qa_engineer',
                    'goal': '制定测试策略，执行质量保证，确保产品稳定性',
                    'backstory': '资深测试专家，精通自动化测试和性能测试',
                    'tools': ['test_planning', 'automation_testing', 'performance_testing']
                },
                'devops_engineer': {
                    'name': 'DevOps工程师',
                    'role': 'devops_engineer',
                    'goal': '构建CI/CD流程，管理基础设施，确保系统可用性',
                    'backstory': 'DevOps专家，擅长容器化和云原生技术',
                    'tools': ['ci_cd', 'infrastructure', 'monitoring']
                },
                'ui_designer': {
                    'name': 'UI设计师',
                    'role': 'ui_designer',
                    'goal': '设计用户界面，创建视觉规范，提升产品美观度',
                    'backstory': '资深UI设计师，精通设计系统和用户体验',
                    'tools': ['ui_design', 'design_system', 'user_experience']
                },
                'business_analyst': {
                    'name': '业务分析师',
                    'role': 'business_analyst',
                    'goal': '分析业务需求，制定解决方案，支持决策制定',
                    'backstory': '业务分析专家，擅长数据分析和流程优化',
                    'tools': ['business_analysis', 'data_analysis', 'process_optimization']
                },
                'security_engineer': {
                    'name': '安全工程师',
                    'role': 'security_engineer',
                    'goal': '评估安全风险，实施安全措施，保护系统安全',
                    'backstory': '网络安全专家，精通安全测试和风险评估',
                    'tools': ['security_assessment', 'penetration_testing', 'risk_management']
                }
            }
        }
    
    def _create_team_members(self) -> Dict[str, TeamMember]:
        """创建团队成员"""
        members = {}
        
        # 项目经理
        members['project_manager'] = TeamMember(
            id=str(uuid.uuid4()),
            name="张经理",
            role="项目经理",
            skills=["项目管理", "团队协作", "风险控制", "敏捷开发"],
            experience_years=8,
            hourly_rate=200,
            availability=40
        )
        
        # 产品经理
        members['product_manager'] = TeamMember(
            id=str(uuid.uuid4()),
            name="李产品",
            role="产品经理",
            skills=["需求分析", "用户研究", "产品设计", "数据分析"],
            experience_years=6,
            hourly_rate=180,
            availability=40
        )
        
        # 技术负责人
        members['tech_lead'] = TeamMember(
            id=str(uuid.uuid4()),
            name="王技术",
            role="技术负责人",
            skills=["系统架构", "技术选型", "代码审查", "团队指导"],
            experience_years=10,
            hourly_rate=250,
            availability=40
        )
        
        # 前端开发
        members['frontend_developer'] = TeamMember(
            id=str(uuid.uuid4()),
            name="陈前端",
            role="前端开发",
            skills=["React", "Vue", "TypeScript", "CSS", "前端优化"],
            experience_years=5,
            hourly_rate=150,
            availability=40
        )
        
        # 后端开发
        members['backend_developer'] = TeamMember(
            id=str(uuid.uuid4()),
            name="刘后端",
            role="后端开发",
            skills=["Python", "Java", "数据库设计", "API设计", "微服务"],
            experience_years=6,
            hourly_rate=160,
            availability=40
        )
        
        # AI工程师
        members['ai_engineer'] = TeamMember(
            id=str(uuid.uuid4()),
            name="赵AI",
            role="AI工程师",
            skills=["机器学习", "深度学习", "NLP", "大模型", "Python"],
            experience_years=7,
            hourly_rate=220,
            availability=40
        )
        
        # 测试工程师
        members['qa_engineer'] = TeamMember(
            id=str(uuid.uuid4()),
            name="孙测试",
            role="测试工程师",
            skills=["自动化测试", "性能测试", "安全测试", "测试策略"],
            experience_years=4,
            hourly_rate=120,
            availability=40
        )
        
        # DevOps工程师
        members['devops_engineer'] = TeamMember(
            id=str(uuid.uuid4()),
            name="周运维",
            role="DevOps工程师",
            skills=["Docker", "Kubernetes", "CI/CD", "监控", "云服务"],
            experience_years=5,
            hourly_rate=170,
            availability=40
        )
        
        return members
    
    def create_project(self, name: str, description: str, budget: float, 
                      duration_weeks: int, required_roles: List[str]) -> Project:
        """创建新项目"""
        project_id = str(uuid.uuid4())
        
        # 计算项目成本
        total_cost = self._calculate_project_cost(required_roles, duration_weeks)
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            budget=budget,
            duration_weeks=duration_weeks,
            required_roles=required_roles,
            estimated_cost=total_cost,
            status="规划中",
            created_at=datetime.now(),
            phases=[]
        )
        
        self.projects[project_id] = project
        return project
    
    def _calculate_project_cost(self, roles: List[str], duration_weeks: int) -> float:
        """计算项目成本"""
        total_cost = 0
        hours_per_week = 40
        
        for role in roles:
            if role in self.team_members:
                member = self.team_members[role]
                weekly_cost = member.hourly_rate * hours_per_week
                total_cost += weekly_cost * duration_weeks
        
        return total_cost
    
    def assign_team_to_project(self, project_id: str, assigned_roles: Dict[str, str]) -> bool:
        """为项目分配团队"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        project.assigned_team = assigned_roles
        project.status = "进行中"
        
        return True
    
    def create_project_phase(self, project_id: str, phase_name: str, 
                           duration_weeks: int, tasks: List[str]) -> ProjectPhase:
        """创建项目阶段"""
        if project_id not in self.projects:
            raise ValueError("项目不存在")
        
        phase = ProjectPhase(
            name=phase_name,
            duration_weeks=duration_weeks,
            tasks=[],
            status="未开始"
        )
        
        # 创建任务
        for task_desc in tasks:
            task = ProjectTask(
                id=str(uuid.uuid4()),
                description=task_desc,
                status=TaskStatus.PENDING,
                assigned_to=None,
                estimated_hours=0,
                actual_hours=0
            )
            phase.tasks.append(task)
        
        project = self.projects[project_id]
        project.phases.append(phase)
        
        return phase
    
    def update_task_status(self, project_id: str, phase_index: int, 
                          task_index: int, status: TaskStatus, 
                          assigned_to: Optional[str] = None) -> bool:
        """更新任务状态"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        if phase_index >= len(project.phases):
            return False
        
        phase = project.phases[phase_index]
        if task_index >= len(phase.tasks):
            return False
        
        task = phase.tasks[task_index]
        task.status = status
        if assigned_to:
            task.assigned_to = assigned_to
        
        return True
    
    def generate_project_report(self, project_id: str) -> ProjectReport:
        """生成项目报告"""
        if project_id not in self.projects:
            raise ValueError("项目不存在")
        
        project = self.projects[project_id]
        
        # 计算进度
        total_tasks = 0
        completed_tasks = 0
        
        for phase in project.phases:
            for task in phase.tasks:
                total_tasks += 1
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks += 1
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 计算成本
        actual_cost = 0
        for phase in project.phases:
            for task in phase.tasks:
                actual_cost += task.actual_hours * 150  # 假设平均时薪150
        
        report = ProjectReport(
            project_id=project_id,
            project_name=project.name,
            progress=progress,
            budget_used=actual_cost,
            budget_remaining=project.budget - actual_cost,
            estimated_completion=datetime.now(),
            risks=[],
            recommendations=[]
        )
        
        return report
    
    def display_team_info(self):
        """显示团队信息"""
        if not RICH_AVAILABLE:
            print("=== 团队信息 ===")
            for role, member in self.team_members.items():
                print(f"{member.name} ({member.role}) - {member.experience_years}年经验")
            return
        
        table = Table(title="团队成员信息")
        table.add_column("姓名", style="cyan")
        table.add_column("角色", style="magenta")
        table.add_column("技能", style="green")
        table.add_column("经验", style="yellow")
        table.add_column("时薪", style="red")
        
        for role, member in self.team_members.items():
            skills_str = ", ".join(member.skills[:3]) + "..." if len(member.skills) > 3 else ", ".join(member.skills)
            table.add_row(
                member.name,
                member.role,
                skills_str,
                f"{member.experience_years}年",
                f"¥{member.hourly_rate}/小时"
            )
        
        console.print(table)
    
    def create_agent(self, role: str) -> Optional[Agent]:
        """创建单个Agent"""
        if not CREWAI_AVAILABLE:
            print("CrewAI未安装，无法创建Agent")
            return None
            
        if role not in self.config['agents']:
            raise ValueError(f"未知的角色: {role}")
        
        agent_config = self.config['agents'][role]
        
        # 获取角色特定的学习资源
        resources = get_role_specific_resources(role)
        learning_path = get_learning_path(role)
        
        # 构建增强的backstory，包含学习资源
        enhanced_backstory = f"{agent_config['backstory']}\n\n"
        enhanced_backstory += f"学习资源:\n{learning_path}\n\n"
        enhanced_backstory += "相关文档:\n"
        for resource in resources[:5]:  # 只显示前5个资源
            enhanced_backstory += f"- {resource.title}: {resource.url}\n"
        
        # 创建CrewAI Agent
        agent = Agent(
            role=agent_config['name'],
            goal=agent_config['goal'],
            backstory=enhanced_backstory,
            verbose=agent_config.get('verbose', True),
            allow_delegation=agent_config.get('allow_delegation', True),
            llm=self.llm_client.get_llm()
        )
        
        self.agents[role] = agent
        return agent
    
    def create_team(self, roles: List[str]) -> List[Agent]:
        """创建团队"""
        team = []
        for role in roles:
            agent = self.create_agent(role)
            if agent:
                team.append(agent)
        return team
    
    def create_project_crew(self, project_name: str, roles: List[str]) -> Optional[Crew]:
        """创建项目团队"""
        if not CREWAI_AVAILABLE:
            print("CrewAI未安装，无法创建Crew")
            return None
            
        team = self.create_team(roles)
        if not team:
            return None
        
        # 创建任务
        tasks = self._create_project_tasks(project_name, team)
        
        # 创建Crew
        crew = Crew(
            agents=team,
            tasks=tasks,
            verbose=True,
            process=Process.sequential
        )
        
        self.crews[project_name] = crew
        return crew
    
    def _create_project_tasks(self, project_name: str, team: List[Agent]) -> List[Task]:
        """创建项目任务"""
        tasks = []
        
        # 项目启动任务
        pm_agent = next((agent for agent in team if '经理' in agent.role), None)
        if pm_agent:
            tasks.append(Task(
                description=f"启动项目 '{project_name}'，制定项目计划和时间表",
                agent=pm_agent,
                expected_output="项目计划文档，包含时间表、里程碑和风险分析"
            ))
        
        # 需求分析任务
        pm_agent = next((agent for agent in team if '产品' in agent.role), None)
        if pm_agent:
            tasks.append(Task(
                description=f"分析项目 '{project_name}' 的业务需求和技术需求",
                agent=pm_agent,
                expected_output="详细的需求文档，包含功能需求和非功能需求"
            ))
        
        # 技术设计任务
        tech_agent = next((agent for agent in team if '技术' in agent.role), None)
        if tech_agent:
            tasks.append(Task(
                description=f"为项目 '{project_name}' 设计技术架构和系统方案",
                agent=tech_agent,
                expected_output="技术架构文档，包含系统设计、技术选型和接口定义"
            ))
        
        # 开发任务
        dev_agents = [agent for agent in team if '开发' in agent.role]
        for dev_agent in dev_agents:
            tasks.append(Task(
                description=f"根据设计文档开发项目 '{project_name}' 的相应模块",
                agent=dev_agent,
                expected_output="功能完整的代码模块，包含单元测试和文档"
            ))
        
        # 测试任务
        qa_agent = next((agent for agent in team if '测试' in agent.role), None)
        if qa_agent:
            tasks.append(Task(
                description=f"为项目 '{project_name}' 制定测试策略并执行测试",
                agent=qa_agent,
                expected_output="测试报告，包含测试用例、测试结果和缺陷报告"
            ))
        
        return tasks
    
    def run_project(self, project_name: str, roles: List[str], project_description: str) -> str:
        """运行项目"""
        crew = self.create_project_crew(project_name, roles)
        if not crew:
            return "无法创建项目团队，请检查CrewAI是否正确安装"
        
        # 添加项目描述到第一个任务
        if crew.tasks:
            crew.tasks[0].description = f"项目描述: {project_description}\n\n{crew.tasks[0].description}"
        
        result = crew.kickoff()
        return result
    
    def get_agent_info(self, role: str) -> Dict[str, Any]:
        """获取Agent信息"""
        if role not in self.config['agents']:
            return {}
        
        agent_config = self.config['agents'][role]
        resources = get_role_specific_resources(role)
        
        return {
            'name': agent_config['name'],
            'role': agent_config['role'],
            'goal': agent_config['goal'],
            'backstory': agent_config['backstory'],
            'tools': agent_config.get('tools', []),
            'resources': [{'title': r.title, 'url': r.url, 'description': r.description} for r in resources[:5]]
        }
    
    def search_knowledge(self, query: str) -> str:
        """搜索知识库"""
        return search_knowledge_base(query)
    
    def get_learning_resources(self, role: str) -> str:
        """获取学习资源"""
        resources = get_role_specific_resources(role)
        return self.knowledge_manager.format_resources_for_agent(resources)
    
    def get_learning_path_for_role(self, role: str) -> str:
        """获取角色学习路径"""
        return get_learning_path(role)
    
    def list_available_roles(self) -> List[str]:
        """列出可用角色"""
        return list(self.config['agents'].keys())
    
    def get_team_cost_estimate(self, roles: List[str], duration_months: int = 3) -> Dict[str, Any]:
        """估算团队成本"""
        # 月薪范围（人民币）
        salary_ranges = {
            'project_manager': (15000, 25000),
            'product_manager': (12000, 20000),
            'tech_lead': (20000, 35000),
            'frontend_developer': (10000, 18000),
            'backend_developer': (12000, 20000),
            'ai_engineer': (15000, 30000),
            'qa_engineer': (8000, 15000),
            'devops_engineer': (12000, 20000),
            'ui_designer': (8000, 15000),
            'business_analyst': (10000, 18000),
            'security_engineer': (12000, 25000)
        }
        
        total_min = 0
        total_max = 0
        role_costs = {}
        
        for role in roles:
            if role in salary_ranges:
                min_salary, max_salary = salary_ranges[role]
                role_costs[role] = {
                    'min_monthly': min_salary,
                    'max_monthly': max_salary,
                    'min_total': min_salary * duration_months,
                    'max_total': max_salary * duration_months
                }
                total_min += min_salary
                total_max += max_salary
        
        return {
            'roles': role_costs,
            'total_monthly': {
                'min': total_min,
                'max': total_max
            },
            'total_project': {
                'min': total_min * duration_months,
                'max': total_max * duration_months
            },
            'duration_months': duration_months
        }


def create_demo_team() -> TeamManager:
    """创建演示团队"""
    manager = TeamManager()
    
    # 演示项目
    project_name = "智能客服系统"
    roles = ['project_manager', 'product_manager', 'tech_lead', 'backend_developer', 'ai_engineer', 'qa_engineer']
    
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
    
    print(f"=== 项目演示: {project_name} ===")
    print(f"团队成员: {', '.join([manager.config['agents'][role]['name'] for role in roles])}")
    print(f"项目描述: {project_description}")
    
    return manager, project_name, roles, project_description


if __name__ == "__main__":
    # 演示知识库功能
    manager = TeamManager()
    
    print("=== 知识库演示 ===")
    
    # 搜索Python相关资源
    print("\n1. 搜索Python相关资源:")
    python_resources = manager.search_knowledge("Python")
    print(python_resources[:500] + "..." if len(python_resources) > 500 else python_resources)
    
    # 获取开发工程师学习路径
    print("\n2. 开发工程师学习路径:")
    dev_path = manager.get_learning_path_for_role("developer")
    print(dev_path)
    
    # 获取AI工程师资源
    print("\n3. AI工程师学习资源:")
    ai_resources = manager.get_learning_resources("ai_engineer")
    print(ai_resources[:500] + "..." if len(ai_resources) > 500 else ai_resources)
    
    # 团队成本估算
    print("\n4. 团队成本估算:")
    roles = ['project_manager', 'tech_lead', 'backend_developer', 'ai_engineer']
    cost_estimate = manager.get_team_cost_estimate(roles, 3)
    print(f"3个月项目总成本: {cost_estimate['total_project']['min']:,} - {cost_estimate['total_project']['max']:,} 元") 