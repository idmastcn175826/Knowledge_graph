import numpy as np
import os
import pickle
from typing import List, Tuple, Dict, Optional
import logging
from .base import KnowledgeCompletionStrategy

logger = logging.getLogger(__name__)


class TransEKnowledgeCompletion(KnowledgeCompletionStrategy):
    """基于TransE算法的知识补全策略实现"""

    def __init__(self, embedding_dim: int = 50, margin: float = 1.0, learning_rate: float = 0.01):
        """
        初始化TransE模型

        Args:
            embedding_dim: 嵌入维度
            margin: 边际参数，用于计算损失
            learning_rate: 学习率
        """
        self.embedding_dim = embedding_dim
        self.margin = margin
        self.learning_rate = learning_rate

        # 实体和关系的嵌入
        self.entity_embeddings = {}  # {entity_id: np.array}
        self.relation_embeddings = {}  # {relation_type: np.array}

        # 实体和关系的集合
        self.entities = set()
        self.relations = set()

        # 模型是否已训练
        self.is_trained = False

    def _initialize_embeddings(self) -> None:
        """初始化实体和关系的嵌入向量"""
        # 初始化实体嵌入
        for entity_id in self.entities:
            self.entity_embeddings[entity_id] = np.random.uniform(
                low=-6 / np.sqrt(self.embedding_dim),
                high=6 / np.sqrt(self.embedding_dim),
                size=self.embedding_dim
            )
            # L2归一化
            self.entity_embeddings[entity_id] /= np.linalg.norm(
                self.entity_embeddings[entity_id]
            )

        # 初始化关系嵌入
        for relation in self.relations:
            self.relation_embeddings[relation] = np.random.uniform(
                low=-6 / np.sqrt(self.embedding_dim),
                high=6 / np.sqrt(self.embedding_dim),
                size=self.embedding_dim
            )
            # L2归一化
            self.relation_embeddings[relation] /= np.linalg.norm(
                self.relation_embeddings[relation]
            )

    def _generate_negative_sample(self, positive_sample: Tuple[str, str, str]) -> Tuple[str, str, str]:
        """生成负样本"""
        head, relation, tail = positive_sample

        # 随机选择替换头实体或尾实体
        if np.random.rand() < 0.5:
            # 替换头实体
            new_head = head
            while new_head == head:
                new_head = np.random.choice(list(self.entities))
            return (new_head, relation, tail)
        else:
            # 替换尾实体
            new_tail = tail
            while new_tail == tail:
                new_tail = np.random.choice(list(self.entities))
            return (head, relation, new_tail)

    def train(self, relations: List[Tuple[str, str, str]], epochs: int = 100) -> None:
        """
        训练TransE模型

        Args:
            relations: 关系三元组列表
            epochs: 训练轮数
        """
        if not relations:
            logger.warning("没有关系数据可用于训练TransE模型")
            return

        # 收集所有实体和关系
        self.entities = set()
        self.relations = set()

        for head, relation, tail in relations:
            self.entities.add(head)
            self.entities.add(tail)
            self.relations.add(relation)

        # 初始化嵌入
        self._initialize_embeddings()

        # 开始训练
        for epoch in range(epochs):
            total_loss = 0.0

            for positive in relations:
                # 生成负样本
                negative = self._generate_negative_sample(positive)

                # 获取嵌入向量
                h_pos = self.entity_embeddings[positive[0]]
                r_pos = self.relation_embeddings[positive[1]]
                t_pos = self.entity_embeddings[positive[2]]

                h_neg = self.entity_embeddings[negative[0]]
                r_neg = self.relation_embeddings[negative[1]]
                t_neg = self.entity_embeddings[negative[2]]

                # 计算得分
                score_pos = np.linalg.norm(h_pos + r_pos - t_pos)
                score_neg = np.linalg.norm(h_neg + r_neg - t_neg)

                # 计算损失
                loss = max(0, self.margin + score_pos - score_neg)
                total_loss += loss

                if loss > 0:
                    # 计算梯度并更新
                    grad_h_pos = 2 * (h_pos + r_pos - t_pos)
                    grad_r_pos = 2 * (h_pos + r_pos - t_pos)
                    grad_t_pos = -2 * (h_pos + r_pos - t_pos)

                    grad_h_neg = -2 * (h_neg + r_neg - t_neg)
                    grad_r_neg = -2 * (h_neg + r_neg - t_neg)
                    grad_t_neg = 2 * (h_neg + r_neg - t_neg)

                    # 更新嵌入
                    self.entity_embeddings[positive[0]] -= self.learning_rate * grad_h_pos
                    self.relation_embeddings[positive[1]] -= self.learning_rate * grad_r_pos
                    self.entity_embeddings[positive[2]] -= self.learning_rate * grad_t_pos

                    self.entity_embeddings[negative[0]] -= self.learning_rate * grad_h_neg
                    self.relation_embeddings[negative[1]] -= self.learning_rate * grad_r_neg
                    self.entity_embeddings[negative[2]] -= self.learning_rate * grad_t_neg

                    # 重新归一化
                    self.entity_embeddings[positive[0]] /= np.linalg.norm(
                        self.entity_embeddings[positive[0]]
                    )
                    self.relation_embeddings[positive[1]] /= np.linalg.norm(
                        self.relation_embeddings[positive[1]]
                    )
                    self.entity_embeddings[positive[2]] /= np.linalg.norm(
                        self.entity_embeddings[positive[2]]
                    )

                    self.entity_embeddings[negative[0]] /= np.linalg.norm(
                        self.entity_embeddings[negative[0]]
                    )
                    self.relation_embeddings[negative[1]] /= np.linalg.norm(
                        self.relation_embeddings[negative[1]]
                    )
                    self.entity_embeddings[negative[2]] /= np.linalg.norm(
                        self.entity_embeddings[negative[2]]
                    )

            if (epoch + 1) % 10 == 0:
                logger.info(f"TransE训练 epoch {epoch + 1}/{epochs}, 损失: {total_loss:.4f}")

        self.is_trained = True
        logger.info("TransE模型训练完成")

    def complete(self,
                 entities: List[Dict],
                 relations: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """
        补全知识图谱中可能缺失的关系

        Args:
            entities: 实体列表
            relations: 已有的关系三元组列表

        Returns:
            补全的关系三元组列表
        """
        if not self.is_trained:
            # 如果模型未训练，则先进行训练
            self.train(relations)

        # 收集所有实体ID
        entity_ids = [entity['id'] for entity in entities]
        if not entity_ids:
            return []

        # 存储已有的关系，避免重复
        existing_relations = set(relations)

        # 补全的关系
        completed_relations = []

        # 对每种关系类型进行补全
        for relation in self.relations:
            # 对每个实体作为头实体，预测可能的尾实体
            for head in entity_ids:
                if head not in self.entity_embeddings:
                    continue

                # 计算头实体+关系的嵌入
                h = self.entity_embeddings[head]
                r = self.relation_embeddings.get(relation, None)
                if r is None:
                    continue

                hr = h + r

                # 计算与所有实体的相似度
                similarities = {}
                for tail in entity_ids:
                    if tail == head or (head, relation, tail) in existing_relations:
                        continue

                    if tail not in self.entity_embeddings:
                        continue

                    t = self.entity_embeddings[tail]
                    # 计算距离（距离越小越相似）
                    distance = np.linalg.norm(hr - t)
                    similarities[tail] = distance

                # 取最相似的前3个实体作为补全结果
                sorted_tails = sorted(similarities.items(), key=lambda x: x[1])[:3]
                for tail, _ in sorted_tails:
                    completed_relations.append((head, relation, tail))

        logger.info(f"知识补全完成，新增 {len(completed_relations)} 个关系")
        return completed_relations

    def save_model(self, path: str) -> None:
        """保存模型到指定路径"""
        try:
            model_data = {
                'entity_embeddings': self.entity_embeddings,
                'relation_embeddings': self.relation_embeddings,
                'entities': self.entities,
                'relations': self.relations,
                'embedding_dim': self.embedding_dim,
                'margin': self.margin,
                'learning_rate': self.learning_rate,
                'is_trained': self.is_trained
            }

            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"TransE模型已保存到 {path}")
        except Exception as e:
            logger.error(f"保存TransE模型失败: {str(e)}")

    def load_model(self, path: str) -> None:
        """从指定路径加载模型"""
        try:
            if not os.path.exists(path):
                logger.warning(f"TransE模型文件不存在: {path}")
                return

            with open(path, 'rb') as f:
                model_data = pickle.load(f)

            self.entity_embeddings = model_data['entity_embeddings']
            self.relation_embeddings = model_data['relation_embeddings']
            self.entities = model_data['entities']
            self.relations = model_data['relations']
            self.embedding_dim = model_data['embedding_dim']
            self.margin = model_data['margin']
            self.learning_rate = model_data['learning_rate']
            self.is_trained = model_data['is_trained']

            logger.info(f"TransE模型已从 {path} 加载")
        except Exception as e:
            logger.error(f"加载TransE模型失败: {str(e)}")
