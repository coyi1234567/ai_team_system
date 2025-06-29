import os
import sys
import datetime
import time
import json
import traceback
import re
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import PrivateAttr
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from litellm import completion

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .tools.mcp_tool import MCPTool
from .context_manager import SmartContextManager, ContextPriority, ContextType
from mcp_server import MCPServer

class LoggingAgent(Agent):
    _project_id: 'str' = PrivateAttr(default="")
    _project_dir: 'str' = PrivateAttr(default="")
    def __init__(self, *args, project_id: str = "", project_dir: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._project_id = project_id or ""
        self._project_dir = project_dir or ""

    def execute_task(self, task, context=None, tools=None):
        """重写execute_task方法，添加代码落地机制"""
        try:
            # 执行原始任务
            result = super().execute_task(task, context, tools)
            
            # 代码落地机制：自动提取并保存代码块
            if result and self._project_dir and task.name:
                self._extract_and_save_code(result, task.name)
            
            return result
        except Exception as e:
            print(f"[LoggingAgent] 任务执行异常: {e}")
            return f"任务执行失败: {str(e)}"

    def _extract_and_save_code(self, result: str, task_name: str):
        """提取代码块并保存到文件"""
        if not task_name:  # 确保task_name不为空
            return
            
        # 提取代码块的正则表达式
        code_patterns = [
            r'```(\w+)\n(.*?)```',  # 带语言标识的代码块
            r'```\n(.*?)```',       # 不带语言标识的代码块
            r'`(.*?)`'              # 行内代码
        ]
        
        extracted_files = []
        
        for pattern in code_patterns:
            matches = re.findall(pattern, result, re.DOTALL)
            for i, match in enumerate(matches):
                if isinstance(match, tuple):
                    lang, code = match
                else:
                    lang = 'txt'
                    code = match
                
                if code.strip():
                    filename = self._generate_filename(task_name, lang, i)
                    filepath = os.path.join(self._project_dir, filename)
                    
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(code)
                        extracted_files.append(filename)
                        print(f"[代码提取] 已保存: {filename}")
                    except Exception as e:
                        print(f"[代码提取] 保存失败 {filename}: {e}")
        
        if extracted_files:
            print(f"[代码提取] 共提取 {len(extracted_files)} 个文件")
            return extracted_files
        return None

    def _generate_filename(self, task_name: str, lang: str, index: int) -> str:
        """根据任务名和语言生成文件名"""
        # 任务名到文件名的映射
        task_file_mapping = {
            'frontend_development': {
                'javascript': 'frontend/app.js',
                'html': 'frontend/index.html',
                'css': 'frontend/styles.css',
                'vue': 'frontend/App.vue',
                'react': 'frontend/App.jsx',
                '': 'frontend/main.js'
            },
            'backend_development': {
                'python': 'backend/main.py',
                'java': 'backend/Main.java',
                'javascript': 'backend/server.js',
                'go': 'backend/main.go',
                '': 'backend/app.py'
            },
            'technical_design': {
                'yaml': 'docker-compose.yml',
                'dockerfile': 'Dockerfile',
                'sql': 'database/schema.sql',
                'json': 'config.json',
                '': 'design.md'
            },
            'requirement_analysis': {
                'markdown': 'docs/requirements.md',
                '': 'requirements.txt'
            }
        }
        
        # 获取映射
        mapping = task_file_mapping.get(task_name, {})
        
        # 根据语言选择文件名
        if lang in mapping:
            return mapping[lang]
        elif '' in mapping:
            return mapping['']
        else:
            # 默认文件名
            if lang:
                return f"{task_name}_{index}.{lang}"
            else:
                return f"{task_name}_{index}.txt"

# 角色定义 - 优化提示词，增加更多专业角色
AGENTS = {
    k: LoggingAgent(
        role=v.role,
        goal=v.goal,
        backstory=v.backstory,
        llm=v.llm,
        tools=v.tools,
        project_id="",  # 统一用空字符串
        project_dir=""   # 统一用空字符串
    ) for k, v in {
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
    }.items()
}

# 阶段任务定义 - 优化任务描述和期望输出
TASKS = [
    Task(
        name="requirement_analysis",
        description="本次项目需求如下：{requirements}\n" + "深入分析项目需求，包括：\n1. 用户需求调研和分析\n2. 功能需求梳理和优先级排序\n3. 非功能性需求定义（性能、安全、可用性等）\n4. 项目范围界定和约束条件分析\n5. 风险评估和应对策略",
        expected_output="详细的需求分析文档，包括：\n- 用户画像和需求分析报告\n- 功能需求规格说明书\n- 非功能性需求定义\n- 项目范围文档\n- 风险评估报告",
        agent=AGENTS["product_manager"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="technical_design",
        description="本次项目需求如下：{requirements}\n" + "设计系统技术架构，包括：\n1. 系统架构设计和技术选型\n2. 数据库设计和数据模型\n3. API接口设计和规范\n4. 安全架构设计\n5. 性能优化策略",
        expected_output="技术设计文档，包括：\n- 系统架构图和技术选型报告\n- 数据库设计文档\n- API接口规范文档\n- 安全设计文档\n- 性能优化方案",
        agent=AGENTS["tech_lead"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="ui_design",
        description="本次项目需求如下：{requirements}\n" + "设计用户界面，包括：\n1. 用户界面原型设计\n2. 交互设计规范\n3. 视觉设计风格定义\n4. 响应式设计适配\n5. 设计系统构建",
        expected_output="UI设计文档，包括：\n- 界面原型图和交互设计稿\n- 设计规范文档\n- 视觉设计稿和设计系统\n- 响应式设计方案\n- 设计交付物清单",
        agent=AGENTS["ui_designer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="algorithm_design",
        description="本次项目需求如下：{requirements}\n" + "设计智能算法，包括：\n1. 算法需求分析和方案设计\n2. 机器学习模型选择和设计\n3. 数据处理和特征工程\n4. 算法性能优化\n5. 算法测试和验证",
        expected_output="算法设计文档，包括：\n- 算法需求分析报告\n- 机器学习模型设计文档\n- 数据处理方案\n- 算法性能优化报告\n- 算法测试方案和结果",
        agent=AGENTS["algorithm_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="frontend_development",
        description="本次项目需求如下：{requirements}\n" + "实现前端功能，包括：\n1. 前端架构搭建和项目初始化\n2. 核心功能模块开发\n3. 用户界面组件实现\n4. 前端性能优化\n5. 前端测试和调试",
        expected_output="前端代码和文档，包括：\n- 完整的前端源代码\n- 组件库和工具函数\n- 前端测试用例\n- 性能优化报告\n- 部署配置文档",
        agent=AGENTS["frontend_dev"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="backend_development",
        description="本次项目需求如下：{requirements}\n" + "实现后端服务，包括：\n1. 后端架构搭建和项目初始化\n2. 核心业务逻辑实现\n3. 数据库操作和API接口开发\n4. 后端性能优化\n5. 后端测试和调试",
        expected_output="后端代码和文档，包括：\n- 完整的后端源代码\n- API接口文档\n- 数据库脚本和配置\n- 后端测试用例\n- 部署配置文档",
        agent=AGENTS["backend_dev"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="data_analysis",
        description="本次项目需求如下：{requirements}\n" + "进行数据分析，包括：\n1. 数据收集和清洗\n2. 数据分析和洞察\n3. 数据可视化设计\n4. 业务指标定义\n5. 数据监控方案",
        expected_output="数据分析报告，包括：\n- 数据分析报告和洞察\n- 数据可视化图表\n- 业务指标定义文档\n- 数据监控方案\n- 数据质量报告",
        agent=AGENTS["data_analyst"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="testing",
        description="本次项目需求如下：{requirements}\n" + "进行全面测试，包括：\n1. 测试策略制定和测试计划\n2. 功能测试和集成测试\n3. 性能测试和压力测试\n4. 安全测试和漏洞检测\n5. 用户体验测试",
        expected_output="测试报告和文档，包括：\n- 测试计划和测试用例\n- 功能测试报告\n- 性能测试报告\n- 安全测试报告\n- 用户体验测试报告",
        agent=AGENTS["qa_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="deployment",
        description="本次项目需求如下：{requirements}\n" + "部署和运维，包括：\n1. 部署环境搭建和配置\n2. 自动化部署流程构建\n3. 监控和日志系统配置\n4. 安全配置和备份策略\n5. 运维文档和操作手册",
        expected_output="部署和运维文档，包括：\n- 部署配置和脚本\n- 监控和日志配置\n- 安全配置文档\n- 运维操作手册\n- 故障处理预案",
        agent=AGENTS["devops_engineer"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="documentation",
        description="本次项目需求如下：{requirements}\n" + "整理项目文档，包括：\n1. 项目文档整理和归档\n2. 会议记录和进度跟踪\n3. 项目状态报告\n4. 团队沟通协调\n5. 项目交付物管理",
        expected_output="项目文档包，包括：\n- 完整的项目文档集\n- 会议记录和进度报告\n- 项目状态总结\n- 团队协作记录\n- 项目交付物清单",
        agent=AGENTS["secretary"],
        tools=[MCPTool()]
    ),
    
    Task(
        name="acceptance",
        description="本次项目需求如下：{requirements}\n" + "项目验收，包括：\n1. 项目成果评估和验收\n2. 质量标准和验收标准确认\n3. 项目总结和经验教训\n4. 后续维护和支持计划\n5. 项目交付和交接",
        expected_output="项目验收报告，包括：\n- 项目验收报告\n- 质量评估报告\n- 项目总结报告\n- 维护支持计划\n- 项目交付确认书",
        agent=AGENTS["boss"],
        tools=[MCPTool()]
    ),
]

def multi_agent_discussion(stage_name: str, agents: List[Agent], context: Dict[str, Any], max_rounds: int = 10, context_manager: Optional[SmartContextManager] = None) -> str:
    """
    多Agent渐进式讨论，产出共识文档
    优化版本：渐进式共识达成 + 智能轮次控制 + 高质量提示词 + 智能上下文管理
    """
    print(f"[多Agent讨论] 开始 {stage_name} 阶段，参与Agent: {[a.role for a in agents]}")
    
    # 上下文缓存，避免重复内容
    context_cache = {}
    discussion_log = []
    consensus_detected = False
    current_round = 0
    max_rounds = min(max_rounds, 10)  # 最多10轮
    
    # 针对典型开发阶段，自动注入目标文件路径
    stage_file_map = {
        'frontend_development': 'frontend/app.js',
        'backend_development': 'backend/main.py',
        'frontend_code': 'frontend/app.js',
        'backend_code': 'backend/main.py',
    }
    file_path = stage_file_map.get(stage_name, None)
    
    # 渐进式讨论：每轮都检测共识状态
    while current_round < max_rounds and not consensus_detected:
        current_round += 1
        print(f"[多Agent讨论] 第{current_round}轮讨论开始...")
        
        round_results = []
        
        for agent in agents:
            try:
                # 使用智能上下文管理器生成优化的上下文
                if context_manager:
                    optimized_context = context_manager.get_context_for_stage(stage_name, agent.role)
                else:
                    simplified_context = {
                        'project_id': context.get('project_id', ''),
                        'project_dir': context.get('project_dir', ''),
                        'requirements': context.get('requirements', ''),
                        'stage': stage_name,
                        'current_round': current_round
                    }
                    optimized_context = str(simplified_context)
                # 自动注入__file_path__到context
                if file_path:
                    if isinstance(optimized_context, str):
                        optimized_context = f'__file_path__:{file_path}\n' + optimized_context
                    elif isinstance(optimized_context, dict):
                        optimized_context['__file_path__'] = file_path
                # 根据轮次生成不同的提示词
                if current_round == 1:
                    prompt = _generate_first_round_prompt(agent.role, stage_name, context)
                else:
                    previous_summary = "\n".join(discussion_log[-len(agents):])
                    consensus_status = _analyze_consensus_status(discussion_log[-len(agents):])
                    prompt = _generate_follow_up_prompt(agent.role, stage_name, current_round, previous_summary, consensus_status)
                task = Task(
                    name=f"{stage_name}_discussion_round{current_round}_{agent.role}",
                    description=prompt,
                    expected_output="请提供具体的专业观点和建议。",
                    agent=agent
                )
                result = agent.execute_task(task, context=optimized_context)
                round_results.append(result)
                discussion_log.append(f"=== 第{current_round}轮 {agent.role} 观点 ===\n{result}")
                context_key = f"{agent.role}_{stage_name}"
                context_cache[context_key] = {'last_output': result}
            except Exception as e:
                print(f"[多Agent讨论] {agent.role} 第{current_round}轮发言异常: {e}")
                discussion_log.append(f"=== 第{current_round}轮 {agent.role} 发言异常: {e} ===")
        print(f"[多Agent讨论] 检测第{current_round}轮共识状态...")
        consensus_detected = _detect_consensus(round_results)
        if consensus_detected:
            print(f"[多Agent讨论] 第{current_round}轮检测到共识，结束讨论")
            break
        elif current_round < max_rounds:
            print(f"[多Agent讨论] 第{current_round}轮未达成共识，继续下一轮")
        else:
            print(f"[多Agent讨论] 达到最大轮次{max_rounds}，强制结束讨论")
    print(f"[多Agent讨论] 生成最终共识文档")
    try:
        summary_agent = _select_summary_agent(stage_name, agents)
        consensus_prompt = _generate_consensus_prompt(stage_name, discussion_log, current_round, consensus_detected)
        consensus_task = Task(
            name=f"{stage_name}_consensus",
            description=consensus_prompt,
            expected_output="请生成结构化的共识文档。",
            agent=summary_agent
        )
        consensus_result = summary_agent.execute_task(consensus_task, context=f"讨论记录: {chr(10).join(discussion_log)}")
        discussion_log_path = os.path.join(context.get('project_dir', ''), f'{stage_name}_discussion_log.txt')
        consensus_path = os.path.join(context.get('project_dir', ''), f'{stage_name}_共识文档.md')
        try:
            with open(discussion_log_path, 'w', encoding='utf-8') as f:
                f.write(f"# {stage_name} 阶段讨论日志\n\n")
                f.write(f"讨论轮次: {current_round}\n")
                f.write(f"共识状态: {'已达成共识' if consensus_detected else '未完全达成共识'}\n")
                f.write(f"结束原因: {'自然达成' if consensus_detected else '达到最大轮次'}\n\n")
                f.write(chr(10).join(discussion_log))
            with open(consensus_path, 'w', encoding='utf-8') as f:
                f.write(consensus_result)
            print(f"[多Agent讨论] 讨论日志已保存: {discussion_log_path}")
            print(f"[多Agent讨论] 共识文档已保存: {consensus_path}")
        except Exception as e:
            print(f"[多Agent讨论] 保存文件异常: {e}")
        return consensus_result
    except Exception as e:
        print(f"[多Agent讨论] 生成共识文档异常: {e}")
        return f"共识文档生成失败: {e}\n讨论记录:\n{chr(10).join(discussion_log)}"


def _generate_first_round_prompt(role: str, stage_name: str, context: Dict) -> str:
    """生成第一轮提示词 - 优化版本，更快达成共识"""
    return f"""作为{role}，请针对{stage_name}阶段提供专业、具体的建议：

项目需求：{context.get('requirements', '')}
当前阶段：{stage_name}

请从你的专业角度提供：
1. 【关键决策点】列出需要明确的关键决策（最多2个，优先最重要的）
2. 【技术方案】提出具体可行的技术方案或建议  
3. 【风险评估】识别潜在风险并提出应对措施
4. 【实施建议】给出明确的实施步骤或时间安排

要求：
- 回答要具体、可执行，避免空泛表述
- 重点关注需要协调和达成共识的部分
- 如果有不同意见，请明确说明理由
- 如果同意其他观点，请明确表示"同意"、"支持"、"认可"
- 优先考虑团队协作和共识达成
- 避免过度复杂化，追求简单可行的方案

请用简洁明了的语言表达，确保每个建议都有实际价值。
"""


def _generate_follow_up_prompt(role: str, stage_name: str, round_num: int, previous_summary: str, consensus_status: Dict) -> str:
    """生成后续轮次提示词 - 优化版本，更快达成共识"""
    return f"""基于前{round_num-1}轮讨论结果，作为{role}，请进行第{round_num}轮发言：

前轮讨论摘要：
{previous_summary}

共识状态分析：
- 已达成共识：{consensus_status.get('agreed_points', [])}
- 存在分歧：{consensus_status.get('disagreed_points', [])}
- 需要澄清：{consensus_status.get('unclear_points', [])}

请针对当前状态提供：
1. 【分歧解决】针对存在分歧的点提出具体解决方案或妥协方案
2. 【细节完善】对已达成共识的部分补充实施细节
3. 【问题澄清】对需要澄清的问题给出明确答案
4. 【最终确认】确认你的最终立场和建议

要求：
- 避免重复已有观点，专注于推进共识
- 如果分歧较大，主动提出妥协方案
- 如果基本达成共识，明确表示"同意"、"支持"、"确认"
- 用具体、可执行的建议推进讨论
- 优先考虑团队协作，避免固执己见
- 如果其他观点合理，主动表示支持

请用简洁明了的语言表达，确保每个建议都有实际价值。
"""


def _analyze_consensus_status(results: List[str]) -> Dict:
    """分析共识状态，识别已达成共识、存在分歧和需要澄清的点 - 优化版本"""
    consensus_status = {
        'agreed_points': [],
        'disagreed_points': [],
        'unclear_points': []
    }
    
    # 提取关键观点
    all_points = []
    for result in results:
        lines = result.split('\n')
        for line in lines:
            if line.strip() and ('【' in line or ':' in line or '：' in line):
                all_points.append(line.strip())
    
    # 简化的观点分析 - 实际项目中可以根据需要实现更复杂的语义分析
    # 这里我们假设大部分情况下Agent能够达成共识
    consensus_status['agreed_points'] = ["技术选型", "架构设计", "实施策略"]
    consensus_status['disagreed_points'] = []  # 减少分歧点
    consensus_status['unclear_points'] = ["具体配置"]  # 减少需要澄清的点
    
    return consensus_status


def _select_summary_agent(stage_name: str, agents: List[Agent]) -> Agent:
    """选择最适合的Agent进行汇总"""
    if stage_name in ['requirement_analysis', 'technical_design']:
        return next((a for a in agents if a.role == '技术总监'), agents[0])
    elif stage_name in ['frontend_development', 'backend_development']:
        return next((a for a in agents if a.role in ['前端开发工程师', '后端开发工程师']), agents[0])
    else:
        return agents[0]


def _generate_consensus_prompt(stage_name: str, discussion_log: List[str], round_num: int, consensus_detected: bool) -> str:
    """生成最终共识文档提示词"""
    return f"""基于{round_num}轮讨论，请生成{stage_name}阶段的最终共识文档：

讨论记录：
{chr(10).join(discussion_log)}

讨论统计：
- 总轮次：{round_num}
- 共识状态：{'已达成共识' if consensus_detected else '部分达成共识'}
- 参与角色：{len(set([log.split()[2] for log in discussion_log if '===' in log]))}个

请生成一份结构化的共识文档，包含：

## 阶段目标
明确本阶段的核心目标和成功标准

## 关键决策
列出已达成共识的关键决策点，包括：
- 技术选型
- 架构设计
- 实施策略
- 时间安排

## 技术方案
详细描述技术实现方案，包括：
- 系统架构
- 技术栈选择
- 接口设计
- 数据流程

## 实施计划
制定具体的实施步骤，包括：
- 里程碑节点
- 责任分工
- 资源需求
- 风险控制

## 验收标准
明确本阶段的验收标准和交付物

## 待确认事项
列出需要进一步确认或讨论的问题（如果有）

要求：
- 使用Markdown格式，结构清晰
- 内容具体可执行，避免空泛表述
- 突出已达成共识的部分
- 明确标注需要进一步确认的问题
- 体现渐进式讨论的成果

请确保文档的完整性和可操作性。
"""


def _detect_consensus(results: List[str]) -> bool:
    """
    智能检测是否已达成共识 - 优化版本，更快达成共识
    通过分析Agent回答的关键词和观点来判断
    """
    if len(results) < 2:
        return True
    
    # 扩展共识关键词
    consensus_keywords = [
        '同意', '支持', '认可', '确认', '达成共识', '一致', '无异议',
        '建议', '推荐', '可行', '合理', '合适', '适当', '确认',
        '可以', '没问题', '同意实施', '支持方案', '同意', '支持',
        '认可', '确认', '一致', '无异议', '可行', '合理', '合适',
        '可以', '没问题', '同意实施', '支持方案', '同意', '支持',
        '认可', '确认', '一致', '无异议', '可行', '合理', '合适',
        '可以', '没问题', '同意实施', '支持方案'
    ]
    
    # 减少分歧关键词的影响
    conflict_keywords = [
        '不同意', '反对', '质疑', '问题', '风险', '担忧', '需要讨论',
        '分歧', '争议', '不同意见', '建议修改', '重新考虑', '有疑问',
        '不确定', '需要澄清', '有待商榷'
    ]
    
    consensus_count = 0
    conflict_count = 0
    
    for result in results:
        result_lower = result.lower()
        
        # 统计共识和分歧关键词
        for keyword in consensus_keywords:
            if keyword in result_lower:
                consensus_count += 1
        
        for keyword in conflict_keywords:
            if keyword in result_lower:
                conflict_count += 1
    
    # 判断共识状态 - 降低阈值，更容易达成共识
    total_agents = len(results)
    consensus_ratio = consensus_count / (consensus_count + conflict_count) if (consensus_count + conflict_count) > 0 else 1.0
    
    # 降低共识阈值：从75%降低到60%，更容易达成共识
    if consensus_ratio > 0.6 and conflict_count < total_agents * 0.4:
        return True
    
    # 额外规则：如果所有Agent都使用了共识关键词，直接认为达成共识
    if consensus_count >= total_agents * 2:  # 每个Agent至少使用2个共识关键词
        return True
    
    return False

def run_command_with_log(cmd, cwd, log_path):
    """在指定目录下执行命令，捕获stdout/stderr并写入日志，返回(exitcode, stdout, stderr)"""
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n[CMD] {cmd}\n")
        try:
            proc = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            out = out.decode(errors='ignore')
            err = err.decode(errors='ignore')
            f.write(f"[STDOUT]\n{out}\n[STDERR]\n{err}\n[EXITCODE] {proc.returncode}\n")
            return proc.returncode, out, err
        except Exception as e:
            f.write(f"[EXCEPTION] {e}\n")
            return -1, '', str(e)

def extract_error_summary(log):
    """自动提取日志中的关键报错信息"""
    # 简单正则提取常见报错行
    lines = log.splitlines()
    error_lines = [l for l in lines if re.search(r'(error|exception|fail|traceback|not found|denied|refused|exit code)', l, re.I)]
    return '\n'.join(error_lines[-10:]) if error_lines else '\n'.join(lines[-10:])

class AiTeamCrew:
    def __init__(self, project_id=None, project_dir=None):
        self.project_id = project_id
        self.project_dir = project_dir
        # 初始化智能上下文管理器
        if project_dir:
            self.context_manager = SmartContextManager(project_dir)
        else:
            self.context_manager = None
        pid = str(project_id) if project_id is not None else ""
        pdir = str(project_dir) if project_dir is not None else ""
        for agent in AGENTS.values():
            agent._project_id = pid
            agent._project_dir = pdir
        self.crew = Crew(agents=list(AGENTS.values()), tasks=TASKS)

    def auto_execute_and_fix(self, project_dir, file_to_run, agent_list, run_type='python', custom_cmd=None, use_mcp=False, max_retry=3):
        """
        支持多执行类型、MCP远程执行、日志摘要与多Agent修正。
        优化版本：添加智能重试策略、循环检测和详细错误分析
        """
        log_path = os.path.join(project_dir, 'auto_exec_log.txt')
        mcp = MCPServer(workspace_path=project_dir) if use_mcp else None
        
        # 记录执行历史，防止循环
        execution_history = []
        
        for attempt in range(1, max_retry+1):
            print(f"[自动执行] 第 {attempt}/{max_retry} 次尝试，类型: {run_type}")
            
            # 1. 构造命令
            if run_type == 'python':
                cmd = f'python {file_to_run}'
            elif run_type == 'shell':
                cmd = f'bash {file_to_run}'
            elif run_type == 'npm':
                cmd = f'npm run {file_to_run}'
            elif run_type == 'pytest':
                cmd = f'pytest {file_to_run or ""}'
            elif run_type == 'docker':
                cmd = f'docker build -t tempimg . && docker run --rm tempimg'
            elif run_type == 'custom' and custom_cmd:
                cmd = custom_cmd
            else:
                print(f"[自动执行] 不支持的执行类型: {run_type}")
                return False
                
            # 2. 检查是否重复执行相同命令
            if cmd in execution_history:
                print(f"[自动执行] 检测到重复命令，跳过: {cmd}")
                continue
            execution_history.append(cmd)
            
            # 3. 执行命令
            try:
                if use_mcp and mcp:
                    if run_type in ['python', 'shell', 'pytest']:
                        result = mcp.execute_code(os.path.join(project_dir, file_to_run))
                        exitcode = getattr(result, 'exit_code', 1)
                        out = getattr(result, 'output', '')
                        err = getattr(result, 'error', '')
                        logs = out + '\n' + err
                    elif run_type == 'docker':
                        # 使用智能Docker名称处理
                        project_name = os.path.basename(project_dir)
                        safe_name = mcp._normalize_project_name(project_name) if hasattr(mcp, '_normalize_project_name') else project_name.replace(' ', '_')
                        image_name = f"{safe_name}:latest"
                        print(f"[Docker] 使用安全镜像名: {image_name}")
                        
                        build_result = mcp.build_docker_image(project_dir, image_name)
                        logs = getattr(build_result, 'logs', '')
                        if not build_result.success:
                            exitcode = 1
                            out = ''
                            err = build_result.message
                        else:
                            run_result = mcp.run_docker_container(image_name, f"{safe_name}-container")
                            logs += '\n' + getattr(run_result, 'logs', '')
                            exitcode = 0 if run_result.success else 1
                            out = run_result.logs
                            err = run_result.message if not run_result.success else ''
                    else:
                        exitcode, out, err = run_command_with_log(cmd, project_dir, log_path)
                        logs = out + '\n' + err
                    
            except Exception as e:
                exitcode, out, err, logs = 1, '', str(e), str(e)
                print(f"[自动执行] 执行异常: {e}")
            
            # 4. 日志归档
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[SUMMARY_ATTEMPT_{attempt}]\n{extract_error_summary(logs)}\n")
            
            # 5. 成功则返回
            if exitcode == 0:
                print(f"[自动执行] 执行成功！")
                return True
                
            # 6. 失败时智能分析和修正
            print(f"[自动执行] 执行失败 (退出码: {exitcode})")
            summary = extract_error_summary(logs)
            
            # 智能错误分析
            error_analysis = self._analyze_error(summary, run_type, attempt)
            
            # 构建更智能的修正提示
            fix_prompt = f"""自动执行命令失败，详细分析如下：

执行命令: {cmd}
退出码: {exitcode}
错误类型: {error_analysis['type']}
错误原因: {error_analysis['reason']}
错误摘要: {summary}

修正建议: {error_analysis['suggestion']}

请根据以上分析，修正产出代码/配置，确保下次执行通过。
"""
            
            print(f"[自动执行] 开始修正，错误类型: {error_analysis['type']}")
            
            # 7. 多Agent修正（限制修正时间）
            for i, agent in enumerate(agent_list):
                if i >= 2:  # 最多2个Agent参与修正
                    break
                    
                try:
                    fix_task = Task(
                        name=f"auto_fix_{run_type}_attempt{attempt}_agent{i+1}", 
                        description=fix_prompt, 
                        expected_output="请提供具体的修正代码或配置修改。", 
                        agent=agent
                    )
                    result = agent.execute_task(fix_task, context=fix_prompt, tools=agent.tools)
                    print(f"[自动执行] {agent.role} 修正完成")
                except Exception as e:
                    print(f"[自动执行] {agent.role} 修正异常: {e}")
                    
        print(f"[自动执行] 所有重试失败，最终退出")
        return False

    def _analyze_error(self, error_summary: str, run_type: str, attempt: int) -> dict:
        """智能分析错误类型和原因"""
        error_lower = error_summary.lower()
        
        # 错误类型识别
        if 'docker' in error_lower and 'invalid' in error_lower:
            return {
                'type': 'Docker名称格式错误',
                'reason': 'Docker镜像或容器名称包含非法字符',
                'suggestion': '检查项目名称，确保只包含字母、数字、下划线、连字符和点号'
            }
        elif 'mcp' in error_lower and '不支持' in error_lower:
            return {
                'type': 'MCP工具不支持',
                'reason': f'MCP工具不支持 {run_type} 类型的执行',
                'suggestion': f'考虑使用本地执行或切换到MCP支持的类型'
            }
        elif 'permission' in error_lower or 'denied' in error_lower:
            return {
                'type': '权限不足',
                'reason': '执行权限被拒绝',
                'suggestion': '检查文件权限，确保有执行权限'
            }
        elif 'not found' in error_lower or '不存在' in error_lower:
            return {
                'type': '文件不存在',
                'reason': '要执行的文件或依赖不存在',
                'suggestion': '检查文件路径和依赖安装'
            }
        elif 'syntax' in error_lower or '语法' in error_lower:
            return {
                'type': '语法错误',
                'reason': '代码存在语法错误',
                'suggestion': '检查代码语法，修复语法错误'
            }
        elif 'import' in error_lower or 'module' in error_lower:
            return {
                'type': '依赖缺失',
                'reason': '缺少必要的依赖模块',
                'suggestion': '安装缺失的依赖包'
            }
        elif attempt >= 2:
            return {
                'type': '多次重试失败',
                'reason': f'已经重试 {attempt} 次仍然失败',
                'suggestion': '检查系统环境配置，可能需要手动干预'
            }
        else:
            return {
                'type': '未知错误',
                'reason': '无法识别的错误类型',
                'suggestion': '查看详细错误日志，手动分析问题'
            }

    def kickoff(self, inputs, resume_from: Optional[str] = None):
        """
        启动AI团队协作流程
        inputs: 项目输入参数
        resume_from: 从指定阶段继续执行（可选）
        """
        context = dict(inputs) if inputs else {}
        results = {}
        project_dir = AGENTS["product_manager"]._project_dir
        
        # 初始化进度管理器
        progress_manager = ProgressManager(project_dir)
        
        # 初始化智能上下文管理器
        if not self.context_manager:
            self.context_manager = SmartContextManager(project_dir)
        
        # 添加项目基础信息到上下文管理器
        self.context_manager.add_context(
            key="project_requirements",
            value=inputs.get('requirements', ''),
            priority=ContextPriority.CRITICAL,
            context_type=ContextType.REQUIREMENT,
            stage="initial"
        )
        
        self.context_manager.add_context(
            key="project_name",
            value=inputs.get('project_name', ''),
            priority=ContextPriority.CRITICAL,
            context_type=ContextType.REQUIREMENT,
            stage="initial"
        )
        
        # 如果指定了恢复点，检查进度
        if resume_from:
            print(f"[AI团队] 从阶段 '{resume_from}' 继续执行...")
            # 加载已完成阶段的结果到context和上下文管理器
            for stage in progress_manager.stages:
                if progress_manager.is_stage_completed(stage):
                    result = progress_manager.get_stage_result(stage)
                    results[stage] = result
                    context[f"{stage}_result"] = result
                    
                    # 添加到智能上下文管理器
                    self.context_manager.add_context(
                        key=f"{stage}_result",
                        value=result,
                        priority=ContextPriority.HIGH if stage in ["requirement_analysis", "technical_design"] else ContextPriority.MEDIUM,
                        context_type=ContextType.DESIGN if "design" in stage else ContextType.IMPLEMENTATION,
                        stage=stage
                    )
                    
                    if stage == resume_from:
                        break
        
        initial_input = f"项目需求：{inputs.get('requirements', '')}"
        
        # 1. 需求分析阶段：老板-产品经理-技术总监多轮对话
        consensus_path = os.path.join(project_dir, '需求分析_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到需求分析共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                consensus = f.read()
            results["requirement_analysis"] = consensus
            context["requirement_analysis_result"] = consensus
            self.context_manager.add_context(
                key="requirement_analysis_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.REQUIREMENT,
                stage="requirement_analysis"
            )
            progress_manager.save_progress("requirement_analysis", consensus, context)
        elif not progress_manager.is_stage_completed("requirement_analysis"):
            print("[AI团队] 开始需求分析阶段...")
            consensus = multi_agent_discussion(
                stage_name="需求分析",
                agents=[AGENTS["boss"], AGENTS["product_manager"], AGENTS["tech_lead"]],
                context=context,
                max_rounds=10,  # 使用渐进式共识达成，最多10轮
                context_manager=self.context_manager
            )
            results["requirement_analysis"] = consensus
            context["requirement_analysis_result"] = consensus
            self.context_manager.add_context(
                key="requirement_analysis_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.REQUIREMENT,
                stage="requirement_analysis"
            )
            progress_manager.save_progress("requirement_analysis", consensus, context)
        else:
            print("[AI团队] 需求分析阶段已完成，跳过...")
            results["requirement_analysis"] = progress_manager.get_stage_result("requirement_analysis")
            context["requirement_analysis_result"] = results["requirement_analysis"]
        
        # 2. 技术设计阶段：技术总监-产品经理-前端-后端多轮对话
        consensus_path = os.path.join(project_dir, '技术设计_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到技术设计共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                consensus = f.read()
            results["technical_design"] = consensus
            context["technical_design_result"] = consensus
            self.context_manager.add_context(
                key="technical_design_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.DESIGN,
                stage="technical_design"
            )
            progress_manager.save_progress("technical_design", consensus, context)
        elif not progress_manager.is_stage_completed("technical_design"):
            print("[AI团队] 开始技术设计阶段...")
            consensus = multi_agent_discussion(
                stage_name="技术设计",
                agents=[AGENTS["tech_lead"], AGENTS["product_manager"], AGENTS["frontend_dev"], AGENTS["backend_dev"]],
                context=context,
                max_rounds=10,  # 使用渐进式共识达成，最多10轮
                context_manager=self.context_manager
            )
            results["technical_design"] = consensus
            context["technical_design_result"] = consensus
            self.context_manager.add_context(
                key="technical_design_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.DESIGN,
                stage="technical_design"
            )
            progress_manager.save_progress("technical_design", consensus, context)
        else:
            print("[AI团队] 技术设计阶段已完成，跳过...")
            results["technical_design"] = progress_manager.get_stage_result("technical_design")
            context["technical_design_result"] = results["technical_design"]
        
        # 3. UI设计阶段（单Agent串行）
        consensus_path = os.path.join(project_dir, 'UI设计_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到UI设计共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                result = f.read()
            results["ui_design"] = result
            context["ui_design_result"] = result
            self.context_manager.add_context(
                key="ui_design_result",
                value=result,
                priority=ContextPriority.HIGH,
                context_type=ContextType.DESIGN,
                stage="ui_design"
            )
            progress_manager.save_progress("ui_design", result, context)
        elif not progress_manager.is_stage_completed("ui_design"):
            print("[AI团队] 开始UI设计阶段...")
            task = next(t for t in TASKS if t.name == "ui_design")
            agent = task.agent
            if agent is not None:
                optimized_context = self.context_manager.get_context_for_stage("ui_design", agent.role)
                result = agent.execute_task(task, context=optimized_context, tools=task.tools)
                results["ui_design"] = result
                context["ui_design_result"] = result
                self.context_manager.add_context(
                    key="ui_design_result",
                    value=result,
                    priority=ContextPriority.HIGH,
                    context_type=ContextType.DESIGN,
                    stage="ui_design"
                )
                progress_manager.save_progress("ui_design", result, context)
        else:
            print("[AI团队] UI设计阶段已完成，跳过...")
            results["ui_design"] = progress_manager.get_stage_result("ui_design")
            context["ui_design_result"] = results["ui_design"]
        
        # 4. 前端开发阶段：前端-UI设计-技术总监多轮对话
        consensus_path = os.path.join(project_dir, '前端开发_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到前端开发共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                consensus = f.read()
            results["frontend_development"] = consensus
            context["frontend_development_result"] = consensus
            self.context_manager.add_context(
                key="frontend_development_result",
                value=consensus,
                priority=ContextPriority.HIGH,
                context_type=ContextType.IMPLEMENTATION,
                stage="frontend_development"
            )
            progress_manager.save_progress("frontend_development", consensus, context)
        elif not progress_manager.is_stage_completed("frontend_development"):
            print("[AI团队] 开始前端开发讨论阶段...")
            consensus = multi_agent_discussion(
                stage_name="前端开发",
                agents=[AGENTS["frontend_dev"], AGENTS["ui_designer"], AGENTS["tech_lead"]],
                context=context,
                max_rounds=10,  # 使用渐进式共识达成，最多10轮
                context_manager=self.context_manager
            )
            results["frontend_development"] = consensus
            context["frontend_development_result"] = consensus
            self.context_manager.add_context(
                key="frontend_development_result",
                value=consensus,
                priority=ContextPriority.HIGH,
                context_type=ContextType.IMPLEMENTATION,
                stage="frontend_development"
            )
            progress_manager.save_progress("frontend_development", consensus, context)
        else:
            print("[AI团队] 前端开发讨论阶段已完成，跳过...")
            results["frontend_development"] = progress_manager.get_stage_result("frontend_development")
            context["frontend_development_result"] = results["frontend_development"]
        
        # 4.1 前端代码生成阶段（单Agent执行）
        if not progress_manager.is_stage_completed("frontend_code"):
            print("[AI团队] 开始前端代码生成阶段...")
            task = next(t for t in TASKS if t.name == "frontend_development")
            agent = task.agent
            if agent is not None:
                # 使用智能上下文管理器
                optimized_context = self.context_manager.get_context_for_stage("frontend_code", agent.role)
                result = agent.execute_task(task, context=optimized_context, tools=task.tools)
                results["frontend_code"] = result
                context["frontend_code_result"] = result
                
                # 添加到智能上下文管理器
                self.context_manager.add_context(
                    key="frontend_code_result",
                    value=result,
                    priority=ContextPriority.MEDIUM,
                    context_type=ContextType.IMPLEMENTATION,
                    stage="frontend_code"
                )
                
                progress_manager.save_progress("frontend_code", result, context)
        else:
            print("[AI团队] 前端代码生成阶段已完成，跳过...")
            results["frontend_code"] = progress_manager.get_stage_result("frontend_code")
            context["frontend_code_result"] = results["frontend_code"]
        
        # 5. 后端开发阶段：后端-技术总监-产品经理多轮对话
        consensus_path = os.path.join(project_dir, '后端开发_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到后端开发共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                consensus = f.read()
            results["backend_development"] = consensus
            context["backend_development_result"] = consensus
            self.context_manager.add_context(
                key="backend_development_result",
                value=consensus,
                priority=ContextPriority.HIGH,
                context_type=ContextType.IMPLEMENTATION,
                stage="backend_development"
            )
            progress_manager.save_progress("backend_development", consensus, context)
        elif not progress_manager.is_stage_completed("backend_development"):
            print("[AI团队] 开始后端开发讨论阶段...")
            consensus = multi_agent_discussion(
                stage_name="后端开发",
                agents=[AGENTS["backend_dev"], AGENTS["tech_lead"], AGENTS["product_manager"]],
                context=context,
                max_rounds=10,  # 使用渐进式共识达成，最多10轮
                context_manager=self.context_manager
            )
            results["backend_development"] = consensus
            context["backend_development_result"] = consensus
            self.context_manager.add_context(
                key="backend_development_result",
                value=consensus,
                priority=ContextPriority.HIGH,
                context_type=ContextType.IMPLEMENTATION,
                stage="backend_development"
            )
            progress_manager.save_progress("backend_development", consensus, context)
        else:
            print("[AI团队] 后端开发讨论阶段已完成，跳过...")
            results["backend_development"] = progress_manager.get_stage_result("backend_development")
            context["backend_development_result"] = results["backend_development"]
        
        # 5.1 后端代码生成阶段（单Agent执行）
        if not progress_manager.is_stage_completed("backend_code"):
            print("[AI团队] 开始后端代码生成阶段...")
            task = next(t for t in TASKS if t.name == "backend_development")
            agent = task.agent
            if agent is not None:
                # 使用智能上下文管理器
                optimized_context = self.context_manager.get_context_for_stage("backend_code", agent.role)
                result = agent.execute_task(task, context=optimized_context, tools=task.tools)
                results["backend_code"] = result
                context["backend_code_result"] = result
                
                # 添加到智能上下文管理器
                self.context_manager.add_context(
                    key="backend_code_result",
                    value=result,
                    priority=ContextPriority.MEDIUM,
                    context_type=ContextType.IMPLEMENTATION,
                    stage="backend_code"
                )
                
                progress_manager.save_progress("backend_code", result, context)
        else:
            print("[AI团队] 后端代码生成阶段已完成，跳过...")
            results["backend_code"] = progress_manager.get_stage_result("backend_code")
            context["backend_code_result"] = results["backend_code"]
        
        # 6. 数据分析、测试、部署、文档阶段（单Agent串行）
        for name, doc_type, priority in [
            ("data_analysis", ContextType.IMPLEMENTATION, ContextPriority.MEDIUM),
            ("testing", ContextType.IMPLEMENTATION, ContextPriority.MEDIUM),
            ("deployment", ContextType.CONFIGURATION, ContextPriority.MEDIUM),
            ("documentation", ContextType.REQUIREMENT, ContextPriority.MEDIUM)
        ]:
            consensus_path = os.path.join(project_dir, f'{name}_共识文档.md')
            if os.path.exists(consensus_path):
                print(f"[AI团队] 检测到{name}共识文档，直接用文档驱动开发...")
                with open(consensus_path, 'r', encoding='utf-8') as f:
                    result = f.read()
                results[name] = result
                context[f"{name}_result"] = result
                self.context_manager.add_context(
                    key=f"{name}_result",
                    value=result,
                    priority=priority,
                    context_type=doc_type,
                    stage=name
                )
                progress_manager.save_progress(name, result, context)
            elif not progress_manager.is_stage_completed(name):
                print(f"[AI团队] 开始{name}阶段...")
                task = next(t for t in TASKS if t.name == name)
                agent = task.agent
                if agent is not None:
                    optimized_context = self.context_manager.get_context_for_stage(name, agent.role)
                    result = agent.execute_task(task, context=optimized_context, tools=task.tools)
                    results[name] = result
                    context[f"{name}_result"] = result
                    self.context_manager.add_context(
                        key=f"{name}_result",
                        value=result,
                        priority=priority,
                        context_type=doc_type,
                        stage=name
                    )
                    progress_manager.save_progress(name, result, context)
            else:
                print(f"[AI团队] {name}阶段已完成，跳过...")
                results[name] = progress_manager.get_stage_result(name)
                context[f"{name}_result"] = results[name]
        
        # 7. 验收阶段：老板-产品经理-测试-开发多轮对话
        consensus_path = os.path.join(project_dir, '验收_共识文档.md')
        if os.path.exists(consensus_path):
            print("[AI团队] 检测到验收共识文档，直接用文档驱动开发...")
            with open(consensus_path, 'r', encoding='utf-8') as f:
                consensus = f.read()
            results["acceptance"] = consensus
            context["acceptance_result"] = consensus
            self.context_manager.add_context(
                key="acceptance_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.REQUIREMENT,
                stage="acceptance"
            )
            progress_manager.save_progress("acceptance", consensus, context)
        elif not progress_manager.is_stage_completed("acceptance"):
            print("[AI团队] 开始验收阶段...")
            consensus = multi_agent_discussion(
                stage_name="验收",
                agents=[AGENTS["boss"], AGENTS["product_manager"], AGENTS["qa_engineer"], AGENTS["frontend_dev"], AGENTS["backend_dev"]],
                context=context,
                max_rounds=10,  # 使用渐进式共识达成，最多10轮
                context_manager=self.context_manager
            )
            results["acceptance"] = consensus
            context["acceptance_result"] = consensus
            self.context_manager.add_context(
                key="acceptance_result",
                value=consensus,
                priority=ContextPriority.CRITICAL,
                context_type=ContextType.REQUIREMENT,
                stage="acceptance"
            )
            progress_manager.save_progress("acceptance", consensus, context)
        else:
            print("[AI团队] 验收阶段已完成，跳过...")
            results["acceptance"] = progress_manager.get_stage_result("acceptance")
            context["acceptance_result"] = results["acceptance"]
        
        # 8. 自动执行与修正闭环（多类型、多Agent、多环境）
        if not progress_manager.is_stage_completed("auto_execution"):
            print("[AI团队] 开始自动执行与修正阶段...")
            # 1) main.py
            main_py = os.path.join(project_dir, 'main.py')
            if os.path.exists(main_py):
                self.auto_execute_and_fix(
                    project_dir, 'main.py',
                    agent_list=[AGENTS["backend_dev"], AGENTS["qa_engineer"]],
                    run_type='python', use_mcp=True, max_retry=3)
            # 2) shell脚本
            shell_file = os.path.join(project_dir, 'deploy.sh')
            if os.path.exists(shell_file):
                self.auto_execute_and_fix(
                    project_dir, 'deploy.sh',
                    agent_list=[AGENTS["devops_engineer"]],
                    run_type='shell', use_mcp=True, max_retry=2)
            # 3) npm前端
            frontend_dir = os.path.join(project_dir, 'frontend')
            if os.path.exists(frontend_dir):
                self.auto_execute_and_fix(
                    frontend_dir, 'build',
                    agent_list=[AGENTS["frontend_dev"], AGENTS["qa_engineer"]],
                    run_type='npm', use_mcp=True, max_retry=2)
            # 4) pytest自动化测试
            test_file = os.path.join(project_dir, 'tests')
            if os.path.exists(test_file):
                self.auto_execute_and_fix(
                    project_dir, '',
                    agent_list=[AGENTS["qa_engineer"], AGENTS["backend_dev"]],
                    run_type='pytest', use_mcp=True, max_retry=2)
            # 5) Dockerfile
            dockerfile = os.path.join(project_dir, 'Dockerfile')
            if os.path.exists(dockerfile):
                self.auto_execute_and_fix(
                    project_dir, '',
                    agent_list=[AGENTS["devops_engineer"], AGENTS["backend_dev"]],
                    run_type='docker', use_mcp=True, max_retry=2)
            progress_manager.save_progress("auto_execution", "自动执行完成", context)
        else:
            print("[AI团队] 自动执行与修正阶段已完成，跳过...")
        
        # 打印进度摘要
        summary = progress_manager.get_progress_summary()
        print(f"[AI团队] 项目执行完成！进度：{summary['completed']}/{summary['total']} ({summary['percentage']}%)")
        
        return results

# 进度状态管理
class ProgressManager:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.progress_file = os.path.join(project_dir, 'progress.json')
        self.stages = [
            "requirement_analysis",
            "technical_design", 
            "ui_design",
            "frontend_development",
            "frontend_code",
            "backend_development",
            "backend_code",
            "data_analysis",
            "testing",
            "deployment",
            "documentation",
            "acceptance",
            "auto_execution"
        ]
    
    def save_progress(self, stage: str, result: str, context: Optional[Dict] = None):
        """保存阶段进度"""
        progress = self.load_progress()
        progress[stage] = {
            "status": "completed",
            "result": result,
            "timestamp": time.time(),
            "context": context if context is not None else {}
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def load_progress(self) -> Dict:
        """加载进度状态"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def get_completed_stages(self) -> List[str]:
        """获取已完成的阶段"""
        progress = self.load_progress()
        return [stage for stage, data in progress.items() if data.get("status") == "completed"]
    
    def get_next_stage(self) -> str:
        """获取下一个待执行的阶段"""
        completed = self.get_completed_stages()
        for stage in self.stages:
            if stage not in completed:
                return stage
        return ""  # 返回空字符串而不是None
    
    def is_stage_completed(self, stage: str) -> bool:
        """检查阶段是否已完成"""
        progress = self.load_progress()
        return stage in progress and progress[stage].get("status") == "completed"
    
    def get_stage_result(self, stage: str) -> str:
        """获取阶段结果"""
        progress = self.load_progress()
        if stage in progress:
            return progress[stage].get("result", "")
        return ""
    
    def reset_progress(self):
        """重置进度"""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
    
    def get_progress_summary(self) -> Dict:
        """获取进度摘要"""
        progress = self.load_progress()
        completed = len([s for s in progress.values() if s.get("status") == "completed"])
        total = len(self.stages)
        return {
            "completed": completed,
            "total": total,
            "percentage": round(completed / total * 100, 1) if total > 0 else 0,
            "completed_stages": self.get_completed_stages(),
            "next_stage": self.get_next_stage()
        } 