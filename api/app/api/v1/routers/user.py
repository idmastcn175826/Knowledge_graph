from datetime import timedelta
from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.db.session import get_db

from app.config.config import settings

from app.models.schema import UserCreate, UserResponse, Token
from app.models.user import User
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
        user: UserCreate,
        db: Annotated[Session, Depends(get_db)]
) -> Dict[str, Any]:
    """用户注册（带密码强度验证）"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已被注册
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 密码加密
    hashed_password = get_password_hash(user.password)

    # 创建数据库用户记录
    db_user = User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        is_active=True,
        role="user"
    )

    # 保存到数据库
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {
            "id": db_user.id,
            "username": db_user.username,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "role": db_user.role
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: 数据库错误 - {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> Dict[str, str]:
    """用户登录"""
    # 从数据库查询用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用，请联系管理员"
        )

    # 验证密码
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)]
) -> Dict[str, Any]:
    """获取当前登录用户信息"""
    db_user = db.query(User).filter(User.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": db_user.id,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "email": db_user.email,
        "role": db_user.role
    }
