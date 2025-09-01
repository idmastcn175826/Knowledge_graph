from .base import PreprocessStrategy
from typing import List, Tuple
import hashlib
import random


class MinHashPreprocessor(PreprocessStrategy):
    """基于MinHash的文本预处理策略"""

    def __init__(self, num_perm: int = 128):
        self.num_perm = num_perm
        self.permutations = self._generate_permutations()

    def process(self, text: str) -> str:
        """简单的文本清洗"""
        return text.strip()

    def deduplicate(self, texts: List[str], threshold: float = 0.7) -> List[str]:
        """使用MinHash进行文本去重"""
        if not texts:
            return []

        # 计算每个文本的MinHash签名
        signatures = [self._compute_minhash(text) for text in texts]

        # 筛选去重后的文本
        unique_texts = []
        unique_signatures = []

        for text, sig in zip(texts, signatures):
            # 检查与已保留的签名的相似度
            is_duplicate = False
            for existing_sig in unique_signatures:
                if self._jaccard_similarity(sig, existing_sig) >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_texts.append(text)
                unique_signatures.append(sig)

        return unique_texts

    def _generate_permutations(self) -> List[Tuple[int, int]]:
        """生成随机置换参数"""
        return [(random.randint(1, 1000000), random.randint(0, 1000000)) for _ in range(self.num_perm)]

    def _compute_minhash(self, text: str) -> List[int]:
        """计算文本的MinHash签名"""
        # 简单分词
        words = set(text.split())  # 使用集合获取唯一词
        if not words:
            return [0] * self.num_perm

        # 计算每个词的哈希值
        word_hashes = []
        for word in words:
            hash_val = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16) % (10 ** 18)
            word_hashes.append(hash_val)

        # 计算MinHash签名
        signature = []
        for a, b in self.permutations:
            min_hash = min((a * h + b) % (10 ** 18) for h in word_hashes)
            signature.append(min_hash)

        return signature

    def _jaccard_similarity(self, sig1: List[int], sig2: List[int]) -> float:
        """计算两个签名的Jaccard相似度"""
        if len(sig1) != len(sig2):
            return 0.0

        matches = sum(1 for s1, s2 in zip(sig1, sig2) if s1 == s2)
        return matches / len(sig1)
