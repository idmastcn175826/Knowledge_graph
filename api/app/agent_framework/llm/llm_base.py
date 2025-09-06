from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMClient(ABC):
    """大模型客户端抽象基类"""

    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        基础聊天接口
        :param messages: 聊天消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
        :return: 模型返回的响应内容
        """
        pass

    @abstractmethod
    def generate_thought(self, prompt: str, memory_context: str) -> str:
        """生成思考过程"""
        pass

    @abstractmethod
    def decide_tool_use(self, prompt: str, thought: str, tools_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """决定是否使用工具及使用哪个工具"""
        pass

    @abstractmethod
    def evaluate_result(self, query: str, tool_result: Any, thought: str) -> Dict[str, Any]:
        """评估工具调用结果是否足够回答问题"""
        pass

    @abstractmethod
    def generate_response(self, query: str, thought: str, memory_context: str, tool_result: Any = None) -> str:
        """生成最终回答"""
        pass