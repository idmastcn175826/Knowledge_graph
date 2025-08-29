from .base import PreprocessStrategy
from typing import List
import hashlib
import numpy as np


class SimHashPreprocessor(PreprocessStrategy):
    """基于SimHash的文本预处理策略"""

    def process(self, text: str) -> str:
        """简单的文本清洗"""
        # 实际应用中可以添加更多清洗步骤：去除特殊字符、小写转换等
        return text.strip()

    def deduplicate(self, texts: List[str]) -> List[str]:
        """使用SimHash进行文本去重"""
        if not texts:
            return []

        # 计算每个文本的SimHash
        simhashes = [self._compute_simhash(text) for text in texts]

        # 筛选去重后的文本
        unique_texts = []
        unique_hashes = []

        for text, sh in zip(texts, simhashes):
            # 检查与已保留的哈希的相似度
            is_duplicate = False
            for existing_sh in unique_hashes:
                if self._hamming_distance(sh, existing_sh) <= 3:  # 阈值可调整
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_texts.append(text)
                unique_hashes.append(sh)

        return unique_texts

    def _compute_simhash(self, text: str) -> int:
        """计算文本的SimHash值"""
        # 简单分词（实际应用中可使用更复杂的分词工具）
        words = text.split()
        if not words:
            return 0

        # 计算每个词的权重（这里简单使用词频）
        word_weights = {}
        for word in words:
            word_weights[word] = word_weights.get(word, 0) + 1

        # 生成SimHash
        vector = [0] * 64
        for word, weight in word_weights.items():
            # 计算词的哈希值
            hash_val = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)

            # 更新向量
            for i in range(64):
                bit = (hash_val >> i) & 1
                vector[i] += weight if bit else -weight

        # 生成最终的SimHash值
        simhash = 0
        for i in range(64):
            if vector[i] > 0:
                simhash |= (1 << i)

        return simhash

    def _hamming_distance(self, hash1: int, hash2: int) -> int:
        """计算两个哈希值的汉明距离"""
        xor = hash1 ^ hash2
        return bin(xor).count('1')
