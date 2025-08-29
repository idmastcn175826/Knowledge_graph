import logging

from app.algorithm.extraction.base import (
    EntityExtractionStrategy,
    RelationExtractionStrategy
)
from app.algorithm.extraction.bert_strategy import BERTEntityExtraction
from app.algorithm.extraction.crf_strategy import CRFEntityExtraction
from app.algorithm.extraction.qwen_strategy import QwenEntityExtraction, QwenRelationExtraction


class EntityExtractionFactory:
    """实体抽取算法工厂类"""

    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> EntityExtractionStrategy:
        if algorithm == 'crf':
            return CRFEntityExtraction()
        elif algorithm == 'qwen':
            return QwenEntityExtraction(api_key)
        else:
            raise ValueError(f"不支持的实体抽取算法: {algorithm}")


class RelationExtractionFactory:
    """关系抽取算法工厂类"""

    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> RelationExtractionStrategy:
        if algorithm == 'qwen':
            return QwenRelationExtraction(api_key)
        # 可以添加其他关系抽取算法
        else:
            raise ValueError(f"不支持的关系抽取算法: {algorithm}")
logger = logging.getLogger(__name__)

class EntityExtractionFactory:
    """实体抽取算法工厂"""
    
    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> EntityExtractionStrategy:
        """
        获取实体抽取策略实例
        
        Args:
            algorithm: 算法名称
            api_key: 模型API密钥，当使用Qwen等API模型时需要
            
        Returns:
            实体抽取策略实例
        """
        algorithm = algorithm.lower()
        
        if algorithm == "bert":
            logger.info("使用BERT实体抽取算法")
            return BERTEntityExtraction()
        elif algorithm == "crf":
            logger.info("使用CRF实体抽取算法")
            return CRFEntityExtraction()
        elif algorithm == "qwen":
            logger.info("使用Qwen实体抽取算法")
            return QwenEntityExtraction(api_key)
        else:
            logger.warning(f"未知的实体抽取算法: {algorithm}，使用默认算法BERT")
            return BERTEntityExtraction()


class RelationExtractionFactory:
    """关系抽取算法工厂"""
    
    @staticmethod
    def get_strategy(algorithm: str, api_key: str = None) -> RelationExtractionStrategy:
        """
        获取关系抽取策略实例
        
        Args:
            algorithm: 算法名称
            api_key: 模型API密钥，当使用Qwen等API模型时需要
            
        Returns:
            关系抽取策略实例
        """
        algorithm = algorithm.lower()
        
        if algorithm == "qwen":
            logger.info("使用Qwen关系抽取算法")
            return QwenRelationExtraction(api_key)
        elif algorithm == "bilstm":
            logger.info("使用BiLSTM关系抽取算法")
            # 这里实际应该返回BiLSTM实现
            return QwenRelationExtraction(api_key)  # 临时使用Qwen作为替代
        else:
            logger.warning(f"未知的关系抽取算法: {algorithm}，使用默认算法Qwen")
            return QwenRelationExtraction(api_key)
