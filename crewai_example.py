from crewai import Agent, Task, Crew, Process
from langchain.tools import DuckDuckGoSearchRun

# 创建工具
search_tool = DuckDuckGoSearchRun()

# 创建Agent（角色）
researcher = Agent(
    role='研究员',
    goal='收集和分析相关信息',
    backstory='你是一个专业的研究员，擅长收集和分析数据',
    tools=[search_tool],
    verbose=True
)

writer = Agent(
    role='写手',
    goal='基于研究结果撰写高质量内容',
    backstory='你是一个经验丰富的写手，擅长将复杂信息转化为易懂的内容',
    verbose=True
)

reviewer = Agent(
    role='审核员',
    goal='审核和优化内容质量',
    backstory='你是一个严格的审核员，确保内容准确性和可读性',
    verbose=True
)

# 创建任务
research_task = Task(
    description='研究如何提高团队工作效率的最新方法和工具',
    agent=researcher
)

writing_task = Task(
    description='基于研究结果，撰写一份关于提高团队工作效率的详细报告',
    agent=writer
)

review_task = Task(
    description='审核报告内容，确保信息准确、结构清晰、易于理解',
    agent=reviewer
)

# 创建团队
crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, writing_task, review_task],
    process=Process.sequential  # 顺序执行
)

# 执行任务
result = crew.kickoff()
print(result) 