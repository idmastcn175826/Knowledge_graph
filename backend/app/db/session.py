from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.mysql_url,
    echo=settings.db_echo,  # 开发环境可设为True，打印SQL语句
    pool_pre_ping=True  # 检查连接可用性
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库会话依赖项
def get_db():
    """获取数据库会话，用于依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 确保会话最终关闭
