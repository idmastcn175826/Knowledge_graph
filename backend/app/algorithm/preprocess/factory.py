from .base import PreprocessStrategy
from .simhash import SimHashPreprocessor
from .minhash import MinHashPreprocessor


class PreprocessFactory:
    """预处理算法工厂类，用于创建不同的预处理策略实例"""

    @staticmethod
    def get_strategy(algorithm: str) -> PreprocessStrategy:
        """
        根据算法名称获取对应的预处理策略实例

        Args:
            algorithm: 算法名称，支持 'simhash' 和 'minhash'

        Returns:
            预处理策略实例

        Raises:
            ValueError: 如果算法名称不支持
        """
        if algorithm == 'simhash':
            return SimHashPreprocessor()
        elif algorithm == 'minhash':
            return MinHashPreprocessor()
        else:
            raise ValueError(f"不支持的预处理算法: {algorithm}，支持的算法有: 'simhash', 'minhash'")
