import os
import uuid
from typing import List, Annotated, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schema import FileInfo, UploadFileResponse
from app.service.file_service import FileService  # 后续会创建这个服务类
from app.utils.auth import get_current_active_user
from app.utils.db import get_db

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)

router = APIRouter()
file_service = FileService()


@router.post("/upload", response_model=UploadFileResponse)
async def upload_file(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db),
        file: UploadFile = File(...)  # 有默认值的参数放在最后
) -> Dict[str, Any]:
    """上传文件"""
    try:
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        saved_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(settings.upload_dir, saved_filename)

        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # 记录文件信息到数据库
        file_info = file_service.save_file_info(
            db=db,
            user_id=current_user["id"],
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type or "application/octet-stream"
        )

        return {
            "success": True,
            "file_id": file_id,
            "message": "文件上传成功",
            "file_info": file_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/list", response_model=List[FileInfo])
async def list_files(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Session = Depends(get_db),
        page: int = 1,
        page_size: int = 20
) -> List[Dict[str, Any]]:
    """获取用户上传的文件列表"""
    skip = (page - 1) * page_size
    return file_service.get_user_files(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=page_size
    )


@router.get("/{file_id}/download")
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

    if not os.path.exists(file_info["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件已被删除"
        )

    return FileResponse(
        path=file_info["file_path"],
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
