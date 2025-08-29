import os
from typing import List, Dict, Any, Optional

from app.models.file import File as DBFile


class FileService:
    """文件服务类，处理文件相关业务逻辑"""

    def save_file_info(self, db, user_id: str, file_id: str, filename: str,
                       file_path: str, file_size: int, file_type: str) -> Dict[str, Any]:
        """保存文件信息到数据库"""
        db_file = DBFile(
            file_id=file_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            user_id=int(user_id)
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return self._db_file_to_info(db_file)

    def get_user_files(self, db, user_id: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的文件列表"""
        files = db.query(DBFile).filter(
            DBFile.user_id == int(user_id)
        ).offset(skip).limit(limit).all()

        return [self._db_file_to_info(file) for file in files]

    def get_file_by_id(self, db, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """根据文件ID获取文件信息"""
        file = db.query(DBFile).filter(
            DBFile.file_id == file_id,
            DBFile.user_id == int(user_id)
        ).first()

        if file:
            return self._db_file_to_info(file)
        return None

    def delete_file(self, db, file_id: str, user_id: str) -> bool:
        """删除文件（数据库记录和物理文件）"""
        file = db.query(DBFile).filter(
            DBFile.file_id == file_id,
            DBFile.user_id == int(user_id)
        ).first()

        if not file:
            return False

        # 删除物理文件
        if os.path.exists(file.file_path):
            try:
                os.remove(file.file_path)
            except Exception as e:
                # 记录日志，但不阻止数据库记录的删除
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"删除文件 {file.file_path} 失败: {str(e)}")

        # 删除数据库记录
        db.delete(file)
        db.commit()
        return True

    def _db_file_to_info(self, db_file: DBFile) -> Dict[str, Any]:
        """将数据库文件对象转换为响应模型"""
        return {
            "file_id": db_file.file_id,
            "file_name": db_file.filename,
            "file_size": db_file.file_size,
            "file_type": db_file.file_type,
            "upload_time": db_file.created_at
        }
