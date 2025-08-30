# app/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

from app.core.config import settings

# 确保日志目录存在
settings.log_dir.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = __name__) -> logging.Logger:
    """获取配置好的日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式：时间 - 模块 - 级别 - 消息
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 文件处理器（按大小轮转）
    file_handler = RotatingFileHandler(
        filename=settings.log_dir / "app.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.log_level)

    # 2. 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.log_level)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_file_parser_logger() -> logging.Logger:
    """文件解析专用日志器"""
    logger = logging.getLogger("file_parser")
    logger.setLevel(settings.log_level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 单独输出到file_parser.log
    file_handler = RotatingFileHandler(
        filename=settings.log_dir / "file_parser.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False  # 不向上传递，避免重复输出
    return logger


def get_kg_service_logger() -> logging.Logger:
    """知识图谱服务专用日志器"""
    logger = logging.getLogger("kg_service")
    logger.setLevel(settings.log_level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 单独输出到kg_service.log
    file_handler = RotatingFileHandler(
        filename=settings.log_dir / "kg_service.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger