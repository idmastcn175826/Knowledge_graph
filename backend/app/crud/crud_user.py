# app/crud/crud_user.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User  # 需在app/models/user.py中定义User ORM模型
from app.models.schema import UserCreate  # 需在app/models/schema.py中定义Pydantic模型

# 密码加密上下文（与app/core/security.py保持一致）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_user(db: Session, user_in: UserCreate) -> User:
    """创建新用户"""
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """通过用户ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> User | None:
    """通过用户名获取用户（登录时用）"""
    return db.query(User).filter(User.username == username).first()