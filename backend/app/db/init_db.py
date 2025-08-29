import logging

from app.utils.db import Base, engine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """创建所有数据库表结构"""
    try:
        # 创建所有模型对应的表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表结构创建成功")
        print("数据库表结构创建成功")
    except Exception as e:
        logger.error(f"数据库表结构创建失败: {str(e)}")
        print(f"数据库表结构创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
