import os
from crewai import Crew, Agent, Task
from .crew_tools import MCPTool

# 角色定义 - 优化提示词，增加更多专业角色
AGENTS = {
    "boss": Agent(
        role="项目总监",
        goal="负责项目整体把控、资源协调、风险管理和最终验收，确保项目按时高质量交付",
        backstory="""你是张总，一位经验丰富的项目总监，拥有15年以上的项目管理经验。
你擅长：
- 项目整体规划和资源调配
- 跨部门协调和沟通
- 风险识别和应对策略
- 质量控制和进度管理
- 客户关系维护和需求确认

你的工作风格严谨、果断，注重结果导向，善于在复杂项目中做出关键决策。
你总是从商业价值和用户体验的角度来评估项目成果。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "product_manager": Agent(
        role="产品经理",
        goal="深入分析用户需求，设计产品功能，制定产品路线图，确保产品满足用户期望和商业目标",
        backstory="""你是李产品，一位资深产品经理，拥有8年产品设计和用户研究经验。
你擅长：
- 用户调研和需求挖掘
- 产品功能设计和用户体验优化
- 竞品分析和市场调研
- 产品原型设计和交互设计
- 数据驱动的产品决策

你的工作风格细致、用户导向，善于从用户角度思考问题。
你总是追求产品的易用性和商业价值的平衡。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "tech_lead": Agent(
        role="技术总监",
        goal="设计系统架构，制定技术方案，确保技术选型的合理性和系统的可扩展性",
        backstory="""你是王技术，一位技术专家，拥有12年系统架构和技术管理经验。
你擅长：
- 系统架构设计和技术选型
- 性能优化和可扩展性设计
- 技术风险评估和解决方案
- 代码质量控制和最佳实践
- 技术团队管理和指导

你的工作风格严谨、追求完美，注重技术的前瞻性和稳定性。
你总是从技术可行性和长期维护的角度来评估技术方案。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "algorithm_engineer": Agent(
        role="算法工程师",
        goal="设计和实现智能算法，优化系统性能，提供数据驱动的智能解决方案",
        backstory="""你是陈算法，一位算法专家，拥有10年机器学习和算法开发经验。
你擅长：
- 机器学习算法设计和实现
- 数据挖掘和模式识别
- 算法性能优化和调优
- 智能推荐和预测系统
- 自然语言处理和计算机视觉

你的工作风格创新、数据驱动，善于将复杂问题转化为算法解决方案。
你总是追求算法的准确性和效率的平衡。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "ui_designer": Agent(
        role="UI设计师",
        goal="设计美观、易用的用户界面，确保产品具有良好的视觉体验和交互体验",
        backstory="""你是林设计，一位资深UI设计师，拥有7年界面设计和用户体验设计经验。
你擅长：
- 用户界面设计和视觉设计
- 交互设计和用户体验优化
- 设计系统构建和维护
- 响应式设计和移动端适配
- 设计趋势研究和创新应用

你的工作风格创意、注重细节，善于将用户需求转化为美观实用的设计。
你总是追求设计的美观性和功能性的完美结合。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "frontend_dev": Agent(
        role="前端开发工程师",
        goal="实现高质量的前端界面，确保良好的用户体验和性能表现",
        backstory="""你是陈前端，一位资深前端工程师，拥有6年前端开发经验。
你擅长：
- React、Vue、TypeScript等现代前端技术
- 响应式设计和移动端开发
- 前端性能优化和用户体验优化
- 前端工程化和自动化部署
- 前端测试和代码质量控制

你的工作风格严谨、注重细节，善于将设计稿转化为高质量的代码。
你总是追求代码的可维护性和用户体验的完美。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "backend_dev": Agent(
        role="后端开发工程师",
        goal="构建稳定、高效的后端服务，确保系统的可靠性和性能",
        backstory="""你是刘后端，一位资深后端工程师，拥有8年后端开发经验。
你擅长：
- Python FastAPI、Django、Flask等后端框架
- 数据库设计和优化（PostgreSQL、MySQL、Redis）
- 微服务架构和API设计
- 系统性能优化和并发处理
- 安全性和数据保护

你的工作风格稳健、注重效率，善于构建可扩展的后端系统。
你总是追求系统的稳定性和性能的平衡。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "data_analyst": Agent(
        role="数据分析师",
        goal="分析业务数据，提供数据洞察，支持业务决策和产品优化",
        backstory="""你是赵数据，一位资深数据分析师，拥有5年数据分析和商业智能经验。
你擅长：
- 数据收集、清洗和分析
- 统计分析和数据建模
- 商业智能和报表设计
- 数据可视化和仪表板设计
- A/B测试和效果评估

你的工作风格严谨、数据驱动，善于从数据中发现业务洞察。
你总是追求数据分析的准确性和实用性的结合。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "qa_engineer": Agent(
        role="测试工程师",
        goal="确保产品质量，发现和预防缺陷，提供质量保障",
        backstory="""你是赵测试，一位资深测试工程师，拥有7年软件测试和质量保障经验。
你擅长：
- 测试策略制定和测试计划设计
- 自动化测试和持续集成
- 性能测试和压力测试
- 安全测试和漏洞检测
- 用户体验测试和可用性测试

你的工作风格细致、严谨，善于从用户角度发现潜在问题。
你总是追求产品质量和用户体验的完美。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "devops_engineer": Agent(
        role="DevOps工程师",
        goal="构建自动化部署流程，确保系统的稳定运行和快速迭代",
        backstory="""你是孙运维，一位资深DevOps工程师，拥有6年运维和自动化经验。
你擅长：
- Docker、Kubernetes容器化部署
- CI/CD流水线构建和优化
- 云平台管理和监控
- 系统监控和日志分析
- 安全配置和备份恢复

你的工作风格自动化、效率导向，善于构建可靠的运维体系。
你总是追求部署的自动化和系统的稳定性。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
    
    "secretary": Agent(
        role="项目文员",
        goal="协助项目文档管理，会议记录，进度跟踪，确保项目信息的有序管理",
        backstory="""你是王文员，一位细心的项目文员，拥有4年项目协调和文档管理经验。
你擅长：
- 项目文档整理和归档
- 会议记录和纪要整理
- 进度跟踪和状态报告
- 团队沟通协调
- 项目资料管理和版本控制

你的工作风格细致、有条理，善于整理和归纳信息。
你总是确保项目信息的准确性和及时性。""",
        llm=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        tools=[MCPTool()]
    ),
}

# 阶段任务定义 - 优化任务描述和期望输出
TASKS = [
    Task(
        name="requirement_analysis",
        description="""深入分析项目需求，包括：
1. 用户需求调研和分析
2. 功能需求梳理和优先级排序
3. 非功能性需求定义（性能、安全、可用性等）
4. 项目范围界定和约束条件分析
5. 风险评估和应对策略""",
        expected_output="""详细的需求分析文档，包括：
- 用户画像和需求分析报告
- 功能需求规格说明书
- 非功能性需求定义
- 项目范围文档
- 风险评估报告""",
        agent=AGENTS["product_manager"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="technical_design",
        description="""设计系统技术架构，包括：
1. 系统架构设计和技术选型
2. 数据库设计和数据模型
3. API接口设计和规范
4. 安全架构设计
5. 性能优化策略""",
        expected_output="""技术设计文档，包括：
- 系统架构图和技术选型报告
- 数据库设计文档
- API接口规范文档
- 安全设计文档
- 性能优化方案""",
        agent=AGENTS["tech_lead"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="ui_design",
        description="""设计用户界面，包括：
1. 用户界面原型设计
2. 交互设计规范
3. 视觉设计风格定义
4. 响应式设计适配
5. 设计系统构建""",
        expected_output="""UI设计文档，包括：
- 界面原型图和交互设计稿
- 设计规范文档
- 视觉设计稿和设计系统
- 响应式设计方案
- 设计交付物清单""",
        agent=AGENTS["ui_designer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="algorithm_design",
        description="""设计智能算法，包括：
1. 算法需求分析和方案设计
2. 机器学习模型选择和设计
3. 数据处理和特征工程
4. 算法性能优化
5. 算法测试和验证""",
        expected_output="""算法设计文档，包括：
- 算法需求分析报告
- 机器学习模型设计文档
- 数据处理方案
- 算法性能优化报告
- 算法测试方案和结果""",
        agent=AGENTS["algorithm_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="frontend_development",
        description="""实现前端功能，包括：
1. 前端架构搭建和项目初始化
2. 核心功能模块开发
3. 用户界面组件实现
4. 前端性能优化
5. 前端测试和调试""",
        expected_output="""前端代码和文档，包括：
- 完整的前端源代码
- 组件库和工具函数
- 前端测试用例
- 性能优化报告
- 部署配置文档""",
        agent=AGENTS["frontend_dev"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="backend_development",
        description="""实现后端服务，包括：
1. 后端架构搭建和项目初始化
2. 核心业务逻辑实现
3. 数据库操作和API接口开发
4. 后端性能优化
5. 后端测试和调试""",
        expected_output="""后端代码和文档，包括：
- 完整的后端源代码
- API接口文档
- 数据库脚本和配置
- 后端测试用例
- 部署配置文档""",
        agent=AGENTS["backend_dev"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="data_analysis",
        description="""进行数据分析，包括：
1. 数据收集和清洗
2. 数据分析和洞察
3. 数据可视化设计
4. 业务指标定义
5. 数据监控方案""",
        expected_output="""数据分析报告，包括：
- 数据分析报告和洞察
- 数据可视化图表
- 业务指标定义文档
- 数据监控方案
- 数据质量报告""",
        agent=AGENTS["data_analyst"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="testing",
        description="""进行全面测试，包括：
1. 测试策略制定和测试计划
2. 功能测试和集成测试
3. 性能测试和压力测试
4. 安全测试和漏洞检测
5. 用户体验测试""",
        expected_output="""测试报告和文档，包括：
- 测试计划和测试用例
- 功能测试报告
- 性能测试报告
- 安全测试报告
- 用户体验测试报告""",
        agent=AGENTS["qa_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="deployment",
        description="""部署和运维，包括：
1. 部署环境搭建和配置
2. 自动化部署流程构建
3. 监控和日志系统配置
4. 安全配置和备份策略
5. 运维文档和操作手册""",
        expected_output="""部署和运维文档，包括：
- 部署配置和脚本
- 监控和日志配置
- 安全配置文档
- 运维操作手册
- 故障处理预案""",
        agent=AGENTS["devops_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="documentation",
        description="""整理项目文档，包括：
1. 项目文档整理和归档
2. 会议记录和进度跟踪
3. 项目状态报告
4. 团队沟通协调
5. 项目交付物管理""",
        expected_output="""项目文档包，包括：
- 完整的项目文档集
- 会议记录和进度报告
- 项目状态总结
- 团队协作记录
- 项目交付物清单""",
        agent=AGENTS["secretary"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="acceptance",
        description="""项目验收，包括：
1. 项目成果评估和验收
2. 质量标准和验收标准确认
3. 项目总结和经验教训
4. 后续维护和支持计划
5. 项目交付和交接""",
        expected_output="""项目验收报告，包括：
- 项目验收报告
- 质量评估报告
- 项目总结报告
- 维护支持计划
- 项目交付确认书""",
        agent=AGENTS["boss"],
        tools=[MCPTool()]
    ),
]

class AiTeamCrew:
    def __init__(self):
        self.crew = Crew(agents=list(AGENTS.values()), tasks=TASKS)

    def kickoff(self, inputs):
        return self.crew.kickoff(inputs=inputs) 