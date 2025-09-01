from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.mysql_url,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    echo=False  # 生产环境设为False，开发环境可设为True查看SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 基础模型类，所有模型都继承这个类
Base = declarative_base()

def get_db():
    """
    数据库会话依赖项
    用于FastAPI路由中获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
