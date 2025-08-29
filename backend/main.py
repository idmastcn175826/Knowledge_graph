import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.utils.exceptions import (
    APIException
)

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="知识图谱构建与问答对话系统",
    description="基于Qwen模型、FastAPI和Neo4j的知识图谱系统",
    version="1.0.0"
)


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册API路由
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def read_index():
    return FileResponse("path/to/your/index.html")

@app.post("/api/v1/user/register")
async def register_user():
    # 您的注册逻辑
    return {"message": "注册成功"}

@app.post("/api/v1/user/login")
async def login_user():
    # 您的登录逻辑
    return {"access_token": "example_token", "token_type": "bearer"}

# 全局异常处理
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    logger.error(f"API Exception: {exc.detail}")
    # 4. 修复exc.data可能不存在的问题
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.detail,
            "data": getattr(exc, 'data', None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Server Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务器内部错误", "data": None}
    )

# 根路径
@app.get("/")
async def root():
    return {"message": "知识图谱构建与问答对话系统API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
