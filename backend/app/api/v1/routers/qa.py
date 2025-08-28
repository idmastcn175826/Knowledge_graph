import logging
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from app.service.qa_service import QAService
from app.models.schema import QAQuery, QAAnswer, QAHistoryResponse
from app.utils.auth import get_current_user

router = APIRouter()
qa_service = QAService()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=QAAnswer)
async def chat(
    query: QAQuery,
    current_user: Dict = Depends(get_current_user)
):
    """与知识图谱进行对话"""
    logger.info(f"用户 {current_user['id']} 问答查询: {query.question}")
    answer = qa_service.get_answer(
        user_id=current_user["id"],
        question=query.question,
        kg_id=query.kg_id,
        model_api_key=query.model_api_key
    )
    return answer

@router.get("/history", response_model=QAHistoryResponse)
async def get_qa_history(
    kg_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user)
):
    """获取问答历史"""
    logger.info(f"用户 {current_user['id']} 获取问答历史，kg_id: {kg_id}, limit: {limit}, offset: {offset}")
    history = qa_service.get_history(
        user_id=current_user["id"],
        kg_id=kg_id,
        limit=limit,
        offset=offset
    )
    return QAHistoryResponse(history=history)
