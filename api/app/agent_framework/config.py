import os
from dotenv import load_dotenv
from typing import Dict, Any

# 加载环境变量
load_dotenv()

class Config:
    """配置管理类，从环境变量读取配置"""
    
    # 模型提供商，支持"qwen"和"openai"
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "qwen")
    
    # Qwen模型配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")
    
    # OpenAI模型配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # 记忆系统配置
    MAX_SHORT_TERM_MEMORY = int(os.getenv("MAX_SHORT_TERM_MEMORY", "100"))
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """获取当前模型提供商的配置"""
        if cls.MODEL_PROVIDER == "qwen":
            return {
                "api_key": cls.QWEN_API_KEY,
                "api_base": cls.QWEN_API_BASE,
                "model": cls.QWEN_MODEL
            }
        elif cls.MODEL_PROVIDER == "openai":
            return {
                "api_key": cls.OPENAI_API_KEY,
                "api_base": cls.OPENAI_API_BASE,
                "model": cls.OPENAI_MODEL
            }
        else:
            raise ValueError(f"不支持的模型提供商: {cls.MODEL_PROVIDER}")
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        if cls.MODEL_PROVIDER == "qwen" and not cls.QWEN_API_KEY:
            raise ValueError("QWEN_API_KEY 未配置，请检查.env文件")
        if cls.MODEL_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请检查.env文件")
        return True
