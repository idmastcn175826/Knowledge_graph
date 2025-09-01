import logging
import time
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi import HTTPException, Query
from neo4j import GraphDatabase, Session

from app.config.config import settings
from app.models import Task
from app.models.schema import (
    KGCreateRequest, KGCreateResponse,
    KGProgressResponse, KGQueryRequest, KGQueryResponse,
    KGListResponse
)
from app.models.user import User
from app.service.kg_service import KGService
from app.utils.auth import get_current_active_user, get_current_user
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

    logger.info(f"用户 {current_user['id']} 查询知识图谱 {query.kg_id}: {query.query}")
    try:
        # 记录查询开始时间（使用标准库time模块）
        start_time = time.time()  # 现在这行代码会正常工作

        # 调用查询服务
        result = kg_service.query_kg(current_user["id"], query.dict())

        # 补全必填字段
        result.setdefault("kg_id", query.kg_id)
        result.setdefault("query", query.query)
        result.setdefault("total", 0)
        # 计算执行时间（当前时间 - 开始时间）
        result.setdefault("execution_time", round(time.time() - start_time, 2))

        # 统计total：实体数 + 关系数
        entities_count = len(result.get("entities", []))
        relations_count = len(result.get("relations", []))
        result["total"] = entities_count + relations_count

        # 兜底可选字段
        result.setdefault("entities", [])
        result.setdefault("relations", [])
        result.setdefault("results", [])
        result.setdefault("answer", "")
        result.setdefault("message", "查询成功")

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
    # logger.info(f"用户 {current_user['id']} 获取知识图谱列表，分页: {page}/{page_size}")

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
@router.get("/{kg_id}/visualize", summary="获取知识图谱可视化数据（唯一接口）")
async def get_kg_visualization_data(
        kg_id: str,
        limit: int = Query(100, ge=1, le=500),  # 限制最大返回数量，避免前端卡顿
        current_user: Dict = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    修复点：
    1. 删除重复的 /visualize/{kg_id} 接口，保留此唯一接口
    2. 补全 get_visualization_data 的 user_id 参数（与 KGService 方法匹配）
    3. 复用 KGService 中的 Neo4j 连接和数据处理逻辑
    """
    # 1. 权限校验（确保用户只能查看自己的图谱）
    if not kg_service.verify_kg_ownership(db=db, kg_id=kg_id, user_id=current_user["id"]):
        logger.warning(f"用户 {current_user['id']} 无权访问图谱 {kg_id}")
        raise HTTPException(status_code=403, detail="知识图谱不存在或无权访问")  # 403更符合权限拒绝语义

    try:
        # 2. 调用服务层方法（关键：补全 user_id 参数！！！）
        visualization_data = kg_service.get_visualization_data(
            kg_id=kg_id,
            user_id=current_user["id"],  # 之前缺失的参数，导致服务层可能处理异常
            limit=limit
        )

        # 3. 校验返回数据（避免前端接收空数据时异常）
        if not visualization_data.get("nodes") and not visualization_data.get("edges"):
            logger.warning(f"图谱 {kg_id} 无可视化数据（节点/关系为空）")
            return {"nodes": [], "edges": [], "message": "该图谱暂无数据可可视化"}

        logger.info(f"用户 {current_user['id']} 获取图谱 {kg_id} 可视化数据：节点{len(visualization_data['nodes'])}个，关系{len(visualization_data['edges'])}个")
        return visualization_data

    except Exception as e:
        logger.error(f"获取图谱 {kg_id} 可视化数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取可视化数据失败: {str(e)}")


@router.delete("/{kg_id}", summary="删除指定知识图谱", status_code=200)
async def delete_knowledge_graph(
    kg_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除除指定的知识图谱（包括数据库记录和Neo4j中的实体/关系）
    - 权限校验：仅图谱者者可删除
    - 操作：删除数据库中的KnowledgeGraph记录 + Neo4j中的相关实体和关系
    """
    # 1. 权限校验（确保用户只能删除自己的图谱）
    if not kg_service.verify_kg_ownership(db=db, kg_id=kg_id, user_id=current_user["id"]):
        logger.warning(f"用户 {current_user['id']} 无权删除图谱 {kg_id}")
        raise HTTPException(status_code=403, detail="无权删除该知识图谱")

    try:
        # 2. 调用服务层删除方法（需在KGService中实现）
        success = kg_service.delete_knowledge_graph(
            db=db,
            kg_id=kg_id,
            user_id=current_user["id"]
        )

        if success:
            logger.info(f"用户 {current_user['id']} 成功删除图谱 {kg_id}")
            return {"success": True, "message": "知识图谱删除成功"}
        else:
            logger.warning(f"图谱 {kg_id} 删除失败，未找到对应记录")
            raise HTTPException(status_code=404, detail="知识图谱不存在")

    except Exception as e:
        logger.error(f"删除图谱 {kg_id} 失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")



#刷新和测试
@router.post("/{kg_id}/refresh", summary="刷新知识图谱")
async def refresh_knowledge_graph(
    kg_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    刷新知识图谱数据
    """
    # 这里实现刷新逻辑，比如重新处理文件、更新实体关系等
    return {"message": "刷新成功", "kg_id": kg_id}

@router.get("/{kg_id}/export", summary="导出知识图谱数据")
async def export_knowledge_graph(
    kg_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    导出知识图谱数据
    """
    # 这里实现导出逻辑，返回JSON格式的数据
    kg_data = {
        "kg_id": kg_id,
        "entities": [],  # 填充实体数据
        "relations": [],  # 填充关系数据
        "export_time": datetime.now().isoformat()
    }
    return kg_data