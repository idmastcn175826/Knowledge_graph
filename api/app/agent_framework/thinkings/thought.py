from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class ThoughtType(Enum):
    """思考类型枚举"""
    ANALYSIS = "analysis"  # 分析问题
    PLANNING = "planning"  # 规划步骤
    DECISION = "decision"  # 做出决策
    EVALUATION = "evaluation"  # 评估结果

@dataclass
class Thought:
    """思考过程数据类"""
    id: str
    content: str
    thought_type: ThoughtType
    timestamp: datetime
    related_memory_ids: List[str] = None
    
    def __post_init__(self):
        if self.related_memory_ids is None:
            self.related_memory_ids = []
