import autogen
from typing import Dict, Any

# 配置LLM
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": "your-api-key"
    }
]

# 创建Agent
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": config_list},
    system_message="你是一个有用的AI助手，擅长分析和解决问题。"
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    llm_config={"config_list": config_list},
    system_message="你代表用户，负责提出问题和需求。"
)

# 开始对话
user_proxy.initiate_chat(
    assistant,
    message="请帮我分析一下如何提高团队的工作效率？"
) 