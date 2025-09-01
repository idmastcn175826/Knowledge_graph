import os
import pickle
from typing import List, Dict

import sklearn_crfsuite

from app.algorithm.extraction.base import EntityExtractionStrategy
from app.config.config import settings


class CRFEntityExtraction(EntityExtractionStrategy):
    """基于条件随机场(CRF)的实体抽取策略实现"""

    def __init__(self):
        """初始化CRF模型，尝试加载预训练模型，若无则初始化新模型"""
        self.model = None
        self.model_path = os.path.join(settings.temp_dir, "crf_entity_model.pkl")
        self._load_model()

        # 如果没有预训练模型，初始化新的CRF模型
        if self.model is None:
            self.model = sklearn_crfsuite.CRF(
                algorithm='lbfgs',
                c1=0.1,
                c2=0.1,
                max_iterations=100,
                all_possible_transitions=True
            )

    def _load_model(self) -> None:
        """加载预训练的CRF模型"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
        except Exception as e:
            print(f"加载CRF模型失败: {e}，将使用新模型")
            self.model = None

    def _save_model(self) -> None:
        """保存训练好的CRF模型"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
        except Exception as e:
            print(f"保存CRF模型失败: {e}")

    def _word2features(self, sent: List[str], i: int) -> Dict:
        """
        将词语转换为特征

        Args:
            sent: 句子的词语列表
            i: 当前词语的索引

        Returns:
            特征字典
        """
        word = sent[i]
        features = {
            'bias': 1.0,
            'word.lower()': word.lower(),
            'word[-3:]': word[-3:],
            'word[-2:]': word[-2:],
            'word.isupper()': word.isupper(),
            'word.istitle()': word.istitle(),
            'word.isdigit()': word.isdigit(),
        }
        if i > 0:
            word1 = sent[i - 1]
            features.update({
                '-1:word.lower()': word1.lower(),
                '-1:word.istitle()': word1.istitle(),
                '-1:word.isupper()': word1.isupper(),
            })
        else:
            features['BOS'] = True  # 句首标记

        if i < len(sent) - 1:
            word1 = sent[i + 1]
            features.update({
                '+1:word.lower()': word1.lower(),
                '+1:word.istitle()': word1.istitle(),
                '+1:word.isupper()': word1.isupper(),
            })
        else:
            features['EOS'] = True  # 句尾标记

        return features

    def _sent2features(self, sent: List[str]) -> List[Dict]:
        """
        将句子转换为特征列表

        Args:
            sent: 句子的词语列表

        Returns:
            特征列表
        """
        return [self._word2features(sent, i) for i in range(len(sent))]

    def train(self, X_train: List[List[str]], y_train: List[List[str]]) -> None:
        """
        训练CRF模型

        Args:
            X_train: 训练数据的句子列表
            y_train: 训练数据的标签列表
        """
        X_features = [self._sent2features(sent) for sent in X_train]
        self.model.fit(X_features, y_train)
        self._save_model()

    def extract(self, text: str) -> List[Dict]:
        """
        从文本中抽取实体

        Args:
            text: 待处理的文本

        Returns:
            实体列表，每个实体包含id、name、type等信息
        """
        # 简单分词（实际应用中应使用更专业的分词工具如jieba）
        words = text.split()
        if not words:
            return []

        # 提取特征并预测
        features = self._sent2features(words)
        labels = self.model.predict([features])[0]

        # 解析预测结果，提取实体
        entities = []
        current_entity = None
        entity_id = 1

        for i, (word, label) in enumerate(zip(words, labels)):
            # 标签格式：B-实体类型 表示实体开始，I-实体类型 表示实体内部
            if label.startswith('B-'):
                # 如果有当前实体，先保存
                if current_entity:
                    entities.append(current_entity)

                entity_type = label[2:]
                current_entity = {
                    'id': f'entity_{entity_id}',
                    'name': word,
                    'type': entity_type,
                    'start_pos': i,
                    'end_pos': i
                }
                entity_id += 1
            elif label.startswith('I-') and current_entity:
                # 实体内部，继续拼接
                entity_type = label[2:]
                if entity_type == current_entity['type']:
                    current_entity['name'] += ' ' + word
                    current_entity['end_pos'] = i

        # 添加最后一个实体
        if current_entity:
            entities.append(current_entity)

        return entities
