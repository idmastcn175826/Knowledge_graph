import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"警告: 未找到.env文件，路径: {env_path}")


class Settings(BaseSettings):
    # 基础配置 - 优先从环境变量获取，其次使用默认值
    api_prefix: str = Field(default_factory=lambda: os.getenv("API_PREFIX", "/api/v1"), alias="API_PREFIX")
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() == "true", alias="DEBUG")
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", 8000)), alias="PORT")

    # 路径配置
    upload_dir: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "./uploads"), alias="UPLOAD_DIR")
    temp_dir: str = Field(default_factory=lambda: os.getenv("TEMP_DIR", "./temp"), alias="TEMP_DIR")
    log_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("LOG_DIR", str(Path(__file__).parent.parent.parent / "logs"))),
        alias="LOG_DIR"
    )

    # 日志配置
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),alias="LOG_LEVEL")
    log_max_bytes: int = Field(default_factory=lambda: int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024)),alias="LOG_MAX_BYTES")
    log_backup_count: int = Field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", 5)),alias="LOG_BACKUP_COUNT")

    # Neo4j配置
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", ""),alias="NEO4J_URI")
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", ""),alias="NEO4J_USER")
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""),alias="NEO4J_PASSWORD")

    # Qwen模型配置
    QWEN_MODEL_NAME: str = Field(default_factory=lambda: os.getenv("QWEN_MODEL_NAME", ""),alias="QWEN_MODEL_NAME")
    QWEN_DEFAULT_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("QWEN_DEFAULT_API_KEY"),alias="QWEN_DEFAULT_API_KEY")
    QWEN_API_BASE_URL: str = Field(default_factory=lambda: os.getenv("QWEN_API_BASE_URL", ""),alias="QWEN_API_BASE_URL")
    # QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.7"))
    #
    # #智能体配置
    # MAX_SHORT_TERM_MEMORY = int(os.getenv("MAX_SHORT_TERM_MEMORY", "100"))



    # CORS配置跨域
    cors_origins: List[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:63342").split(","),
        alias="CORS_ORIGINS")
    allowed_origins: List[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(","),
        alias="ALLOWED_ORIGINS")

    # 数据库配置
    db_echo: bool = Field(default_factory=lambda: os.getenv("DB_ECHO", "False").lower() == "true",alias="DB_ECHO")
    mysql_host: str = Field(default_factory=lambda: os.getenv("MYSQL_HOST", ""),alias="MYSQL_HOST")
    mysql_port: int = Field(default_factory=lambda: int(os.getenv("MYSQL_PORT", 3306)),alias="MYSQL_PORT")
    mysql_user: str = Field(default_factory=lambda: os.getenv("MYSQL_USER", ""),alias="MYSQL_USER")
    mysql_password: str = Field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", ""),alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default_factory=lambda: os.getenv("MYSQL_DATABASE", ""),alias="MYSQL_DATABASE")

    # JWT配置
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""),alias="JWT_SECRET_KEY")
    jwt_access_token_expire_minutes: int = Field(default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 120)),
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # RAG配置
    vector_store_path: str = "data/vector_store"
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # 可以根据需要更改
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # 文件上传配置
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = ["txt", "pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls"]

    # 健康监测默认状态配置
    HEALTH_MONITOR_DEFAULT_ENABLED: bool = Field(default_factory=lambda: os.getenv("HEALTH_MONITOR_DEFAULT_ENABLED", "False"),
                                                 alias="HEALTH_MONITOR_DEFAULT_ENABLED")

    # 验证Qwen API地址
    @field_validator('QWEN_API_BASE_URL')  # 原错误：'qwen_api_base_url'（小写）
    def validate_qwen_api_url(cls, v):
        if not v:
            return v  # 为空时不验证，在使用处处理

        required_path = "/compatible-mode/v1/chat/completions"
        if required_path not in v:
            import warnings
            warnings.warn(
                f"Qwen API地址似乎不完整，缺少必要路径'{required_path}'。"
                f"请检查配置，正确格式应为类似'https://dashscope.aliyuncs.com{required_path}'"
            )
        return v

    # 验证关键配置是否存在
    @field_validator('neo4j_uri', 'neo4j_user', 'neo4j_password')
    def validate_neo4j_config(cls, v, info):
        field_name = info.field_name
        if not v:
            import warnings
            warnings.warn(f"Neo4j配置项 {field_name} 未设置，可能导致数据库连接失败")
        return v

    @field_validator('mysql_host', 'mysql_user', 'mysql_database')
    def validate_mysql_config(cls, v, info):
        field_name = info.field_name
        if not v:
            import warnings
            warnings.warn(f"MySQL配置项 {field_name} 未设置，可能导致数据库连接失败")
        return v

    @field_validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if not v:
            import warnings
            warnings.warn("JWT密钥未设置，将使用不安全的默认值")
            return "default-insecure-secret-key-for-development-only"
        return v

    # MySQL连接URL属性
    @property
    def mysql_url(self) -> str:
        """生成MySQL连接URL"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    class Config:
        case_sensitive = True
        env_file = ".env"  # 冗余配置，确保兼容性
        extra = "ignore"  # 忽略未定义的环境变量


settings = Settings()
