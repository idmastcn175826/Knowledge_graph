from typing import Dict, Any
from datetime import datetime

from app.agent_framework.memory.memory import MemorySystem
from app.agent_framework.observer.observer import Observable


class PerceptionSystem(Observable):
    """感知系统，处理输入信息"""
    def __init__(self, memory_system: MemorySystem):
        super().__init__()
        self._memory = memory_system
    
    def process_input(self, input_data: str, input_type: str = "text") -> Dict[str, Any]:
        """处理输入信息"""
        # 处理不同类型的输入（文本、语音转文本等）
        processed = {
            "original_input": input_data,
            "processed_input": input_data,
            "input_type": input_type,
            "timestamp": datetime.now()
        }
        
        # 将输入存储到短期记忆
        memory_id = self._memory.add_short_term_memory(
            content=f"用户输入: {input_data}",
            metadata={"type": input_type}
        )
        processed["memory_id"] = memory_id
        
        self.notify_observers("input_processed", processed)
        return processed
