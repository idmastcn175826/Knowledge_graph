from app.agent_framework.observer.observer import Observable
from app.agent_framework.memory.memory import MemorySystem
from app.agent_framework.factory.tool_factory import ToolFactory
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class ActionType(Enum):
    """行动类型枚举"""
    RESPONSE = "response"  # 生成响应
    TOOL_CALL = "tool_call"  # 调用工具
    MEMORY_STORAGE = "memory_storage"  # 存储记忆

@dataclass
class Action:
    """行动数据类"""
    id: str
    action_type: ActionType
    content: Any
    timestamp: datetime
    related_thought_id: Optional[str] = None
    result: Optional[Any] = None

class ActionSystem(Observable):
    """行动系统，负责执行操作"""
    def __init__(self, memory_system: MemorySystem, tool_factory: ToolFactory):
        super().__init__()
        self._memory = memory_system
        self._tool_factory = tool_factory
        self._pending_actions = []
    
    def generate_response(self, content: str, thought_id: Optional[str] = None) -> Action:
        """生成响应"""
        action = Action(
            id=str(uuid.uuid4()),
            action_type=ActionType.RESPONSE,
            content=content,
            timestamp=datetime.now(),
            related_thought_id=thought_id
        )
        
        # 将响应存储到记忆
        self._memory.add_short_term_memory(
            content=f"系统响应: {content}",
            metadata={"action_id": action.id}
        )
        
        self.notify_observers("action_executed", action)
        return action
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any], thought_id: Optional[str] = None) -> Action:
        """调用工具"""
        try:
            # 创建工具实例
            tool = self._tool_factory.create_tool(tool_name)
            
            # 执行工具
            result = tool.execute(**parameters)
            
            # 创建行动记录
            action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.TOOL_CALL,
                content={
                    "tool_name": tool_name,
                    "parameters": parameters
                },
                timestamp=datetime.now(),
                related_thought_id=thought_id,
                result=result
            )
            
            # 将工具调用结果存储到记忆
            self._memory.add_short_term_memory(
                content=f"工具调用 {tool_name} 结果: {str(result)[:100]}",
                metadata={"action_id": action.id, "tool_name": tool_name}
            )
            
            self.notify_observers("action_executed", action)
            return action
            
        except Exception as e:
            error_action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.TOOL_CALL,
                content={
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "error": str(e)
                },
                timestamp=datetime.now(),
                related_thought_id=thought_id,
                result={"error": str(e)}
            )
            
            self.notify_observers("action_failed", error_action)
            return error_action
    
    def store_in_long_term_memory(self, content: str, thought_id: Optional[str] = None) -> Action:
        """将内容存储到长期记忆"""
        memory_id = self._memory.add_long_term_memory(content)
        
        action = Action(
            id=str(uuid.uuid4()),
            action_type=ActionType.MEMORY_STORAGE,
            content={"memory_id": memory_id, "content": content},
            timestamp=datetime.now(),
            related_thought_id=thought_id
        )
        
        self.notify_observers("action_executed", action)
        return action
