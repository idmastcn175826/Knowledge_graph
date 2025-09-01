import logging
import string
from typing import List, Dict, Tuple

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class EntityAlignment:
    """实体对齐工具类，用于识别并合并相同或相似的实体"""

    def __init__(self, threshold: float = 0.8):
        """
        初始化实体对齐工具

        Args:
            threshold: 相似度阈值，超过此值的实体将被认为是相同实体
        """
        self.threshold = threshold
        self.merged_entities = {}  # 记录合并后的实体映射关系

    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理，用于提高相似度计算准确性

        Args:
            text: 原始文本

        Returns:
            预处理后的文本
        """
        # 转换为小写
        text = text.lower()
        # 移除标点符号
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        # 去除多余空格
        text = ' '.join(text.split())
        return text

    def _calculate_similarity(self, entity1: Dict, entity2: Dict) -> float:
        """
        计算两个实体的相似度

        Args:
            entity1: 第一个实体
            entity2: 第二个实体

        Returns:
            相似度分数，范围0-1
        """
        # 1. 名称相似度
        name1 = self._preprocess_text(entity1['name'])
        name2 = self._preprocess_text(entity2['name'])

        # 使用模糊匹配计算名称相似度
        name_similarity = fuzz.ratio(name1, name2) / 100.0

        # 如果名称完全相同，直接返回高相似度
        if name_similarity == 1.0:
            return 1.0

        # 2. 类型相似度
        type_similarity = 1.0 if entity1.get('type') == entity2.get('type') else 0.5

        # 3. 综合相似度（加权平均）
        final_similarity = (name_similarity * 0.7) + (type_similarity * 0.3)

        return final_similarity

    def align_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        对实体列表进行对齐，合并相似实体

        Args:
            entities: 待对齐的实体列表

        Returns:
            对齐后的实体列表，相似实体已被合并
        """
        if not entities or len(entities) <= 1:
            return entities

        # 重置合并记录
        self.merged_entities = {}
        aligned_entities = []
        processed_indices = set()

        # 遍历所有实体对，寻找相似实体
        for i in range(len(entities)):
            if i in processed_indices:
                continue

            current_entity = entities[i].copy()
            merged_ids = [current_entity['id']]

            # 与其他实体比较
            for j in range(i + 1, len(entities)):
                if j in processed_indices:
                    continue

                similarity = self._calculate_similarity(current_entity, entities[j])

                if similarity >= self.threshold:
                    # 标记为已处理
                    processed_indices.add(j)
                    # 记录合并关系
                    self.merged_entities[entities[j]['id']] = current_entity['id']
                    merged_ids.append(entities[j]['id'])

                    # 合并实体信息（取最长的名称）
                    if len(entities[j]['name']) > len(current_entity['name']):
                        current_entity['name'] = entities[j]['name']

                    # 合并其他属性
                    for key, value in entities[j].items():
                        if key not in current_entity:
                            current_entity[key] = value

            # 记录合并的ID
            current_entity['merged_ids'] = merged_ids
            aligned_entities.append(current_entity)
            processed_indices.add(i)

        logger.info(f"实体对齐完成：{len(entities)} 个原始实体 -> {len(aligned_entities)} 个对齐实体")
        return aligned_entities

    def adjust_relations(self, relations: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """
        根据实体对齐结果调整关系，更新已合并实体的ID

        Args:
            relations: 原始关系列表

        Returns:
            调整后的关系列表
        """
        if not relations or not self.merged_entities:
            return relations

        adjusted_relations = []
        relation_set = set()

        for rel in relations:
            entity1_id, relation_type, entity2_id = rel

            # 替换已合并的实体ID
            adjusted_entity1_id = self.merged_entities.get(entity1_id, entity1_id)
            adjusted_entity2_id = self.merged_entities.get(entity2_id, entity2_id)

            # 避免重复关系
            relation_tuple = (adjusted_entity1_id, relation_type, adjusted_entity2_id)
            if relation_tuple not in relation_set:
                relation_set.add(relation_tuple)
                adjusted_relations.append(relation_tuple)

        return adjusted_relations
