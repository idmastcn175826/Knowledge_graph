import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

# 从路由目录导入所有路由
from app.api.v1.routers import (user, file, knowledge_graph, qa, data_router,sql_router,health_agent_router)
from app.api.v1.routers import rag
from app.config.config import settings
from app.utils.exceptions import APIException
from app.db.init_db import init_db

# 确保日志目录存在
log_dir = Path(settings.log_dir)
log_dir.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

# 模块专用日志器
file_parser_logger = logging.getLogger("file_parser")
file_parser_logger.addHandler(
    RotatingFileHandler(
        log_dir / "file_parser.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
)
file_parser_logger.propagate = False

kg_service_logger = logging.getLogger("kg_service")
kg_service_logger.addHandler(
    RotatingFileHandler(
        log_dir / "kg_service.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
)
kg_service_logger.propagate = False

logger = logging.getLogger(__name__)


# 使用新的lifespan替代on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    init_db()
    logger.info(f"服务器启动完成，API前缀: {settings.api_prefix}")
    logger.info(f"可用接口文档: http://localhost:8000/docs")
    logger.info(f"可用接口文档: http://localhost:8000/redoc")
    logger.info(f"日志文件存储路径: {log_dir.resolve()}")
    yield


# 创建FastAPI应用
app = FastAPI(
    title="AI应用问答系统",
    description="基于Qwen模型、FastAPI和Neo4j的问答系统",
    version="1.0.0",
    lifespan=lifespan  # 使用新的生命周期管理
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册所有路由
app.include_router(user.router, prefix=f"{settings.api_prefix}/user", tags=["用户管理"])
app.include_router(file.router, prefix=f"{settings.api_prefix}/file", tags=["文件管理"])
app.include_router(knowledge_graph.router, prefix=f"{settings.api_prefix}/kg", tags=["知识图谱"])
app.include_router(qa.router, prefix=f"{settings.api_prefix}/qa", tags=["问答对话"])
app.include_router(data_router.router, prefix=f"{settings.api_prefix}/convert", tags=["微调数据集转换"])
app.include_router(sql_router.router, prefix=f"{settings.api_prefix}/dataset", tags=["数据库查询"])
app.include_router(rag.router, prefix=f"{settings.api_prefix}/rag", tags=["RAG系统"])
app.include_router(health_agent_router.router, prefix=f"{settings.api_prefix}/health", tags=["健康监测agent"])


# 根路径路由
@app.get("/", include_in_schema=False)
async def read_root():
    frontend_index = Path("frontend/index.html")
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "message": "谱构建问答对话系统API",
        "version": "1.0.0",
        "docs": f"http://localhost:{settings.port}{settings.api_prefix}/docs"
    }


# 全局异常处理
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    logger.error(f"API异常: {exc.detail} (代码: {exc.code})")
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
    logger.error(f"服务器内部错误: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务器内部错误", "data": None}
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"准备启动服务器，监听地址: 0.0.0.0:{settings.port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_config=None
    )
