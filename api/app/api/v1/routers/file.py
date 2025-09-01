import os
import uuid
import logging
from typing import List, Annotated, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config.config import settings
from app.models.schema import FileInfo, UploadFileResponse
from app.service.file_service import FileService
from app.utils.auth import get_current_active_user
from app.utils.db import get_db

# 初始化日志
logger = logging.getLogger(__name__)

# 确保上传目录存在
upload_dir = Path(settings.upload_dir).resolve()
try:
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"上传目录准备就绪: {upload_dir}")
except Exception as e:
    logger.error(f"创建上传目录失败: {str(e)}", exc_info=True)
    # 启动时就抛出错误，避免后续上传失败
    raise RuntimeError(f"无法初始化上传目录: {str(e)}")

router = APIRouter()
file_service = FileService()


@router.post("/upload", response_model=UploadFileResponse)
async def upload_file(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db),
        file: UploadFile = File(...)
) -> Dict[str, Any]:
    """上传文件"""
    file_id = None
    file_path = None
    try:
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        # 提取并保留原始文件扩展名
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        # 保存文件名格式: UUID + 原始扩展名
        saved_filename = f"{file_id}{file_ext}"
        file_path = upload_dir / saved_filename

        # 保存文件内容
        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # 转换为人类可读的文件大小
            file_size_mb = len(content) / (1024 * 1024)
            logger.info(
                f"文件内容已保存: 用户={current_user['id']}, "
                f"文件ID={file_id}, 路径={file_path}, 大小={file_size_mb:.2f}MB"
            )
        except Exception as e:
            logger.error(f"写入文件到磁盘失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件保存到磁盘失败: {str(e)}"
            )

        # 保存文件信息到数据库
        try:
            file_info = file_service.save_file_info(
                db=db,
                user_id=current_user["id"],
                file_id=file_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size=len(content),
                file_type=file.content_type or "application/octet-stream"
            )
            logger.info(f"文件信息已保存到数据库: 文件ID={file_id}")
        except Exception as e:
            logger.error(f"保存文件信息到数据库失败: {str(e)}", exc_info=True)
            if file_path and file_path.exists():
                os.remove(file_path)
                logger.info(f"数据库保存失败，已删除临时文件: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件信息保存失败: {str(e)}"
            )

        return {
            "success": True,
            "file_id": file_id,
            "message": "文件上传成功",
            "file_info": file_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传过程中发生意外错误: {str(e)}", exc_info=True)
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"上传失败，已清理文件: {file_path}")
            except Exception as cleanup_err:
                logger.warning(f"清理文件失败: {str(cleanup_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/list", response_model=List[FileInfo])
async def list_files(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(20, ge=10, le=100, description="每页数量，10-100之间")
) -> List[Dict[str, Any]]:
    """获取用户文件列表（分页）"""
    skip = (page - 1) * page_size
    return file_service.get_user_files(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=page_size
    )


@router.get("/{file_id}/download", response_class=FileResponse)
async def download_file(
        file_id: str,
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db)
) -> FileResponse:
    """下载文件"""
    file_info = file_service.get_file_by_id(
        db=db,
        file_id=file_id,
        user_id=current_user["id"]
    )

    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在或无权访问"
        )

    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件已被删除"
        )

    return FileResponse(
        path=file_path,
        filename=file_info["filename"],
        media_type=file_info["file_type"]
    )


@router.delete("/{file_id}")
async def delete_file(
        file_id: str,
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """删除文件"""
    try:
        success = file_service.delete_file(
            db=db,
            file_id=file_id,
            user_id=current_user["id"]
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或无权访问"
            )

        return {
            "success": True,
            "message": "文件已删除"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}"
        )
