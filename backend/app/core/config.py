import os
from typing import List

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    # Neo4j配置
    neo4j_uri: str = Field(default=os.getenv("NEO4J_URI"), env="NEO4J_URI")
    neo4j_user: str = Field(default=os.getenv("NEO4J_USER"), env="NEO4J_USER")
    neo4j_password: str = Field(default=os.getenv("NEO4J_PASSWORD"), env="NEO4J_PASSWORD")

    # Qwen模型配置
    qwen_default_api_key: str = Field(default=os.getenv("QWEN_DEFAULT_API_KEY"), env="QWEN_DEFAULT_API_KEY")
    qwen_api_base_url: str = Field(default=os.getenv("QWEN_API_BASE_URL"), env="QWEN_API_BASE_URL")

    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    # 数据库配置
    mysql_host: str = Field(default=os.getenv("MYSQL_HOST"), env="MYSQL_HOST")
    mysql_port: int = Field(default=int(os.getenv("MYSQL_PORT", 3306)), env="MYSQL_PORT")
    mysql_user: str = Field(default=os.getenv("MYSQL_USER"), env="MYSQL_USER")
    mysql_password: str = Field(default=os.getenv("MYSQL_PASSWORD"), env="MYSQL_PASSWORD")
    mysql_database: str = Field(default=os.getenv("MYSQL_DATABASE"), env="MYSQL_DATABASE")

    # JWT配置
    jwt_secret_key: str = Field(default=os.getenv("JWT_SECRET_KEY"), env="JWT_SECRET_KEY")
    jwt_access_token_expire_minutes: int = Field(default=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 120)),
                                                 env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # 应用配置
    api_prefix: str = Field(default=os.getenv("API_PREFIX", "/api/v1"), env="API_PREFIX")
    upload_dir: str = Field(default=os.getenv("UPLOAD_DIR", "./uploads"), env="UPLOAD_DIR")
    temp_dir: str = Field(default=os.getenv("TEMP_DIR", "./temp"), env="TEMP_DIR")
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), env="LOG_LEVEL")

    # MySQL连接URL属性
    @property
    def mysql_url(self) -> str:
        """生成MySQL连接URL"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    class Config:
        case_sensitive = True


settings = Settings()
