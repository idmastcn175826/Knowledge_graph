from datetime import timedelta
from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.models.schema import UserCreate, UserResponse, Token
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user
)

router = APIRouter()

# 模拟数据库 - 实际应用中应替换为真实数据库操作
fake_users_db = {
    "testuser": {
        "id": "1",
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
        "role": "user"
    }
}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate) -> Dict[str, Any]:
    """用户注册"""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    hashed_password = get_password_hash(user.password)
    user_id = str(len(fake_users_db) + 1)

    fake_users_db[user.username] = {
        "id": user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "role": "user"
    }

    return {
        "id": user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": "user"
    }


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Dict[str, str]:
    """用户登录，获取访问令牌"""
    user = fake_users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)]
) -> Dict[str, Any]:
    """获取当前登录用户信息"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "full_name": fake_users_db[current_user["username"]]["full_name"],
        "email": fake_users_db[current_user["username"]]["email"],
        "role": current_user["role"]
    }
