import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi import HTTPException, Query
from neo4j import GraphDatabase, Session

from app.core.config import settings
from app.models import Task
from app.models.schema import (
    KGCreateRequest, KGCreateResponse,
    KGProgressResponse, KGQueryRequest, KGQueryResponse,
    KGListResponse
)
from app.service.kg_service import KGService
from app.utils.auth import get_current_active_user
from app.utils.db import get_db

router = APIRouter()
kg_service = KGService()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=KGCreateResponse)
async def create_knowledge_graph(
        request: KGCreateRequest,
        current_user: Dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """创建知识图谱"""
    logger.info(f"用户 {current_user['id']} 请求创建知识图谱: {request.kg_name}")

    # 验证文件ID列表不为空
    if not request.file_ids or len(request.file_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="请至少选择一个文件用于构建知识图谱"
        )

    try:
        task_id = kg_service.create_knowledge_graph(current_user["id"], request)
        return KGCreateResponse(
            success=True,
            task_id=task_id,
            message="知识图谱创建任务已提交"
        )
    except Exception as e:
        logger.error(f"创建知识图谱失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"创建知识图谱失败: {str(e)}"
        )


@router.get("/progress/{task_id}", response_model=KGProgressResponse)
async def get_kg_progress(
        task_id: str,
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> KGProgressResponse:  # 明确指定返回类型为响应模型
    """获取知识图谱构建进度（验证任务归属）"""
    # 验证任务是否属于当前用户
    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == current_user["id"]
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="任务不存在或无权访问"
        )

    logger.info(f"用户 {current_user['id']} 查询任务 {task_id} 进度")

    # 先从数据库获取进度
    progress_data = {
        "task_id": task_id,  # 确保包含task_id字段
        "progress": task.progress,
        "status": task.status,
        "message": task.message,
        "stage": task.stage,
        "kg_id": task.kg_id
    }

    # 如果任务正在处理中，从内存获取最新进度
    if task.status == "processing" and task_id in kg_service.task_progress:
        # 只更新需要的字段，保留task_id
        memory_progress = kg_service.task_progress[task_id].copy()
        progress_data.update({
            "progress": memory_progress.get("progress", progress_data["progress"]),
            "status": memory_progress.get("status", progress_data["status"]),
            "message": memory_progress.get("message", progress_data["message"]),
            "stage": memory_progress.get("stage", progress_data["stage"]),
            "kg_id": memory_progress.get("kg_id", progress_data["kg_id"])
        })

        # 更新数据库中的进度
        task.progress = progress_data["progress"]
        task.stage = progress_data["stage"]
        task.message = progress_data["message"]
        db.commit()

    # 直接返回响应模型实例，确保结构正确
    return KGProgressResponse(** progress_data)


@router.post("/query", response_model=KGQueryResponse)
async def query_knowledge_graph(
        query: KGQueryRequest,
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """查询知识图谱（验证权限）"""
    # 验证知识图谱是否存在且属于当前用户
    if not kg_service.verify_kg_ownership(
            db=db,
            kg_id=query.kg_id,
            user_id=current_user["id"]
    ):
        raise HTTPException(
            status_code=404,
            detail="知识图谱不存在或无权访问"
        )

    logger.info(f"用户 {current_user['id']} 查询知识图谱 {query.kg_id}: {query.entity}")
    try:
        result = kg_service.query_kg(current_user["id"], query.dict())
        return KGQueryResponse(**result)
    except Exception as e:
        logger.error(f"知识图谱查询失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询处理失败: {str(e)}"
        )

#相应前端知识图谱页面
@router.get("/list", response_model=KGListResponse)
async def list_knowledge_graphs(
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=10, le=100)
) -> Dict[str, Any]:
    """获取用户的知识图谱列表（带分页）"""
    skip = (page - 1) * page_size
    logger.info(f"用户 {current_user['id']} 获取知识图谱列表，分页: {page}/{page_size}")

    graphs, total = kg_service.get_kg_list(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=page_size
    )

    return {
        "graphs": graphs,  # 直接返回字典列表
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

# 可视化知识图谱
@router.get("/{kg_id}/visualize")
async def get_kg_visualization_data(
        kg_id: str,
        limit: int = Query(100, ge=1, le=500),
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """获取知识图谱可视化数据"""
    # 验证权限
    if not kg_service.verify_kg_ownership(db=db, kg_id=kg_id, user_id=current_user["id"]):
        raise HTTPException(status_code=404, detail="知识图谱不存在或无权访问")

    try:
        visualization_data = kg_service.get_visualization_data(kg_id, limit)
        return visualization_data
    except Exception as e:
        logger.error(f"获取可视化数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可视化数据失败: {str(e)}")

#图谱渲染接口

def get_neo4j_session() -> Session:
    # 初始化 Neo4j 连接
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    session = driver.session()
    try:
        yield session
    finally:
        session.close()

@router.get("/visualize/{kg_id}")
def visualize_knowledge_graph(kg_id: str, session: Session = Depends(get_neo4j_session)):
    """查询知识图谱的实体和关系，用于前端可视化"""
    # 示例：假设 kg_id 对应 Neo4j 中某类标签的节点（需根据业务调整）
    query = """
    MATCH (n)-[r]->(m) 
    WHERE n.kg_id = $kg_id OR m.kg_id = $kg_id
    RETURN n { .name, .type, id: id(n) } AS source, 
           r { .type, id: id(r) } AS relationship, 
           m { .name, .type, id: id(m) } AS target
    LIMIT 100  # 限制数量，避免前端渲染压力
    """
    result = session.run(query, kg_id=kg_id)
    # 格式化数据为前端可视化所需结构（节点列表 + 关系列表）
    nodes = []
    edges = []
    for record in result:
        source = record["source"]
        rel = record["relationship"]
        target = record["target"]
        # 去重添加节点
        if source not in nodes:
            nodes.append(source)
        if target not in nodes:
            nodes.append(target)
        edges.append({
            "source": source["id"],
            "target": target["id"],
            "type": rel["type"]
        })
    return {"nodes": nodes, "edges": edges}