import os
import sys
import datetime
from crewai import Crew, Agent, Task
from .crew_tools import MCPTool
from pydantic import PrivateAttr
from typing import Optional, cast, List
import subprocess
from mcp_server import MCPServer
import re

class LoggingAgent(Agent):
    _project_id: 'str' = PrivateAttr(default="")
    _project_dir: 'str' = PrivateAttr(default="")
    def __init__(self, *args, project_id: str = "", project_dir: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._project_id = project_id or ""
        self._project_dir = project_dir or ""

    def execute_task(self, task, context=None, tools=None):
        # 处理任务描述中的参数替换
        task_description = task.description
        if context and isinstance(context, dict):
            # 如果是字典格式的上下文，进行参数替换
            try:
                task_description = task_description.format(**context)
            except KeyError:
                # 如果缺少某些参数，保持原样
                pass
        elif context and isinstance(context, str):
            # 如果是字符串格式的上下文，尝试解析为字典
            try:
                import ast
                context_dict = ast.literal_eval(context)
                if isinstance(context_dict, dict):
                    task_description = task_description.format(**context_dict)
            except:
                # 解析失败，保持原样
                pass
        
        # 创建临时任务对象，替换描述
        task.prompt = lambda: task_description
        
        task_prompt = task.prompt()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        role = self.role
        task_name = getattr(task, 'name', 'unknown')
        # 控制台打印输入
        print(f"\n================ LLM调用日志 ================")
        print(f"[{now}] 角色: {role} 任务: {task_name}")
        print(f"【输入Prompt】\n{task_prompt}")
        if context:
            print(f"【上下文】\n{context}")
        sys.stdout.flush()
        # 调用原始Agent逻辑
        result = super().execute_task(task, context, tools)
        # 控制台打印输出
        print(f"【输出Result】\n{result}")
        print(f"============================================\n")
        sys.stdout.flush()
        # 日志落盘
        if self._project_dir:
            log_path = os.path.join(self._project_dir, 'llm_log.txt')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{now}] 角色: {role} 任务: {task_name}\n")
                f.write(f"【输入Prompt】\n{task_prompt}\n")
                if context:
                    f.write(f"【上下文】\n{context}\n")
                f.write(f"【输出Result】\n{result}\n")
                f.write(f"--------------------------------------------\n")
        # === 自动产出落盘机制 ===
        if self._project_dir and isinstance(self._project_dir, str) and self._project_dir.strip() != "" and task_name:
            project_dir: str = self._project_dir
            name_map = {
                'requirement_analysis': '需求分析.md',
                'technical_design': '技术设计.md',
                'ui_design': 'UI设计.md',
                'algorithm_design': '算法设计.md',
                'frontend_development': 'frontend/前端开发.md',
                'backend_development': 'backend/后端开发.md',
                'data_analysis': '数据分析报告.md',
                'testing': '测试报告.md',
                'deployment': '部署文档.md',
                'documentation': '项目文档.md',
                'acceptance': '项目验收报告.md',
            }
            out_file = name_map.get(task_name, f'{task_name}.md')
            if out_file and isinstance(out_file, str):
                out_path = os.path.join(project_dir, out_file)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                if 'Dockerfile' in result:
                    dockerfile_path = os.path.join(project_dir, 'Dockerfile')
                    docker_content = self._extract_block(result, 'Dockerfile')
                    if docker_content:
                        with open(dockerfile_path, 'w', encoding='utf-8') as f:
                            f.write(docker_content.strip() + '\n')
                self._extract_and_write_code_blocks(result)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(result.strip() + '\n')
        return result

    def _extract_block(self, text, block_name):
        """提取如```Dockerfile ...```或```block_name ...```的内容"""
        import re
        pattern = rf'```{block_name}([\s\S]*?)```'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_and_write_code_blocks(self, text):
        """自动提取并写入代码块到对应文件"""
        import re
        code_blocks = re.findall(r'```(\w+)?\n([\s\S]*?)```', text)
        for lang, code in code_blocks:
            ext_map = {
                'python': '.py', 'js': '.js', 'javascript': '.js', 'ts': '.ts', 'java': '.java',
                'go': '.go', 'c': '.c', 'cpp': '.cpp', 'html': '.html', 'css': '.css',
                'sh': '.sh', 'bash': '.sh', 'Dockerfile': 'Dockerfile',
            }
            ext = ext_map.get(lang.lower(), '.txt') if lang else '.txt'
            # 文件名自动递增防止覆盖
            base = lang if lang else 'code'
            idx = 1
            while True:
                fname = f'{base}_{idx}{ext}' if ext != 'Dockerfile' else 'Dockerfile'
                fpath = os.path.join(self._project_dir, fname)
                if not os.path.exists(fpath):
                    break
                idx += 1
            # Dockerfile 特殊处理
            if ext == 'Dockerfile':
                fpath = os.path.join(self._project_dir, 'Dockerfile')
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(code.strip() + '\n')

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

def multi_agent_discussion(stage_name: str, agents: List[Agent], initial_input: str, project_dir: str, rounds: int = 3) -> str:
    """
    多角色多轮对话，最终由最后一个Agent汇总共识。
    :param stage_name: 阶段名（如需求分析）
    :param agents: 参与角色列表
    :param initial_input: 初始输入（如需求）
    :param project_dir: 产出目录
    :param rounds: 对话轮数
    :return: 共识产出
    """
    context = initial_input
    discussion_log = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for r in range(rounds):
        for agent in agents:
            prompt = f"【阶段】{stage_name} 第{r+1}轮\n【当前上下文】\n{context}\n请以你的身份补充、提问、质疑或确认。"
            result = agent.execute_task(Task(name=f"{stage_name}_discussion_round{r+1}_{agent.role}", description=prompt, expected_output="请补充你的观点/建议/问题/确认。", agent=agent), context=context)
            discussion_log.append(f"[{now}] {agent.role} 第{r+1}轮: {result}")
            context += f"\n{agent.role}：{result}"
    # 最后由最后一个Agent汇总共识
    summary_prompt = f"【阶段】{stage_name}共识汇总\n【全部对话】\n{context}\n请以你的身份对本阶段进行总结，输出最终共识文档。"
    consensus = agents[-1].execute_task(Task(name=f"{stage_name}_consensus", description=summary_prompt, expected_output="请输出最终共识文档。", agent=agents[-1]), context=context)
    # 写入对话日志
    if project_dir:
        log_path = os.path.join(project_dir, f"{stage_name}_discussion_log.txt")
        with open(log_path, 'w', encoding='utf-8') as f:
            for line in discussion_log:
                f.write(line + '\n')
        # 共识产出也写入主产出文件
        consensus_path = os.path.join(project_dir, f"{stage_name}_共识文档.md")
        with open(consensus_path, 'w', encoding='utf-8') as f:
            f.write(consensus.strip() + '\n')
    return consensus

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
        pid = str(project_id) if project_id is not None else ""
        pdir = str(project_dir) if project_dir is not None else ""
        for agent in AGENTS.values():
            agent._project_id = pid
            agent._project_dir = pdir
        self.crew = Crew(agents=list(AGENTS.values()), tasks=TASKS)

    def auto_execute_and_fix(self, project_dir, file_to_run, agent_list, run_type='python', custom_cmd=None, use_mcp=False, max_retry=3):
        """
        支持多执行类型、MCP远程执行、日志摘要与多Agent修正。
        agent_list: 参与修正的Agent列表（如[开发, 测试, 运维]）
        run_type: python/shell/npm/pytest/docker/custom
        custom_cmd: 自定义命令
        use_mcp: 是否优先用MCP远程执行
        """
        log_path = os.path.join(project_dir, 'auto_exec_log.txt')
        mcp = MCPServer(workspace_path=project_dir) if use_mcp else None
        for attempt in range(1, max_retry+1):
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
                return False
            # 2. 执行命令
            if use_mcp and mcp:
                if run_type == 'python' or run_type == 'shell' or run_type == 'pytest':
                    result = mcp.execute_code(os.path.join(project_dir, file_to_run))
                    exitcode = getattr(result, 'exit_code', 1)
                    out = getattr(result, 'output', '')
                    err = getattr(result, 'error', '')
                    logs = out + '\n' + err
                elif run_type == 'docker':
                    image_name = f"{os.path.basename(project_dir)}:latest"
                    build_result = mcp.build_docker_image(project_dir, image_name)
                    logs = getattr(build_result, 'logs', '')
                    if not build_result.success:
                        exitcode = 1
                        out = ''
                        err = build_result.message
                    else:
                        run_result = mcp.run_docker_container(image_name, f"{os.path.basename(project_dir)}-container")
                        logs += '\n' + getattr(run_result, 'logs', '')
                        exitcode = 0 if run_result.success else 1
                        out = run_result.logs
                        err = run_result.message if not run_result.success else ''
                else:
                    # 其它类型暂不支持MCP
                    exitcode, out, err, logs = 1, '', 'MCP暂不支持该类型', 'MCP暂不支持该类型'
            else:
                exitcode, out, err = run_command_with_log(cmd, project_dir, log_path)
                logs = out + '\n' + err
            # 3. 日志归档
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[SUMMARY_ATTEMPT_{attempt}]\n{extract_error_summary(logs)}\n")
            # 4. 成功则返回
            if exitcode == 0:
                return True
            # 5. 失败时多Agent多轮修正
            summary = extract_error_summary(logs)
            fix_prompt = f"自动执行命令失败，日志摘要如下：\n{summary}\n请修正产出，确保下次执行通过。"
            for agent in agent_list:
                fix_task = Task(name=f"auto_fix_{run_type}_attempt{attempt}", description=fix_prompt, expected_output="请修正产出代码/配置。", agent=agent)
                agent.execute_task(fix_task, context=fix_prompt, tools=agent.tools)
        return False

    def kickoff(self, inputs):
        context = dict(inputs) if inputs else {}
        results = {}
        project_dir = AGENTS["product_manager"]._project_dir
        initial_input = f"项目需求：{inputs.get('requirements', '')}"
        # 1. 需求分析阶段：老板-产品经理-技术总监多轮对话
        consensus = multi_agent_discussion(
            stage_name="需求分析",
            agents=[AGENTS["boss"], AGENTS["product_manager"], AGENTS["tech_lead"]],
            initial_input=initial_input,
            project_dir=project_dir,
            rounds=3
        )
        results["requirement_analysis"] = consensus
        context["requirement_analysis_result"] = consensus
        # 2. 技术设计阶段：技术总监-产品经理-前端-后端多轮对话
        consensus = multi_agent_discussion(
            stage_name="技术设计",
            agents=[AGENTS["tech_lead"], AGENTS["product_manager"], AGENTS["frontend_dev"], AGENTS["backend_dev"]],
            initial_input=context["requirement_analysis_result"],
            project_dir=project_dir,
            rounds=3
        )
        results["technical_design"] = consensus
        context["technical_design_result"] = consensus
        # 3. UI设计阶段（单Agent串行）
        task = next(t for t in TASKS if t.name == "ui_design")
        agent = task.agent
        if agent is not None:
            context_str = str(context) if context else None
            result = agent.execute_task(task, context=context_str, tools=task.tools)
            results["ui_design"] = result
            context["ui_design_result"] = result
        # 4. 前端开发阶段：前端-UI设计-技术总监多轮对话
        consensus = multi_agent_discussion(
            stage_name="前端开发",
            agents=[AGENTS["frontend_dev"], AGENTS["ui_designer"], AGENTS["tech_lead"]],
            initial_input=context["ui_design_result"],
            project_dir=project_dir,
            rounds=2
        )
        results["frontend_development"] = consensus
        context["frontend_development_result"] = consensus
        # 5. 后端开发阶段：后端-技术总监-产品经理多轮对话
        consensus = multi_agent_discussion(
            stage_name="后端开发",
            agents=[AGENTS["backend_dev"], AGENTS["tech_lead"], AGENTS["product_manager"]],
            initial_input=context["technical_design_result"],
            project_dir=project_dir,
            rounds=2
        )
        results["backend_development"] = consensus
        context["backend_development_result"] = consensus
        # 6. 数据分析、测试、部署、文档阶段（单Agent串行）
        for name in ["data_analysis", "testing", "deployment", "documentation"]:
            task = next(t for t in TASKS if t.name == name)
            agent = task.agent
            if agent is not None:
                context_str = str(context) if context else None
                result = agent.execute_task(task, context=context_str, tools=task.tools)
                results[name] = result
                context[f"{name}_result"] = result
        # 7. 验收阶段：老板-产品经理-测试-开发多轮对话
        consensus = multi_agent_discussion(
            stage_name="验收",
            agents=[AGENTS["boss"], AGENTS["product_manager"], AGENTS["qa_engineer"], AGENTS["frontend_dev"], AGENTS["backend_dev"]],
            initial_input="\n".join([
                context.get("requirement_analysis_result", ""),
                context.get("technical_design_result", ""),
                context.get("frontend_development_result", ""),
                context.get("backend_development_result", ""),
                context.get("testing_result", "")
            ]),
            project_dir=project_dir,
            rounds=2
        )
        results["acceptance"] = consensus
        context["acceptance_result"] = consensus
        # 8. 自动执行与修正闭环（多类型、多Agent、多环境）
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
        return results 