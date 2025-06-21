import json
import time
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TeamMember:
    """团队成员"""
    name: str
    role: str
    skills: List[str]
    responsibilities: List[str]

@dataclass
class ProjectTask:
    """项目任务"""
    name: str
    description: str
    assignee: str
    status: str
    output: str = ""

class CodeTeamAgentSystem:
    """简化的代码团队Agent系统"""
    
    def __init__(self):
        self.team_members = self.create_team()
        self.project_tasks = []
        
    def create_team(self) -> Dict[str, TeamMember]:
        """创建团队"""
        return {
            "boss": TeamMember(
                name="老板",
                role="项目决策者",
                skills=["项目管理", "商务谈判", "资源分配"],
                responsibilities=["需求理解", "项目目标制定", "最终验收"]
            ),
            "product_manager": TeamMember(
                name="产品经理",
                role="产品规划师",
                skills=["需求分析", "产品设计", "用户体验"],
                responsibilities=["需求分析", "产品方案", "功能设计"]
            ),
            "tech_lead": TeamMember(
                name="技术负责人",
                role="技术架构师",
                skills=["系统设计", "技术选型", "架构规划"],
                responsibilities=["技术方案", "架构设计", "技术指导"]
            ),
            "frontend_dev": TeamMember(
                name="前端开发",
                role="前端工程师",
                skills=["React", "Vue", "JavaScript", "CSS"],
                responsibilities=["前端开发", "UI实现", "用户交互"]
            ),
            "backend_dev": TeamMember(
                name="后端开发",
                role="后端工程师",
                skills=["Python", "Java", "数据库", "API"],
                responsibilities=["后端开发", "数据库设计", "API开发"]
            ),
            "qa_engineer": TeamMember(
                name="测试工程师",
                role="质量保证",
                skills=["测试设计", "自动化测试", "质量监控"],
                responsibilities=["测试计划", "质量保证", "缺陷管理"]
            ),
            "devops_engineer": TeamMember(
                name="DevOps工程师",
                role="运维专家",
                skills=["Docker", "Kubernetes", "CI/CD", "监控"],
                responsibilities=["系统部署", "运维监控", "自动化"]
            )
        }
    
    def simulate_llm_response(self, role: str, prompt: str) -> str:
        """模拟LLM响应"""
        responses = {
            "boss": {
                "需求理解": "我理解了客户需求，这是一个很有价值的项目。我们需要确保按时交付高质量的产品。",
                "项目验收": "项目已经完成，质量符合预期，可以交付给客户。"
            },
            "product_manager": {
                "需求分析": "基于客户需求，我制定了详细的产品方案，包括用户故事、功能列表和交互设计。",
                "产品方案": "产品方案已确定，包括核心功能模块、用户界面设计和业务流程。"
            },
            "tech_lead": {
                "技术方案": "我设计了完整的技术架构，包括前端React、后端Python Flask、MySQL数据库和Docker部署。",
                "架构设计": "系统架构采用微服务设计，支持高并发和可扩展性。"
            },
            "frontend_dev": {
                "前端开发": "前端页面已开发完成，包括用户界面、组件库和响应式设计。",
                "UI实现": "所有页面都已实现，用户体验良好，支持移动端适配。"
            },
            "backend_dev": {
                "后端开发": "后端API已开发完成，包括用户管理、数据操作和业务逻辑。",
                "数据库设计": "数据库设计合理，支持数据完整性和性能优化。"
            },
            "qa_engineer": {
                "测试计划": "测试计划已制定，包括功能测试、性能测试和安全测试。",
                "质量保证": "所有测试用例已执行，产品质量符合标准。"
            },
            "devops_engineer": {
                "系统部署": "系统已部署到云服务器，配置了监控和自动化部署。",
                "运维监控": "运维环境已搭建完成，包括日志监控、性能监控和告警系统。"
            }
        }
        
        # 根据角色和提示返回相应响应
        for key, response in responses.get(role, {}).items():
            if key in prompt:
                return response
        
        return f"{role}已完成相关任务。"
    
    def create_project_tasks(self, project_requirements: str) -> List[ProjectTask]:
        """创建项目任务"""
        tasks = [
            ProjectTask("需求分析", "分析客户需求，制定产品方案", "product_manager", "pending"),
            ProjectTask("技术方案", "设计技术架构和开发方案", "tech_lead", "pending"),
            ProjectTask("前端开发", "开发用户界面和前端功能", "frontend_dev", "pending"),
            ProjectTask("后端开发", "开发后端服务和API接口", "backend_dev", "pending"),
            ProjectTask("测试验证", "执行测试计划，保证质量", "qa_engineer", "pending"),
            ProjectTask("系统部署", "部署系统，配置运维环境", "devops_engineer", "pending")
        ]
        return tasks
    
    def execute_task(self, task: ProjectTask, project_requirements: str) -> str:
        """执行任务"""
        print(f"🔄 {task.assignee} 正在执行: {task.name}")
        
        # 模拟任务执行时间
        time.sleep(1)
        
        # 生成任务输出
        prompt = f"基于项目需求'{project_requirements}'，执行{task.name}任务"
        output = self.simulate_llm_response(task.assignee, prompt)
        
        task.status = "completed"
        task.output = output
        
        print(f"✅ {task.assignee} 完成: {task.name}")
        print(f"   输出: {output}")
        print()
        
        return output
    
    def execute_project(self, project_requirements: str) -> Dict[str, Any]:
        """执行完整项目"""
        
        print("🚀 === 项目启动 ===")
        print(f"📋 项目需求: {project_requirements}")
        print()
        
        # 第一阶段：老板和产品经理讨论
        print("👥 === 第一阶段：需求讨论 ===")
        
        boss_response = self.simulate_llm_response("boss", "需求理解")
        print(f"👨‍💼 老板: {boss_response}")
        
        pm_response = self.simulate_llm_response("product_manager", "需求分析")
        print(f"👩‍💼 产品经理: {pm_response}")
        
        print()
        
        # 第二阶段：技术开发
        print("⚙️ === 第二阶段：技术开发 ===")
        
        tasks = self.create_project_tasks(project_requirements)
        results = []
        
        for task in tasks:
            result = self.execute_task(task, project_requirements)
            results.append({
                "task": task.name,
                "assignee": task.assignee,
                "output": result
            })
        
        # 第三阶段：项目验收
        print("🎯 === 第三阶段：项目验收 ===")
        
        boss_approval = self.simulate_llm_response("boss", "项目验收")
        print(f"👨‍💼 老板验收: {boss_approval}")
        
        print()
        print("🎉 === 项目完成 ===")
        
        return {
            "project_requirements": project_requirements,
            "team_members": {name: member.__dict__ for name, member in self.team_members.items()},
            "development_results": results,
            "final_approval": boss_approval,
            "status": "completed"
        }

# 使用示例
if __name__ == "__main__":
    # 创建团队系统
    team_system = CodeTeamAgentSystem()
    
    # 项目需求示例
    project_requirements = """
    开发一个在线图书管理系统，功能包括：
    1. 用户注册和登录
    2. 图书信息管理（增删改查）
    3. 图书借阅和归还
    4. 用户借阅历史查询
    5. 图书搜索和分类
    6. 管理员后台管理
    
    技术要求：
    - 前端使用React
    - 后端使用Python Flask
    - 数据库使用MySQL
    - 部署到云服务器
    """
    
    # 执行项目
    result = team_system.execute_project(project_requirements)
    
    # 输出详细结果
    print("\n📊 === 项目详细报告 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False)) 