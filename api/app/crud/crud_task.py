# app/crud/crud_task.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.task import Task  # ORM模型
from app.models.schema import TaskCreate, TaskProgressUpdate

def create_task(db: Session, task_in: TaskCreate, user_id: int) -> Task:
    """创建知识图谱构建任务记录"""
    db_task = Task(
        task_id=task_in.task_id,
        kg_name=task_in.kg_name,
        user_id=user_id,
        file_ids=task_in.file_ids,  # 存储文件ID列表（JSON格式，需在ORM模型中配置）
        algorithms=task_in.algorithms,  # 存储算法配置（JSON格式）
        progress=0,
        status="pending",
        stage="初始化",
        message="任务已提交",
        create_time=datetime.now(),
        update_time=datetime.now()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task_by_id(db: Session, task_id: str, user_id: int) -> Task | None:
    """通过任务ID和用户ID获取任务（确保权限）"""
    return db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == user_id
    ).first()


def update_task_progress(db: Session, task_id: str, user_id: int, progress_in: TaskProgressUpdate) -> Task | None:
    """更新任务进度（kg_service.py中异步调用）"""
    db_task = get_task_by_id(db, task_id, user_id)
    if not db_task:
        return None

    # 更新进度字段
    db_task.progress = progress_in.progress
    db_task.status = progress_in.status
    db_task.stage = progress_in.stage
    db_task.message = progress_in.message
    db_task.update_time = datetime.now()

    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks_by_user(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> list[Task]:
    """分页获取用户的所有任务（任务列表接口用）"""
    offset = (page - 1) * page_size
    return db.query(Task).filter(Task.user_id == user_id).order_by(Task.create_time.desc()).offset(offset).limit(
        page_size).all()