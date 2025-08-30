# app/crud/crud_file.py
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from app.models.file import File  # ORM模型
from app.models.schema import FileCreate  # Pydantic模型
from app.core.config import settings  # 项目配置（包含上传目录）


def create_file(db: Session, file_in: FileCreate, user_id: int) -> File:
    """创建文件记录（上传文件后调用）"""
    # 拼接文件完整路径（与app/service/file_service.py逻辑一致）
    file_path = str(Path(settings.upload_dir) / file_in.file_id)
    if file_in.file_ext:
        file_path += file_in.file_ext  # 补充文件扩展名（如.pdf）

    db_file = File(
        file_id=file_in.file_id,
        filename=file_in.filename,
        file_path=file_path,
        file_size=file_in.file_size,
        file_type=file_in.file_type,
        user_id=user_id,
        upload_time=datetime.now()
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file_by_id(db: Session, file_id: str, user_id: int) -> File | None:
    """通过文件ID和用户ID获取文件（确保用户只能访问自己的文件）"""
    return db.query(File).filter(
        File.file_id == file_id,
        File.user_id == user_id
    ).first()


def get_files_by_user(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> list[File]:
    """分页获取用户的所有文件（文件列表接口用）"""
    offset = (page - 1) * page_size
    return db.query(File).filter(File.user_id == user_id).offset(offset).limit(page_size).all()


def delete_file(db: Session, file_id: str, user_id: int) -> bool:
    """删除文件记录（物理删除可选）"""
    db_file = get_file_by_id(db, file_id, user_id)
    if not db_file:
        return False

    # 可选：物理删除文件（若需要）
    try:
        Path(db_file.file_path).unlink(missing_ok=True)
    except Exception as e:
        from app.utils.logger import logger  # 项目日志工具
        logger.warning(f"物理删除文件失败: {db_file.file_path}, 错误: {str(e)}")

    # 数据库删除记录
    db.delete(db_file)
    db.commit()
    return True