from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi.responses import HTMLResponse

from app.data_to_sql.database import DatabaseType, DatabaseFactory
from app.data_to_sql.llm_client import generate_sql

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 数据库连接配置缓存
db_connections: Dict[str, Any] = {}

# 定义请求模型
class ConnectRequest(BaseModel):
    db_type: str
    host: str
    user: str
    password: str
    database: str
    port: Optional[int] = None

class QueryRequest(BaseModel):
    connection_id: str
    question: str
    table_name: Optional[str] = None

class DisconnectRequest(BaseModel):
    connection_id: str

@router.get("/", response_class=HTMLResponse)
def index():
    """首页路由"""
    frontend_path = Path("web/index.html")
    if frontend_path.exists():
        return frontend_path.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="首页文件未找到")

@router.post("/connect")
def connect_db(request: ConnectRequest):
    """连接数据库接口"""
    try:
        # 转换数据库类型为枚举
        try:
            db_type = DatabaseType[request.db_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的数据库类型: {request.db_type}"
            )

        # 创建数据库连接
        db_factory = DatabaseFactory()
        db_connection = db_factory.create_database(
            db_type,
            host=request.host,
            user=request.user,
            password=request.password,
            database=request.database,
            port=request.port
        )

        # 测试连接
        if db_connection.test_connection():
            # 保存连接引用
            connection_id = f"{request.db_type}_{request.host}_{request.database}"
            db_connections[connection_id] = db_connection
            return {
                "message": "数据库连接成功",
                "connection_id": connection_id
            }
        else:
            raise HTTPException(status_code=500, detail="数据库连接失败")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"连接数据库时发生错误: {str(e)}"
        )

@router.post("/query")
def query_db(request: QueryRequest):
    """查询数据库接口"""
    # 验证连接ID
    if request.connection_id not in db_connections:
        logger.error(f"无效的数据库连接ID: {request.connection_id}")
        raise HTTPException(status_code=400, detail="无效的数据库连接ID")

    try:
        # 获取数据库连接
        db_connection = db_connections[request.connection_id]
        logger.info(f"使用连接ID: {request.connection_id}, 数据库类型: {db_connection.db_type}")

        # 使用大模型生成SQL
        sql_query = generate_sql(
            request.question,
            db_connection.db_type,
            request.table_name
        )
        logger.info(f"生成的SQL: {sql_query}")

        # 执行查询
        result = db_connection.execute_query(sql_query)
        logger.info(f"查询成功，返回 {len(result)} 条结果")

        return {
            "sql": sql_query,
            "result": result
        }

    except Exception as e:
        logger.error(f"查询失败: {str(e)}", exc_info=True)
        # 捕获异常时尝试返回已生成的SQL（如果有）
        sql_info = {"sql": locals().get('sql_query')} if 'sql_query' in locals() else {}
        raise HTTPException(
            status_code=500,
            detail={**{"error": f"查询失败: {str(e)}"},** sql_info}
        )


class ExecuteRequest(BaseModel):
    connection_id: str
    sql: str

@router.post("/execute")
def execute_sql(request: ExecuteRequest):
    """执行SQL查询接口"""
    if request.connection_id not in db_connections:
        raise HTTPException(status_code=400, detail="无效的数据库连接ID")

    try:
        db_connection = db_connections[request.connection_id]
        result = db_connection.execute_query(request.sql)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SQL执行错误: {str(e)}"
        )

@router.post("/disconnect")
def disconnect_db(request: DisconnectRequest):
    """断开数据库连接接口"""
    if request.connection_id not in db_connections:
        raise HTTPException(status_code=400, detail="无效的数据库连接ID")

    # 断开连接并移除缓存
    db_connections[request.connection_id].disconnect()
    del db_connections[request.connection_id]
    return {"message": "数据库连接已断开"}
