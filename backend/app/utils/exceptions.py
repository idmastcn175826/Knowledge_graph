from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class APIException(HTTPException):
    """自定义API异常类，继承自FastAPI的HTTPException"""
    def __init__(
        self,
        detail: str = "服务器内部错误",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: int = -1,
        headers: dict = None
    ):
        self.code = code  # 自定义错误代码
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class ResourceNotFoundError(APIException):
    """资源未找到异常"""
    def __init__(self, detail: str = "资源不存在", code: int = 404):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            code=code
        )

class PermissionDeniedError(APIException):
    """权限不足异常"""
    def __init__(self, detail: str = "没有足够的权限", code: int = 403):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            code=code
        )

class InvalidParameterError(APIException):
    """参数无效异常"""
    def __init__(self, detail: str = "无效的参数", code: int = 400):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code
        )

class AuthenticationError(APIException):
    """认证失败异常"""
    def __init__(self, detail: str = "认证失败", code: int = 401):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            headers={"WWW-Authenticate": "Bearer"}
        )

# 全局异常处理器
async def api_exception_handler(request: Request, exc: APIException):
    """处理自定义API异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.detail,
            "request": f"{request.method} {request.url}"
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": -1,
            "message": "服务器内部错误",
            "detail": str(exc) if status.HTTP_500_INTERNAL_SERVER_ERROR else None,
            "request": f"{request.method} {request.url}"
        }
    )
