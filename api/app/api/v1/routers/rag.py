import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from app.db.session import get_db
from sqlalchemy.orm import Session

from app.models.schema import RAGCollectionResponse, RAGCollectionCreate, RAGDocumentResponse, RAGQueryRequest, \
    RAGQueryResponse, CollectionQueryRequest
from app.rag.file_processor import FileProcessor
from app.rag.rag_service import RAGService
from app.utils.exceptions import RAGException

router = APIRouter()
logger = logging.getLogger(__name__)



# 路由定义
@router.post("/collections", response_model=RAGCollectionResponse)
async def create_collection(
        collection: RAGCollectionCreate,
        db: Session = Depends(get_db)
):
    """创建新的RAG文档集合"""
    try:
        rag_service = RAGService(db)
        new_collection = rag_service.create_collection(
            name=collection.name,
            description=collection.description
        )
        return new_collection
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建集合失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/collections", response_model=List[RAGCollectionResponse])
async def list_collections(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """获取所有RAG文档集合"""
    try:
        rag_service = RAGService(db)
        # 现在返回的是字典列表，而非对象列表
        collections = rag_service.list_collections(skip=skip, limit=limit)

        # 关键修复：访问字典的键而非对象的属性
        response_list = []
        for col in collections:
            # 安全处理创建时间（如果已经是字符串则无需转换）
            created_at_str = col["created_at"]
            if hasattr(created_at_str, 'isoformat'):  # 如果还是datetime对象
                created_at_str = created_at_str.isoformat()

            response_item = {
                "id": col["id"],  # 使用字典键访问
                "name": col["name"],
                "description": col.get("description"),  # 使用get方法处理可选字段
                "document_count": col["document_count"],
                "created_at": created_at_str
            }
            response_list.append(response_item)

        return response_list
    except Exception as e:
        logger.error(f"获取集合列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.delete("/collections/{collection_id}")
async def delete_collection(
        collection_id: int,
        db: Session = Depends(get_db)
):
    """删除RAG文档集合"""
    try:
        rag_service = RAGService(db)
        success = rag_service.delete_collection(collection_id)
        if not success:
            raise HTTPException(status_code=404, detail="集合未找到")
        return {"message": "集合删除成功"}
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除集合失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/collections/{collection_id}/documents")
async def add_document_to_collection(
        collection_id: int,
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """添加文档到RAG集合"""
    try:
        rag_service = RAGService(db)
        file_processor = FileProcessor()

        # 验证集合是否存在
        collection = rag_service.get_collection(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="集合未找到")

        # 保存文件
        file_info = await file_processor.save_file(file)

        # 创建文档记录
        document = rag_service.create_document(
            collection_id=collection_id,
            filename=file_info["filename"],
            file_path=file_info["file_path"],
            file_type=file_info["file_type"],
            file_size=file_info["file_size"]
        )

        # 后台处理文档索引
        background_tasks.add_task(
            rag_service.process_and_index_document,
            document.id,
            file_info["file_path"]
        )

        return {"message": "文档上传成功，正在处理中", "document_id": document.id}
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.delete("/collections/{collection_id}/documents/{document_id}")
async def remove_document_from_collection(
        collection_id: int,
        document_id: int,
        db: Session = Depends(get_db)
):
    """从RAG集合中移除文档"""
    try:
        rag_service = RAGService(db)
        success = rag_service.remove_document(collection_id, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档未找到")
        return {"message": "文档移除成功"}
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"移除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/collections/{collection_id}/documents", response_model=List[RAGDocumentResponse])
async def list_collection_documents(
        collection_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """获取RAG集合中的所有文档"""
    try:
        rag_service = RAGService(db)
        documents = rag_service.list_documents(collection_id, skip=skip, limit=limit)
        return documents
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
        query_request: RAGQueryRequest,
        db: Session = Depends(get_db)
):
    """查询RAG系统"""
    try:
        rag_service = RAGService(db)
        result = rag_service.query(
            collection_id=query_request.collection_id,
            query=query_request.query,
            top_k=query_request.top_k,
            mode=query_request.mode
        )
        return result
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/collections/{collection_id}/query", response_model=RAGQueryResponse)
async def query_collection(
        collection_id: int,
        query_request: CollectionQueryRequest,
        db: Session = Depends(get_db)
):
    """查询指定的RAG集合"""
    try:
        # 验证集合是否存在
        rag_service = RAGService(db)
        collection = rag_service.get_collection(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail=f"集合 ID {collection_id} 不存在")

        # 执行查询
        result = rag_service.query(
            collection_id=collection_id,
            query=query_request.query,
            top_k=query_request.top_k,
            mode=query_request.mode
        )
        return result
    except RAGException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"查询集合 {collection_id} 失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询处理失败")