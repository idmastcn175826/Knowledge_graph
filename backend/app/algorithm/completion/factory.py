from .base import KnowledgeCompletionStrategy
from .transe_strategy import TransEKnowledgeCompletion


# 后续可以添加其他知识补全算法的导入

class KnowledgeCompletionFactory:
    """知识补全算法工厂类，用于创建不同的知识补全策略实例"""

    @staticmethod
    def get_strategy(algorithm: str, **kwargs) -> KnowledgeCompletionStrategy:
        """
        根据算法名称获取对应的知识补全策略实例

        Args:
            algorithm: 算法名称，支持 'transe', 'transh', 'rotate' 等
           ** kwargs: 算法的初始化参数

        Returns:
            知识补全策略实例

        Raises:
            ValueError: 如果算法名称不支持
        """
        if algorithm == 'transe':
            return TransEKnowledgeCompletion(**kwargs)
        # 可以添加其他知识补全算法的支持
        # elif algorithm == 'transh':
        #     return TransHKnowledgeCompletion(** kwargs)
        # elif algorithm == 'rotate':
        #     return RotatEKnowledgeCompletion(**kwargs)
        else:
            raise ValueError(f"不支持的知识补全算法: {algorithm}，目前支持的算法有: 'transe'")
