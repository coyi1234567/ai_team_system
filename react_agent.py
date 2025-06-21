import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ReActStep:
    """ReAct步骤的数据结构"""
    thought: str  # 推理过程
    action: str   # 行动名称
    action_input: str  # 行动输入
    observation: str = ""  # 观察结果

class ReActAgent:
    """ReAct模式Agent实现"""
    
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps
        self.tools = {
            "search": self.search_tool,
            "calculator": self.calculator_tool,
            "lookup": self.lookup_tool
        }
    
    def search_tool(self, query: str) -> str:
        """搜索工具 - 模拟搜索结果"""
        # 这里可以集成真实的搜索API
        return f"搜索结果: 关于'{query}'的信息"
    
    def calculator_tool(self, expression: str) -> str:
        """计算器工具"""
        try:
            result = eval(expression)
            return f"计算结果: {expression} = {result}"
        except:
            return f"计算错误: 无法计算 {expression}"
    
    def lookup_tool(self, key: str) -> str:
        """查找工具 - 模拟知识库查询"""
        knowledge_base = {
            "北京": "中国的首都，人口约2100万",
            "上海": "中国最大的城市，人口约2400万",
            "深圳": "中国科技城市，人口约1700万"
        }
        return knowledge_base.get(key, f"未找到关于'{key}'的信息")
    
    def parse_llm_response(self, response: str) -> ReActStep:
        """解析LLM响应，提取推理、行动和输入"""
        # 简单的正则表达式解析
        thought_match = re.search(r"思考:(.*?)(?=行动:|$)", response, re.DOTALL)
        action_match = re.search(r"行动:(.*?)(?=输入:|$)", response, re.DOTALL)
        input_match = re.search(r"输入:(.*?)(?=观察:|$)", response, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else ""
        action_input = input_match.group(1).strip() if input_match else ""
        
        return ReActStep(thought=thought, action=action, action_input=action_input)
    
    def execute_action(self, step: ReActStep) -> str:
        """执行行动并返回观察结果"""
        if step.action in self.tools:
            return self.tools[step.action](step.action_input)
        else:
            return f"未知行动: {step.action}"
    
    def solve(self, question: str) -> str:
        """使用ReAct模式解决问题"""
        steps = []
        current_context = f"问题: {question}\n"
        
        for step_num in range(self.max_steps):
            # 构建提示词
            prompt = f"""
{current_context}

请按照以下格式回答:
思考: [你的推理过程]
行动: [search/calculator/lookup]
输入: [行动的具体输入]

可用工具:
- search: 搜索信息
- calculator: 计算数学表达式  
- lookup: 查找知识库信息
"""
            
            # 这里应该调用真实的LLM
            # 为了演示，我们模拟LLM响应
            llm_response = self.simulate_llm_response(question, step_num, current_context)
            
            # 解析响应
            step = self.parse_llm_response(llm_response)
            step.observation = self.execute_action(step)
            
            steps.append(step)
            
            # 更新上下文
            current_context += f"""
步骤 {step_num + 1}:
思考: {step.thought}
行动: {step.action}
输入: {step.action_input}
观察: {step.observation}\n"""
            
            # 检查是否应该停止
            if "最终答案" in step.thought or step_num == self.max_steps - 1:
                break
        
        return self.format_final_answer(steps, question)
    
    def simulate_llm_response(self, question: str, step_num: int, context: str) -> str:
        """模拟LLM响应 - 实际使用时替换为真实LLM调用"""
        if "北京" in question:
            if step_num == 0:
                return "思考: 用户想了解北京的信息，我需要查找相关知识\n行动: lookup\n输入: 北京"
            else:
                return "思考: 已经获得了北京的信息，可以给出最终答案\n行动: 最终答案\n输入: 北京是中国的首都，人口约2100万"
        
        elif "计算" in question or "+" in question or "*" in question:
            if step_num == 0:
                return "思考: 这是一个数学计算问题，需要使用计算器\n行动: calculator\n输入: 2+3*4"
            else:
                return "思考: 计算完成，可以给出最终答案\n行动: 最终答案\n输入: 2+3*4 = 14"
        
        else:
            if step_num == 0:
                return "思考: 需要搜索相关信息来回答问题\n行动: search\n输入: " + question
            else:
                return "思考: 基于搜索结果，可以给出答案\n行动: 最终答案\n输入: 根据搜索结果，这是相关信息"
    
    def format_final_answer(self, steps: List[ReActStep], question: str) -> str:
        """格式化最终答案"""
        result = f"问题: {question}\n\n"
        result += "ReAct解决过程:\n"
        
        for i, step in enumerate(steps):
            result += f"\n步骤 {i+1}:\n"
            result += f"思考: {step.thought}\n"
            result += f"行动: {step.action}\n"
            result += f"输入: {step.action_input}\n"
            result += f"观察: {step.observation}\n"
        
        # 提取最终答案
        final_step = steps[-1]
        if "最终答案" in final_step.action:
            result += f"\n最终答案: {final_step.action_input}"
        else:
            result += f"\n最终答案: {final_step.observation}"
        
        return result

# 使用示例
if __name__ == "__main__":
    agent = ReActAgent()
    
    # 测试问题
    questions = [
        "北京是什么地方？",
        "计算 2+3*4 等于多少？",
        "什么是人工智能？"
    ]
    
    for question in questions:
        print("=" * 50)
        answer = agent.solve(question)
        print(answer)
        print("=" * 50) 