import logging
from typing import List, Dict

import torch
from transformers import BertTokenizer, BertForTokenClassification

from app.algorithm.extraction.base import EntityExtractionStrategy

logger = logging.getLogger(__name__)

class BERTEntityExtraction(EntityExtractionStrategy):
    """基于BERT的实体抽取策略"""
    
    def __init__(self):
        """初始化BERT模型和分词器"""
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        self.model = BertForTokenClassification.from_pretrained("ckiplab/bert-base-chinese-ner")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # 标签映射
        self.label_map = {
            0: "O",      # 非实体
            1: "B-PER",  # 人物开始
            2: "I-PER",  # 人物中间
            3: "B-ORG",  # 组织开始
            4: "I-ORG",  # 组织中间
            5: "B-LOC",  # 地点开始
            6: "I-LOC"   # 地点中间
        }
        
        # 实体类型映射
        self.entity_type_map = {
            "PER": "人物",
            "ORG": "组织",
            "LOC": "地点"
        }
        
        logger.info("BERT实体抽取模型初始化完成")
    
    def extract(self, text: str) -> List[Dict]:
        """
        使用BERT模型从文本中抽取实体
        
        Args:
            text: 待处理的文本
            
        Returns:
            实体列表，每个实体包含id、name、type等信息
        """
        if not text:
            return []
            
        # 文本分词
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 模型预测
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        # 处理预测结果
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        labels = [self.label_map[p.item()] for p in predictions[0]]
        
        # 提取实体
        entities = []
        current_entity = None
        current_type = None
        
        for token, label in zip(tokens, labels):
            # 跳过特殊标记
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
                
            # 处理子词
            if token.startswith("##"):
                token = token[2:]
                if current_entity is not None:
                    current_entity += token
                continue
                
            # 开始新实体
            if label.startswith("B-"):
                # 如果有当前实体，先保存
                if current_entity is not None:
                    entities.append({
                        "name": current_entity,
                        "type": self.entity_type_map[current_type]
                    })
                
                current_type = label[2:]
                current_entity = token
                
            # 实体中间部分
            elif label.startswith("I-") and current_entity is not None:
                current_entity += token
                
            # 非实体或实体结束
            else:
                if current_entity is not None:
                    entities.append({
                        "name": current_entity,
                        "type": self.entity_type_map[current_type]
                    })
                    current_entity = None
                    current_type = None
        
        # 处理最后一个实体
        if current_entity is not None:
            entities.append({
                "name": current_entity,
                "type": self.entity_type_map[current_type]
            })
        
        # 为实体添加唯一ID
        for i, entity in enumerate(entities):
            entity["id"] = f"entity_{i}_{entity['name']}"
            
        logger.info(f"BERT实体抽取完成，共抽取{len(entities)}个实体")
        return entities
