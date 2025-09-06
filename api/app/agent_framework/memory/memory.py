from app.agent_framework.observer.observer import Observable
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

@dataclass
class MemoryEntry:
    """记忆条目数据类"""
    id: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


class MemorySystem(Observable):
    """记忆系统，负责存储和检索信息"""
    def __init__(self, max_short_term_entries: int = 100):
        super().__init__()
        self._short_term_memory: List[MemoryEntry] = []
        self._long_term_memory: Dict[str, MemoryEntry] = {}
        self._max_short_term_entries = max_short_term_entries  # 短期记忆最大条目数
    
    def add_short_term_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加短期记忆"""
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self._short_term_memory.append(entry)
        
        # 保持短期记忆在限制范围内
        if len(self._short_term_memory) > self._max_short_term_entries:
            self._short_term_memory.pop(0)
        
        self.notify_observers("memory_added", {"type": "short_term", "id": entry_id})
        return entry_id
    
    def add_long_term_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加长期记忆"""
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self._long_term_memory[entry_id] = entry
        
        self.notify_observers("memory_added", {"type": "long_term", "id": entry_id})
        return entry_id
    
    def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """检索与查询相关的记忆"""
        relevant = []
        
        # 先检查短期记忆
        for entry in reversed(self._short_term_memory):
            if query.lower() in entry.content.lower():
                relevant.append(entry)
                if len(relevant) >= limit:
                    break
        
        # 如果不够，检查长期记忆
        if len(relevant) < limit:
            for entry in self._long_term_memory.values():
                if query.lower() in entry.content.lower():
                    relevant.append(entry)
                    if len(relevant) >= limit:
                        break
        
        return relevant
    
    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """通过ID获取记忆"""
        # 先检查短期记忆
        for entry in self._short_term_memory:
            if entry.id == memory_id:
                return entry
        
        # 再检查长期记忆
        return self._long_term_memory.get(memory_id)
    
    def clear_short_term_memory(self):
        """清除短期记忆"""
        self._short_term_memory = []
        self.notify_observers("memory_cleared", {"type": "short_term"})
    
    def get_short_term_memory_count(self) -> int:
        """获取短期记忆数量（主要用于测试）"""
        return len(self._short_term_memory)
    
    def get_long_term_memory_count(self) -> int:
        """获取长期记忆数量（主要用于测试）"""
        return len(self._long_term_memory)
