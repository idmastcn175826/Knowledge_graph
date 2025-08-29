from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 密码Bearer模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对密码进行加密

    Args:
        password: 明文密码

    Returns:
        加密后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要包含在令牌中的数据
        expires_delta: 令牌过期时间

    Returns:
        生成的JWT令牌
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # 生成令牌
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm="HS256"  # 使用HS256算法
    )

    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """
    获取当前认证用户

    Args:
        token: OAuth2令牌

    Returns:
        当前用户信息

    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码令牌
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )

        # 获取用户名（或用户ID）
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # 可以从数据库加载完整用户信息
        # 这里简化处理，实际应用中应该查询数据库
        user_info = {
            "id": user_id,
            "username": payload.get("username"),
            "role": payload.get("role", "user")
        }

        return user_info

    except JWTError:
        raise credentials_exception


async def get_current_active_user(
        current_user: Annotated[Dict[str, Any], Depends(get_current_user)]
) -> Dict[str, Any]:
    """
    获取当前活跃用户（附加检查）

    Args:
        current_user: 当前认证用户

    Returns:
        当前活跃用户信息

    Raises:
        HTTPException: 用户未激活时抛出
    """
    # 这里可以添加用户是否激活的检查
    # if not current_user.get("is_active", True):
    #     raise HTTPException(status_code=400, detail="未激活的用户")
    return current_user


async def get_current_admin_user(
        current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)]
) -> Dict[str, Any]:
    """
    获取当前管理员用户（权限检查）

    Args:
        current_user: 当前认证用户

    Returns:
        当前管理员用户信息

    Raises:
        HTTPException: 非管理员用户时抛出
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    return current_user
