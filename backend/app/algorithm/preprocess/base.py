from abc import ABC, abstractmethod
from typing import List


class PreprocessStrategy(ABC):
    """预处理算法策略基类"""

    @abstractmethod
    def process(self, text: str) -> str:
        """
        处理单段文本

        Args:
            text: 待处理的文本

        Returns:
            处理后的文本
        """
        pass

    @abstractmethod
    def deduplicate(self, texts: List[str]) -> List[str]:
        """
        文本去重

        Args:
            texts: 文本列表

        Returns:
            去重后的文本列表
        """
        pass
