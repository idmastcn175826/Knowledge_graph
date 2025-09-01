from abc import ABC, abstractmethod
from typing import List, Tuple, Dict


class KnowledgeCompletionStrategy(ABC):
    """知识补全算法策略基类"""

    @abstractmethod
    def complete(self,
                 entities: List[Dict],
                 relations: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """
        补全知识图谱中可能缺失的关系

        Args:
            entities: 实体列表
            relations: 已有的关系三元组列表

        Returns:
            补全的关系三元组列表，每个三元组为(实体1id, 关系类型, 实体2id)
        """
        pass

    @abstractmethod
    def save_model(self, path: str) -> None:
        """保存模型到指定路径"""
        pass

    @abstractmethod
    def load_model(self, path: str) -> None:
        """从指定路径加载模型"""
        pass
