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
        """调用Qwen模型生成回答（优化版：修复URL拼接+增强异常处理）"""
        # 1. 优先使用请求传入的api_key，其次用配置的默认密钥
        api_key = api_key or settings.QWEN_DEFAULT_API_KEY

        # 2. 校验API密钥（确保非空）
        if not api_key:
            error_msg = "Qwen API密钥未配置，请在请求中传入model_api_key或在.env中设置QWEN_DEFAULT_API_KEY"
            logger.error(error_msg)
            raise ValueError(error_msg)  # 抛出明确错误，便于上层捕获

        # 3. 校验Qwen API地址（避免空地址导致请求失败）
        if not settings.QWEN_API_BASE_URL:
            error_msg = "Qwen API地址未配置，请在.env中设置QWEN_API_BASE_URL（格式：https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions）"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # 4. 构建提示词（优化格式：避免上下文过长导致模型混淆）
            prompt = (
                "基于以下信息回答用户问题，需遵循以下规则：\n"
                "1. 优先使用提供的信息，信息不足时可补充你的知识，但必须注明「信息不足，基于现有知识回答：」；\n"
                "2. 回答需简洁准确，避免冗余；\n"
                "3. 若信息与你的知识冲突，以提供的信息为准，并注明「基于提供的信息回答：」。\n\n"
                f"提供的信息：{context}\n\n"
                f"用户问题：{question}\n\n"
                "回答："
            )

            # 5. 构建API请求参数（适配Qwen API规范）
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"  # 正确的Bearer Token格式
            }

            # Qwen API请求体（严格遵循官方规范，避免多余字段）
            data = {
                "model": settings.QWEN_MODEL_NAME or "qwen-plus",  # 优先用配置的模型名，兜底用qwen-plus
                "messages": [{"role": "user", "content": prompt}],  # 标准user角色消息
                "temperature": 0.7,  # 保持原有温度，控制回答随机性
                "max_tokens": 2048  # 新增：限制最大生成token数，避免超长回答（可选，根据需求调整）
            }

            # 6. 发送API请求（关键：删除多余的/chat/completions拼接）
            response = requests.post(
                url=settings.QWEN_API_BASE_URL,  # 直接使用配置的完整地址，不额外拼接
                headers=headers,
                json=data,
                timeout=30  # 新增：设置30秒超时，避免请求挂起（重要！）
            )

            # 7. 处理HTTP错误（如401未授权、403无权限、429限流等）
            response.raise_for_status()  # 若状态码≥400，直接抛出HTTPError

            # 8. 解析API响应（兼容Qwen API返回格式）
            result = response.json()
            # 检查响应结构是否正确
            if not result.get("choices") or len(result["choices"]) == 0:
                logger.warning("Qwen API返回空结果，可能是模型无响应")
                return "无法生成回答，请稍后再试（模型返回空结果）"

            # 提取回答内容（处理可能的空字符串）
            answer = result["choices"][0]["message"].get("content", "").strip()
            if not answer:
                logger.warning("Qwen API返回空回答内容")
                return "无法生成回答，请稍后再试（模型返回空内容）"

            return answer

        # 9. 分类捕获异常，返回明确错误信息
        except requests.exceptions.Timeout:
            error_msg = "调用Qwen模型超时（超过30秒），请检查网络或稍后重试"
            logger.error(error_msg)
            raise ValueError(error_msg)

        except requests.exceptions.ConnectionError:
            error_msg = "调用Qwen模型失败，网络连接异常（如API地址不可达）"
            logger.error(error_msg)
            raise ValueError(error_msg)

        except requests.exceptions.HTTPError as e:
            # 处理具体HTTP错误（如401：密钥无效，429：限流）
            status_code = e.response.status_code if e.response else None
            if status_code == 401:
                error_msg = "Qwen API密钥无效或过期，请检查API密钥配置"
            elif status_code == 403:
                error_msg = "无权限调用Qwen模型，可能是密钥权限不足或模型未开通"
            elif status_code == 429:
                error_msg = "Qwen模型调用频率超限，请稍后再试"
            else:
                error_msg = f"调用Qwen模型失败（HTTP错误 {status_code}）：{str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        except Exception as e:
            # 捕获其他未知异常
            error_msg = f"调用Qwen模型失败：{str(e)}"
            logger.error(error_msg, exc_info=True)  # 打印堆栈信息，便于调试
            raise ValueError(error_msg)
    
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
