import logging
from datetime import time, datetime
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge_graphs import KnowledgeGraph
from app.models.schema import QAQuery, QAAnswer, QAHistoryResponse, QAHistoryItem
from app.service.qa_service import QAService
from app.utils.auth import get_current_active_user
from app.utils.db import get_db


router = APIRouter()

qa_service = QAService()
logger = logging.getLogger(__name__)

@router.get("/test")
async def qa_test():
    return {"message": "qa 路由测试成功", "status": "ok"}

@router.post("/chat", response_model=QAAnswer)
async def chat(
        query: QAQuery,
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """与知识图谱进行对话（带权限验证）"""
    # 1. 验证知识图谱权限（修正 kg_id 字段匹配）
    if query.kg_id:
        kg = db.query(KnowledgeGraph).filter(
            KnowledgeGraph.kg_id == query.kg_id,  # 匹配数据库的 kg_id 字段
            KnowledgeGraph.user_id == current_user["id"]
        ).first()
        if not kg:
            raise HTTPException(
                status_code=403,
                detail="知识图谱不存在或无权访问"
            )

    try:
        # # 新增：提前校验 API 密钥（避免调用模型时才报错）
        # if not (query.model_api_key or settings.QWEN_DEFAULT_API_KEY):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Qwen API 密钥未配置，请在请求中传入 model_api_key 或在系统设置中配置默认密钥"
        #     )
        logger.info(f"用户 {current_user['id']} 问答查询: {query.question} (KG: {query.kg_id or 'None'})")
        service_result = qa_service.get_answer(
            user_id=current_user["id"],
            question=query.question,
            kg_id=query.kg_id,
            model_api_key=query.model_api_key
        )

        # 2. 严格按照 QAAnswer 模型格式组装响应
        return QAAnswer(
            kg_id=query.kg_id,  # 回传请求的 kg_id
            question=query.question,  # 回传问题
            answer=service_result["answer"],  # 服务层返回的答案
            confidence=0.0,  # 服务层未实现，用默认值
            related_entities=service_result["related_entities"],  # 服务层返回的实体
            related_relations=[],  # 服务层未返回，用空列表
            reasoning_steps=[],  # 服务层未返回，用空列表
            response_time=0,  # 服务层未记录，用默认值
            session_id=query.session_id,  # 回传请求的 session_id
            timestamp=datetime.utcnow().isoformat() + "Z"  # 生成 UTC 时间戳
        )

    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"处理查询失败: {str(e)}"
        )

@router.get("/history", response_model=QAHistoryResponse, summary="获取用户的问答历史记录")
async def get_qa_history(
        kg_id: Optional[str] = Query(None, description="可选，按知识图谱ID筛选历史"),
        limit: int = Query(20, ge=1, le=100, description="每页条数，最大100"),
        offset: int = Query(0, ge=0, description="分页偏移量，从0开始"),
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取当前登录用户的问答历史，适配QAService的内存存储结构
    """
    # 1. 验证知识图谱权限（若传入kg_id）
    if kg_id:
        kg = db.query(KnowledgeGraph).filter(
            KnowledgeGraph.kg_id == kg_id,
            KnowledgeGraph.user_id == current_user["id"]
        ).first()
        if not kg:
            raise HTTPException(
                status_code=403,
                detail=f"知识图谱 {kg_id} 不存在或无访问权限"
            )

    # 2. 调用QAService获取历史数据
    try:
        # 从服务层获取分页历史（你的QAService返回的是List[Dict]）
        raw_history: List[Dict] = qa_service.get_history(
            user_id=current_user["id"],
            kg_id=kg_id,
            limit=limit,
            offset=offset
        )

        # 计算总条数（基于QAService的实现，需要重新查询全量数据）
        total = len(qa_service.get_history(
            user_id=current_user["id"],
            kg_id=kg_id,
            limit=10000,  # 超出实际存储上限的大值
            offset=0
        ))

        # 3. 格式化数据为模型要求的结构
        formatted_history: List[QAHistoryItem] = []
        for item in raw_history:
            iso_timestamp = datetime.utcfromtimestamp(item["timestamp"]).isoformat() + "Z"
            formatted_history.append(QAHistoryItem(
                query=QAQuery(
                    kg_id=item["kg_id"],
                    question=item["question"],
                    top_k=5,  # 与模型默认值一致
                    use_context=True,
                    session_id=item.get("session_id"),
                    model_api_key=None  # 历史记录无需该字段
                ),
                answer=QAAnswer(
                    kg_id=item["kg_id"],
                    question=item["question"],
                    answer=item["answer"],
                    confidence=0.0,
                    related_entities=[],
                    related_relations=[],
                    reasoning_steps=[],
                    response_time=0,
                    session_id=item.get("session_id"),
                    timestamp=iso_timestamp
                ),
                timestamp=iso_timestamp
            ))

        # 4. 组装最终响应
        return QAHistoryResponse(
            kg_id=kg_id,
            session_id=None,
            history=formatted_history,
            total=total,
            page=offset // limit + 1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"获取历史失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取问答历史失败：{str(e)}"
        )
