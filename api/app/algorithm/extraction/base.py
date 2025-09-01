from abc import ABC, abstractmethod
from typing import List, Dict, Tuple


class EntityExtractionStrategy(ABC):
    """实体抽取算法策略基类"""

    @abstractmethod
    def extract(self, text: str) -> List[Dict]:
        """
        从文本中抽取实体

        Args:
            text: 待处理的文本

        Returns:
            实体列表，每个实体是包含id、name、type、start_pos、end_pos等信息的字典
        """
        pass


class RelationExtractionStrategy(ABC):
    """关系抽取算法策略基类"""

    @abstractmethod
    def extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """
        从文本中抽取实体间的关系

        Args:
            text: 待处理的文本
            entities: 已抽取的实体列表

        Returns:
            关系三元组列表，每个三元组为(实体1id, 关系类型, 实体2id)
        """
        pass


class AttributeExtractionStrategy(ABC):
    """属性抽取算法策略基类"""

    @abstractmethod
    def extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """
        从文本中抽取实体的属性

        Args:
            text: 待处理的文本
            entities: 已抽取的实体列表

        Returns:
            属性三元组列表，每个三元组为(实体id, 属性名, 属性值)
        """
        pass
