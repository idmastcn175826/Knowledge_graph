import json
from typing import List, Dict, Any

import openai

from app.agent_framework.config import Config
from app.agent_framework.llm.llm_base import LLMClient

# 确保配置有效
Config.validate()



class QwenClient(LLMClient):
    """Qwen大模型客户端实现"""
    
    def __init__(self):
        config = Config.get_model_config()
        self.client = openai.OpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"]
        )
        self.model = config["model"]
    
    def chat_completion(self, messages: List[Dict[str, str]],** kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Qwen API 调用错误: {str(e)}"
    
    def generate_thought(self, prompt: str, memory_context: str) -> str:
        messages = [
            {"role": "system", "content": "你是一个智能体的思考模块。请分析用户的问题，结合提供的记忆上下文，思考如何回答这个问题。不需要给出最终答案，只需描述你的思考过程。"},
            {"role": "user", "content": f"用户问题: {prompt}\n记忆上下文: {memory_context}"}
        ]
        return self.chat_completion(messages)
    
    def decide_tool_use(self, prompt: str, thought: str, tools_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        tools_desc = "\n".join([f"- {tool['name']}: {tool['description']}, 参数: {tool['parameters']}" for tool in tools_metadata])
        
        messages = [
            {"role": "system", "content": f"""你需要决定是否调用工具来回答用户问题。可用工具如下:
{tools_desc}

请返回一个JSON对象，包含:
- need_tool: 布尔值，表示是否需要调用工具
- tool_name: 若需要调用工具，则为工具名称
- parameters: 若需要调用工具，则为工具参数的键值对
- reason: 做出此决定的原因"""},
            {"role": "user", "content": f"用户问题: {prompt}\n思考过程: {thought}"}
        ]
        
        response = self.chat_completion(messages)
        try:
            return json.loads(response)
        except:
            return {"need_tool": False, "reason": f"无法解析工具决策: {response}"}
    
    def evaluate_result(self, query: str, tool_result: Any, thought: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": """请评估工具调用结果是否足够回答用户问题。
请返回一个JSON对象，包含:
- sufficient: 布尔值，表示结果是否足够
- reason: 评估理由
- next_step: 如果结果不足够，下一步建议"""},
            {"role": "user", "content": f"用户问题: {query}\n思考过程: {thought}\n工具结果: {str(tool_result)}"}
        ]
        
        response = self.chat_completion(messages)
        try:
            return json.loads(response)
        except:
            return {"sufficient": False, "reason": f"无法解析结果评估: {response}", "next_step": "请重新尝试"}
    
    def generate_response(self, query: str, thought: str, memory_context: str, tool_result: Any = None) -> str:
        content = f"用户问题: {query}\n思考过程: {thought}\n记忆上下文: {memory_context}"
        if tool_result:
            content += f"\n工具结果: {str(tool_result)}"
        
        messages = [
            {"role": "system", "content": "请根据用户问题、思考过程、记忆上下文和可能的工具结果，生成一个自然、准确的回答。"},
            {"role": "user", "content": content}
        ]
        
        return self.chat_completion(messages)

class OpenAIClient(LLMClient):
    """OpenAI大模型客户端实现"""
    
    def __init__(self):
        config = Config.get_model_config()
        self.client = openai.OpenAI(
            api_key=config["api_key"],
            base_url=config["api_base"]
        )
        self.model = config["model"]
    
    def chat_completion(self, messages: List[Dict[str, str]],** kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI API 调用错误: {str(e)}"
    
    def generate_thought(self, prompt: str, memory_context: str) -> str:
        # 与Qwen使用相同的提示词模板，确保行为一致
        messages = [
            {"role": "system", "content": "你是一个智能体的思考模块。请分析用户的问题，结合提供的记忆上下文，思考如何回答这个问题。不需要给出最终答案，只需描述你的思考过程。"},
            {"role": "user", "content": f"用户问题: {prompt}\n记忆上下文: {memory_context}"}
        ]
        return self.chat_completion(messages)
    
    def decide_tool_use(self, prompt: str, thought: str, tools_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 与Qwen使用相同的提示词模板，确保行为一致
        tools_desc = "\n".join([f"- {tool['name']}: {tool['description']}, 参数: {tool['parameters']}" for tool in tools_metadata])
        
        messages = [
            {"role": "system", "content": f"""你需要决定是否调用工具来回答用户问题。可用工具如下:
{tools_desc}

请返回一个JSON对象，包含:
- need_tool: 布尔值，表示是否需要调用工具
- tool_name: 若需要调用工具，则为工具名称
- parameters: 若需要调用工具，则为工具参数的键值对
- reason: 做出此决定的原因"""},
            {"role": "user", "content": f"用户问题: {prompt}\n思考过程: {thought}"}
        ]
        
        response = self.chat_completion(messages)
        try:
            return json.loads(response)
        except:
            return {"need_tool": False, "reason": f"无法解析工具决策: {response}"}
    
    def evaluate_result(self, query: str, tool_result: Any, thought: str) -> Dict[str, Any]:
        # 与Qwen使用相同的提示词模板，确保行为一致
        messages = [
            {"role": "system", "content": """请评估工具调用结果是否足够回答用户问题。
请返回一个JSON对象，包含:
- sufficient: 布尔值，表示结果是否足够
- reason: 评估理由
- next_step: 如果结果不足够，下一步建议"""},
            {"role": "user", "content": f"用户问题: {query}\n思考过程: {thought}\n工具结果: {str(tool_result)}"}
        ]
        
        response = self.chat_completion(messages)
        try:
            return json.loads(response)
        except:
            return {"sufficient": False, "reason": f"无法解析结果评估: {response}", "next_step": "请重新尝试"}
    
    def generate_response(self, query: str, thought: str, memory_context: str, tool_result: Any = None) -> str:
        # 与Qwen使用相同的提示词模板，确保行为一致
        content = f"用户问题: {query}\n思考过程: {thought}\n记忆上下文: {memory_context}"
        if tool_result:
            content += f"\n工具结果: {str(tool_result)}"
        
        messages = [
            {"role": "system", "content": "请根据用户问题、思考过程、记忆上下文和可能的工具结果，生成一个自然、准确的回答。"},
            {"role": "user", "content": content}
        ]
        
        return self.chat_completion(messages)

class LLMClientFactory:
    """大模型客户端工厂类，根据配置创建相应的客户端实例"""
    
    @staticmethod
    def create_client() -> LLMClient:
        provider = Config.MODEL_PROVIDER
        if provider == "qwen":
            return QwenClient()
        elif provider == "openai":
            return OpenAIClient()
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
