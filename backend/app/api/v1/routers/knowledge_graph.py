import logging
from typing import Dict

from fastapi import APIRouter, Depends

from app.models.schema import (
    KGCreateRequest, KGCreateResponse,
    KGProgressResponse, KGQueryRequest, KGQueryResponse
)
from app.service.kg_service import KGService
from app.utils.auth import get_current_user

router = APIRouter()
kg_service = KGService()
logger = logging.getLogger(__name__)

@router.post("/create", response_model=KGCreateResponse)
async def create_knowledge_graph(
    request: KGCreateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """创建知识图谱"""
    logger.info(f"用户 {current_user['id']} 请求创建知识图谱: {request.dict()}")
    task_id = kg_service.create_knowledge_graph(current_user["id"], request)
    return KGCreateResponse(task_id=task_id)

@router.get("/progress/{task_id}", response_model=KGProgressResponse)
async def get_kg_progress(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """获取知识图谱构建进度"""
    logger.info(f"用户 {current_user['id']} 查询任务 {task_id} 进度")
    return kg_service.get_progress(task_id)

@router.post("/query", response_model=KGQueryResponse)
async def query_knowledge_graph(
    query: KGQueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """查询知识图谱"""
    logger.info(f"用户 {current_user['id']} 查询知识图谱: {query.dict()}")
    result = kg_service.query_kg(current_user["id"], query.dict())
    return KGQueryResponse(**result)

@router.get("/list")
async def list_knowledge_graphs(
    current_user: Dict = Depends(get_current_user)
):
    """获取用户的知识图谱列表"""
    logger.info(f"用户 {current_user['id']} 获取知识图谱列表")
    # 实际实现中应该从数据库查询用户的知识图谱列表
    return {
        "graphs": [
            {
                "id": "kg_123",
                "name": "我的第一个知识图谱",
                "created_at": "2023-11-01T10:00:00Z",
                "entity_count": 120,
                "relation_count": 250
            },
            {
                "id": "kg_456",
                "name": "技术文档知识图谱",
                "created_at": "2023-11-05T14:30:00Z",
                "entity_count": 350,
                "relation_count": 580
            }
        ]
    }
