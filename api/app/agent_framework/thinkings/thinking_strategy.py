from abc import ABC, abstractmethod
from app.agent_framework.thinkings.thought import Thought, ThoughtType
from app.agent_framework.memory.memory import MemorySystem
from datetime import datetime
import uuid

class ThinkingStrategy(ABC):
    """思考策略接口"""
    @abstractmethod
    def think(self, prompt: str, memory: MemorySystem) -> Thought:
        """根据提示和记忆进行思考"""
        pass

class BasicThinkingStrategy(ThinkingStrategy):
    """基础思考策略实现，用于测试"""
    def think(self, prompt: str, memory: MemorySystem) -> Thought:
        """简单的思考过程模拟"""
        relevant_memories = memory.retrieve_relevant_memories(prompt)
        related_memory_ids = [mem.id for mem in relevant_memories]
        
        # 简单模拟思考过程
        thought_content = f"分析用户问题: '{prompt}'. "
        
        if relevant_memories:
            thought_content += f"找到了相关记忆: {[mem.content[:30] + '...' for mem in relevant_memories]}. "
        
        thought_content += "需要判断是否需要调用工具来回答这个问题。"
        
        return Thought(
            id=str(uuid.uuid4()),
            content=thought_content,
            thought_type=ThoughtType.ANALYSIS,
            timestamp=datetime.now(),
            related_memory_ids=related_memory_ids
        )

class LLMBasedThinkingStrategy(ThinkingStrategy):
    """基于大模型的思考策略，兼容多种模型"""
    
    def __init__(self, llm_client):
        """
        初始化思考策略
        :param llm_client: LLM客户端实例，需实现generate_thought方法
        """
        self._llm_client = llm_client
    
    def think(self, prompt: str, memory: MemorySystem) -> Thought:
        """使用大模型进行思考"""
        # 获取相关记忆作为上下文
        relevant_memories = memory.retrieve_relevant_memories(prompt)
        related_memory_ids = [mem.id for mem in relevant_memories]
        
        # 构建记忆上下文
        memory_context = "\n".join([mem.content for mem in relevant_memories])
        
        # 调用大模型生成思考过程
        thought_content = self._llm_client.generate_thought(prompt, memory_context)
        
        return Thought(
            id=str(uuid.uuid4()),
            content=thought_content,
            thought_type=ThoughtType.ANALYSIS,
            timestamp=datetime.now(),
            related_memory_ids=related_memory_ids
        )
