import autogen
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
import json
import os

class CodeTeamAgentSystem:
    """代码团队Agent系统"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.config_list = [
            {
                "model": "gpt-4",
                "api_key": openai_api_key
            }
        ]
        
        # 初始化AutoGen配置
        autogen.config_list_from_json(
            "OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-4"]
            }
        )
        
        # 创建团队成员
        self.create_team_members()
        
    def create_team_members(self):
        """创建团队成员"""
        
        # 老板Agent (AutoGen)
        self.boss = autogen.AssistantAgent(
            name="老板",
            llm_config={"config_list": self.config_list},
            system_message="""你是一个经验丰富的公司老板，负责：
1. 理解客户需求
2. 制定项目目标
3. 分配资源和预算
4. 监督项目进度
5. 最终决策和验收

你需要与产品经理和技术团队协作，确保项目成功交付。"""
        )
        
        # 产品经理Agent (AutoGen)
        self.product_manager = autogen.AssistantAgent(
            name="产品经理",
            llm_config={"config_list": self.config_list},
            system_message="""你是一个专业的产品经理，负责：
1. 需求分析和产品规划
2. 用户故事和功能设计
3. 产品原型和交互设计
4. 与开发团队沟通需求
5. 产品验收和迭代

你需要将老板的需求转化为具体的产品方案。"""
        )
        
        # 技术负责人Agent (CrewAI)
        self.tech_lead = Agent(
            role='技术负责人',
            goal='设计技术方案，指导开发团队，确保技术质量',
            backstory='你是一个经验丰富的技术负责人，擅长系统架构设计和技术选型',
            verbose=True
        )
        
        # 前端开发Agent (CrewAI)
        self.frontend_dev = Agent(
            role='前端开发工程师',
            goal='开发用户界面，实现前端功能',
            backstory='你是一个专业的前端开发工程师，精通React、Vue等框架',
            verbose=True
        )
        
        # 后端开发Agent (CrewAI)
        self.backend_dev = Agent(
            role='后端开发工程师',
            goal='开发后端服务，设计数据库，实现API',
            backstory='你是一个专业的后端开发工程师，精通Python、Java等语言',
            verbose=True
        )
        
        # 测试工程师Agent (CrewAI)
        self.qa_engineer = Agent(
            role='测试工程师',
            goal='设计测试用例，执行测试，保证产品质量',
            backstory='你是一个专业的测试工程师，擅长自动化测试和质量管理',
            verbose=True
        )
        
        # DevOps工程师Agent (CrewAI)
        self.devops_engineer = Agent(
            role='DevOps工程师',
            goal='系统部署，运维监控，自动化流程',
            backstory='你是一个专业的DevOps工程师，精通Docker、Kubernetes等技术',
            verbose=True
        )
    
    def create_project_tasks(self, project_requirements: str) -> List[Task]:
        """创建项目任务"""
        
        tasks = [
            Task(
                description=f"""
                基于以下项目需求，设计详细的技术方案：
                {project_requirements}
                
                包括：
                1. 系统架构设计
                2. 技术栈选型
                3. 数据库设计
                4. API接口设计
                5. 部署方案
                """,
                agent=self.tech_lead
            ),
            
            Task(
                description="""
                基于技术方案，开发前端用户界面：
                1. 页面设计和布局
                2. 组件开发
                3. 用户交互实现
                4. 响应式设计
                5. 前端测试
                """,
                agent=self.frontend_dev
            ),
            
            Task(
                description="""
                基于技术方案，开发后端服务：
                1. 数据库设计和实现
                2. API接口开发
                3. 业务逻辑实现
                4. 安全认证
                5. 性能优化
                """,
                agent=self.backend_dev
            ),
            
            Task(
                description="""
                设计并执行测试计划：
                1. 功能测试用例
                2. 性能测试
                3. 安全测试
                4. 自动化测试脚本
                5. 测试报告
                """,
                agent=self.qa_engineer
            ),
            
            Task(
                description="""
                系统部署和运维：
                1. 环境配置
                2. 容器化部署
                3. 监控系统设置
                4. 自动化部署流程
                5. 运维文档
                """,
                agent=self.devops_engineer
            )
        ]
        
        return tasks
    
    def execute_project(self, project_requirements: str) -> Dict[str, Any]:
        """执行项目"""
        
        print("=== 项目启动 ===")
        print(f"项目需求: {project_requirements}")
        print()
        
        # 第一阶段：老板和产品经理讨论
        print("=== 第一阶段：需求讨论 ===")
        
        # 创建用户代理
        user_proxy = autogen.UserProxyAgent(
            name="客户",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config={"config_list": self.config_list},
            system_message="你代表客户，提出项目需求。"
        )
        
        # 启动讨论
        user_proxy.initiate_chat(
            self.boss,
            message=f"我们有一个新项目需求：{project_requirements}。请与产品经理讨论并制定详细的产品方案。"
        )
        
        # 产品经理参与讨论
        self.boss.initiate_chat(
            self.product_manager,
            message="请基于客户需求，制定详细的产品方案，包括功能列表、用户故事、技术需求等。"
        )
        
        print("\n=== 第二阶段：技术开发 ===")
        
        # 第二阶段：技术团队开发
        tasks = self.create_project_tasks(project_requirements)
        
        # 创建开发团队
        development_crew = Crew(
            agents=[self.tech_lead, self.frontend_dev, self.backend_dev, 
                   self.qa_engineer, self.devops_engineer],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # 执行开发任务
        result = development_crew.kickoff()
        
        print("\n=== 第三阶段：项目验收 ===")
        
        # 第三阶段：老板验收
        user_proxy.initiate_chat(
            self.boss,
            message=f"项目开发已完成，请验收项目成果：\n{result}"
        )
        
        return {
            "requirements": project_requirements,
            "development_result": result,
            "status": "completed"
        }

# 使用示例
if __name__ == "__main__":
    # 配置OpenAI API密钥
    OPENAI_API_KEY = "your-openai-api-key"
    
    # 创建团队系统
    team_system = CodeTeamAgentSystem(OPENAI_API_KEY)
    
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
    
    print("\n=== 项目完成 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False)) 