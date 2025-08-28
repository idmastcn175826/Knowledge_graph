from fastapi import APIRouter
from app.api.v1.routers import user, file, knowledge_graph, qa

# 创建API路由
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])
api_router.include_router(file.router, prefix="/file", tags=["文件处理"])
api_router.include_router(knowledge_graph.router, prefix="/kg", tags=["知识图谱"])
api_router.include_router(qa.router, prefix="/qa", tags=["问答对话"])
