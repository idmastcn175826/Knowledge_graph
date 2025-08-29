import logging
import time
import uuid
from typing import List, Dict, Optional

import requests

from app.algorithm.extraction.factory import EntityExtractionFactory
from app.core.config import settings
from app.service.kg_service import KGService

logger = logging.getLogger(__name__)

class QAService:
    """问答服务类"""
    
    def __init__(self):
        self.kg_service = KGService()
        self.entity_extractor = EntityExtractionFactory.get_strategy("qwen")
        # 模拟存储问答历史
        self.qa_history = {}  # {user_id: [{id, question, answer, kg_id, timestamp}, ...]}
    
    def get_answer(self, user_id: str, question: str, kg_id: Optional[str] = None, 
                  model_api_key: Optional[str] = None) -> Dict:
        """
        获取问题答案
        
        Args:
            user_id: 用户ID
            question: 问题
            kg_id: 知识图谱ID，可选
            model_api_key: 模型API密钥，可选
            
        Returns:
            包含答案的字典
        """
        try:
            # 1. 从问题中提取实体
            entities = self.entity_extractor.extract(question)
            logger.info(f"从问题中提取实体: {entities}")
            
            # 2. 查询知识图谱获取相关信息
            kg_info = ""
            if entities:
                # 构建查询条件
                query = {}
                if entities:
                    query["entity"] = entities[0]["name"]
                
                # 查询知识图谱
                kg_result = self.kg_service.query_kg(user_id, query)
                kg_info = self._format_kg_info(kg_result)
                logger.info(f"知识图谱查询结果: {kg_info[:200]}...")
            
            # 3. 调用Qwen模型生成回答
            answer = self._call_qwen_model(question, kg_info, model_api_key)
            
            # 4. 保存问答历史
            self._save_history(user_id, question, answer, kg_id)
            
            return {
                "answer": answer,
                "related_entities": entities,
                "kg_used": bool(kg_info)
            }
            
        except Exception as e:
            logger.error(f"获取答案失败: {str(e)}", exc_info=True)
            return {
                "answer": f"抱歉，无法回答您的问题: {str(e)}",
                "related_entities": [],
                "kg_used": False
            }
    
    def _format_kg_info(self, kg_result: Dict) -> str:
        """格式化知识图谱信息为自然语言"""
        if not kg_result or not kg_result.get("nodes"):
            return ""
            
        info_parts = []
        nodes = {node["id"]: node for node in kg_result["nodes"]}
        
        for edge in kg_result.get("edges", []):
            source_id = edge["source"]
            target_id = edge["target"]
            relation = edge["type"]
            
            if source_id in nodes and target_id in nodes:
                source_name = nodes[source_id]["name"]
                target_name = nodes[target_id]["name"]
                info_parts.append(f"{source_name} {relation} {target_name}")
        
        # 如果没有关系，只返回实体信息
        if not info_parts:
            for node in kg_result["nodes"]:
                info_parts.append(f"存在实体: {node['name']}（{node['type']}）")
        
        return "; ".join(info_parts)
    
    def _call_qwen_model(self, question: str, context: str, api_key: Optional[str]) -> str:
        """调用Qwen模型生成回答"""
        api_key = api_key or settings.QWEN_DEFAULT_API_KEY
        
        if not api_key:
            raise ValueError("Qwen API密钥未配置，请提供API密钥")
        
        try:
            # 构建提示词
            prompt = f"基于以下信息回答问题。如果信息不足，可以基于你的知识回答，但要注明。\n"
            prompt += f"信息: {context}\n"
            prompt += f"问题: {question}\n"
            prompt += f"回答:"
            
            # 调用Qwen API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": "qwen-plus",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{settings.QWEN_API_BASE_URL}/chat/completions",
                headers=headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("choices") and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "无法生成回答，请稍后再试"
                
        except Exception as e:
            logger.error(f"调用Qwen模型失败: {str(e)}")
            raise
    
    def _save_history(self, user_id: str, question: str, answer: str, kg_id: Optional[str]):
        """保存问答历史"""
        if user_id not in self.qa_history:
            self.qa_history[user_id] = []
            
        self.qa_history[user_id].append({
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer,
            "kg_id": kg_id,
            "timestamp": int(time.time())
        })
        
        # 限制历史记录数量
        if len(self.qa_history[user_id]) > 1000:
            self.qa_history[user_id] = self.qa_history[user_id][-1000:]
    
    def get_history(self, user_id: str, kg_id: Optional[str] = None, 
                   limit: int = 20, offset: int = 0) -> List[Dict]:
        """获取问答历史"""
        if user_id not in self.qa_history:
            return []
            
        # 筛选指定知识图谱的历史
        history = self.qa_history[user_id]
        if kg_id:
            history = [h for h in history if h["kg_id"] == kg_id]
        
        # 按时间倒序排列
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 分页
        return history[offset:offset+limit]
