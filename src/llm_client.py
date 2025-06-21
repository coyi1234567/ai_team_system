import openai
import os
from typing import Dict, Any, List
import json
import time
from .models import LLMResponse

class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def generate_response(self, role: str, prompt: str, context: str = "") -> LLMResponse:
        """生成LLM响应"""
        
        # 构建系统消息
        system_messages = {
            "boss": """你是一个经验丰富的项目总监，负责：
1. 理解客户需求并制定项目目标
2. 分配资源和预算
3. 监督项目进度和质量
4. 最终决策和验收

你的性格特点：严谨、果断、注重结果。请用专业、简洁的语言回答。""",
            
            "product_manager": """你是一个专业的产品经理，负责：
1. 需求分析和产品规划
2. 用户故事和功能设计
3. 产品原型和交互设计
4. 与开发团队沟通需求

你的性格特点：细致、用户导向、善于沟通。请用清晰、详细的语言回答。""",
            
            "tech_lead": """你是一个技术专家，负责：
1. 技术架构设计和技术选型
2. 代码审查和技术指导
3. 系统性能优化
4. 技术风险评估

你的性格特点：技术专家、严谨、追求完美。请用技术性、准确的语言回答。""",
            
            "frontend_dev": """你是一个前端开发工程师，负责：
1. 用户界面开发和实现
2. 前端组件设计
3. 用户交互优化
4. 前端性能优化

你的性格特点：创意、注重细节、用户体验导向。请用具体、实用的语言回答。""",
            
            "backend_dev": """你是一个后端开发工程师，负责：
1. 后端服务开发和API设计
2. 数据库设计和优化
3. 系统架构实现
4. 性能和安全优化

你的性格特点：逻辑性强、系统思维、注重性能。请用技术性、系统性的语言回答。""",
            
            "qa_engineer": """你是一个测试工程师，负责：
1. 测试计划设计和执行
2. 质量保证和缺陷管理
3. 自动化测试开发
4. 性能和安全测试

你的性格特点：严谨、细致、质量导向。请用准确、详细的语言回答。""",
            
            "devops_engineer": """你是一个DevOps工程师，负责：
1. 系统部署和配置管理
2. 监控和运维自动化
3. CI/CD流程设计
4. 环境管理和优化

你的性格特点：自动化思维、系统化、效率导向。请用实用、系统性的语言回答。"""
        }
        
        system_message = system_messages.get(role, "你是一个专业的团队成员。")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"上下文：{context}\n\n任务：{prompt}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            return LLMResponse(
                role=role,
                content=content,
                confidence=0.9,
                reasoning="基于角色专业知识和项目上下文生成",
                timestamp=time.time()
            )
            
        except Exception as e:
            # 如果API调用失败，返回模拟响应
            return self._get_fallback_response(role, prompt)
    
    def _get_fallback_response(self, role: str, prompt: str) -> LLMResponse:
        """获取备用响应（当API不可用时）"""
        
        fallback_responses = {
            "boss": {
                "需求理解": "我理解了客户需求，这是一个很有价值的项目。我们需要确保按时交付高质量的产品。",
                "项目验收": "项目已经完成，质量符合预期，可以交付给客户。",
                "预算分配": "基于项目复杂度，我建议分配合理的预算和资源。"
            },
            "product_manager": {
                "需求分析": "基于客户需求，我制定了详细的产品方案，包括用户故事、功能列表和交互设计。",
                "产品方案": "产品方案已确定，包括核心功能模块、用户界面设计和业务流程。",
                "功能设计": "功能设计已完成，涵盖了所有用户需求和使用场景。"
            },
            "tech_lead": {
                "技术方案": "我设计了完整的技术架构，包括前端React、后端Python FastAPI、PostgreSQL数据库和Docker部署。",
                "架构设计": "系统架构采用微服务设计，支持高并发和可扩展性。",
                "技术选型": "技术栈选型合理，能够满足项目需求并保证系统稳定性。"
            },
            "frontend_dev": {
                "前端开发": "前端页面已开发完成，包括用户界面、组件库和响应式设计。",
                "UI实现": "所有页面都已实现，用户体验良好，支持移动端适配。",
                "组件开发": "React组件库已开发完成，代码结构清晰，可复用性强。"
            },
            "backend_dev": {
                "后端开发": "后端API已开发完成，包括用户管理、数据操作和业务逻辑。",
                "数据库设计": "数据库设计合理，支持数据完整性和性能优化。",
                "API开发": "RESTful API设计规范，支持完整的CRUD操作。"
            },
            "qa_engineer": {
                "测试计划": "测试计划已制定，包括功能测试、性能测试和安全测试。",
                "质量保证": "所有测试用例已执行，产品质量符合标准。",
                "缺陷管理": "发现的问题已记录并分配给开发团队修复。"
            },
            "devops_engineer": {
                "系统部署": "系统已部署到云服务器，配置了监控和自动化部署。",
                "运维监控": "运维环境已搭建完成，包括日志监控、性能监控和告警系统。",
                "自动化": "CI/CD流程已配置，支持自动化构建、测试和部署。"
            }
        }
        
        # 根据角色和提示返回相应响应
        responses = fallback_responses.get(role, {})
        for key, response in responses.items():
            if key in prompt:
                return LLMResponse(
                    role=role,
                    content=response,
                    confidence=0.8,
                    reasoning="使用备用响应模式",
                    timestamp=time.time()
                )
        
        return LLMResponse(
            role=role,
            content=f"{role}已完成相关任务。",
            confidence=0.7,
            reasoning="通用备用响应",
            timestamp=time.time()
        ) 