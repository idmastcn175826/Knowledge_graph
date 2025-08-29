import requests
import json
import uuid
from typing import List, Dict, Tuple
from app.algorithm.extraction.base import EntityExtractionStrategy, RelationExtractionStrategy
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class QwenEntityExtraction(EntityExtractionStrategy):
    """基于Qwen模型的实体抽取策略实现"""

    def __init__(self, api_key: str = None):
        """
        初始化Qwen实体抽取器

        Args:
            api_key: Qwen API密钥，若为None则使用配置中的默认密钥
        """
        self.api_key = api_key or settings.qwen_default_api_key
        self.api_base_url = settings.qwen_api_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        if not self.api_key:
            logger.warning("Qwen API密钥未配置，实体抽取功能可能无法正常工作")

    def extract(self, text: str) -> List[Dict]:
        """
        使用Qwen模型从文本中抽取实体

        Args:
            text: 待处理的文本

        Returns:
            实体列表，每个实体包含id、name、type等信息
        """
        if not self.api_key:
            logger.error("Qwen API密钥未配置，无法进行实体抽取")
            return []

        try:
            # 构建提示词
            prompt = f"""请从以下文本中抽取实体，并按照指定格式返回结果。
实体类型包括但不限于：人物、组织、地点、时间、事件、产品等。
如果识别到其他有意义的实体类型也可以返回。

文本：{text}

请以JSON数组格式返回，每个实体包含以下字段：
- "name": 实体名称
- "type": 实体类型
- "start_pos": 实体在文本中的起始位置索引
- "end_pos": 实体在文本中的结束位置索引

只返回JSON数组，不要添加任何额外说明文字。"""

            # 调用Qwen API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": "你是一个实体抽取专家，能够准确识别文本中的各类实体。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }

            response = requests.post(
                self.api_base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # 解析API返回结果
            if "choices" in result and len(result["choices"]) > 0:
                entity_str = result["choices"][0]["message"]["content"].strip()
                entities = json.loads(entity_str)

                # 为每个实体添加唯一ID
                for i, entity in enumerate(entities):
                    entity["id"] = f"entity_{uuid.uuid4().hex[:8]}"

                logger.info(f"从文本中成功抽取到 {len(entities)} 个实体")
                return entities
            else:
                logger.warning("Qwen API返回结果不包含有效实体信息")
                return []

        except Exception as e:
            logger.error(f"Qwen模型实体抽取失败: {str(e)}")
            # 发生错误时返回空列表或 fallback 到其他抽取方式
            return []


class QwenRelationExtraction(RelationExtractionStrategy):
    """基于Qwen模型的关系抽取策略实现"""

    def __init__(self, api_key: str = None):
        """
        初始化Qwen关系抽取器

        Args:
            api_key: Qwen API密钥，若为None则使用配置中的默认密钥
        """
        self.api_key = api_key or settings.qwen_default_api_key
        self.api_base_url = settings.qwen_api_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        if not self.api_key:
            logger.warning("Qwen API密钥未配置，关系抽取功能可能无法正常工作")

    def extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """
        使用Qwen模型从文本中抽取实体间的关系

        Args:
            text: 待处理的文本
            entities: 已抽取的实体列表

        Returns:
            关系三元组列表，每个三元组为(实体1id, 关系类型, 实体2id)
        """
        if not self.api_key:
            logger.error("Qwen API密钥未配置，无法进行关系抽取")
            return []

        if not entities or len(entities) < 2:
            logger.info("实体数量不足，无需进行关系抽取")
            return []

        try:
            # 构建实体列表描述
            entity_descriptions = "\n".join([
                f"- ID: {entity['id']}, 名称: {entity['name']}, 类型: {entity['type']}"
                for entity in entities
            ])

            # 构建提示词
            prompt = f"""请从以下文本中抽取已识别实体之间的关系，并按照指定格式返回结果。

文本：{text}

已识别的实体列表：
{entity_descriptions}

请找出这些实体之间存在的关系，以JSON数组格式返回，每个关系包含以下字段：
- "entity1_id": 第一个实体的ID
- "relation": 实体间的关系类型
- "entity2_id": 第二个实体的ID

只返回JSON数组，不要添加任何额外说明文字。如果没有识别到关系，返回空数组。"""

            # 调用Qwen API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": "你是一个关系抽取专家，能够准确识别文本中实体之间的各类关系。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }

            response = requests.post(
                self.api_base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # 解析API返回结果
            if "choices" in result and len(result["choices"]) > 0:
                relation_str = result["choices"][0]["message"]["content"].strip()
                relations = json.loads(relation_str)

                # 转换为三元组列表
                relation_triplets = [
                    (rel["entity1_id"], rel["relation"], rel["entity2_id"])
                    for rel in relations
                ]

                logger.info(f"从文本中成功抽取到 {len(relation_triplets)} 个关系")
                return relation_triplets
            else:
                logger.warning("Qwen API返回结果不包含有效关系信息")
                return []

        except Exception as e:
            logger.error(f"Qwen模型关系抽取失败: {str(e)}")
            # 发生错误时返回空列表
            return []
