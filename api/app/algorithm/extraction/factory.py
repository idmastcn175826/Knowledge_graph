import logging

from app.algorithm.extraction.base import (
    EntityExtractionStrategy,
    RelationExtractionStrategy
)
from app.algorithm.extraction.bert_strategy import BERTEntityExtraction
from app.algorithm.extraction.crf_strategy import CRFEntityExtraction
from app.algorithm.extraction.qwen_strategy import QwenEntityExtraction, QwenRelationExtraction

# 初始化日志（确保日志能正常输出）
logger = logging.getLogger(__name__)


class EntityExtractionFactory:
    """实体抽取算法工厂（增强版，支持多算法+默认降级）"""

    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> EntityExtractionStrategy:
        """
        获取实体抽取策略实例

        Args:
            algorithm: 算法名称（支持bert、crf、qwen）
            api_key: 模型API密钥（仅Qwen算法需要）

        Returns:
            实体抽取策略实例
        """
        if not algorithm:
            logger.warning("算法名称为空，使用默认算法BERT")
            return BERTEntityExtraction()

        algorithm = algorithm.lower()

        if algorithm == "bert":
            logger.info("使用BERT实体抽取算法")
            return BERTEntityExtraction()
        elif algorithm == "crf":
            logger.info("使用CRF实体抽取算法")
            return CRFEntityExtraction()
        elif algorithm == "qwen":
            logger.info("使用Qwen实体抽取算法（传入API密钥）")
            return QwenEntityExtraction(api_key)  # 确保传入API密钥
        else:
            logger.warning(f"未知的实体抽取算法: {algorithm}，使用默认算法BERT")
            return BERTEntityExtraction()


class RelationExtractionFactory:
    """关系抽取算法工厂（增强版，支持多算法+默认降级）"""

    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> RelationExtractionStrategy:
        """
        获取关系抽取策略实例

        Args:
            algorithm: 算法名称（支持qwen、bilstm）
            api_key: 模型API密钥（仅Qwen算法需要）

        Returns:
            关系抽取策略实例
        """
        if not algorithm:
            logger.warning("算法名称为空，使用默认算法Qwen")
            return QwenRelationExtraction(api_key)

        algorithm = algorithm.lower()

        if algorithm == "qwen":
            logger.info("使用Qwen关系抽取算法（传入API密钥）")
            return QwenRelationExtraction(api_key)  # 关键：返回增强版Qwen实例
        elif algorithm == "bilstm":
            logger.warning("BiLSTM关系抽取算法暂未实现，使用默认算法Qwen")
            # TODO: 后续实现BiLSTMRelationExtraction后替换以下代码
            # from app.algorithm.extraction.bilstm_strategy import BiLSTMRelationExtraction
            # return BiLSTMRelationExtraction()
            return QwenRelationExtraction(api_key)
        else:
            logger.warning(f"未知的关系抽取算法: {algorithm}，使用默认算法Qwen")
            return QwenRelationExtraction(api_key)