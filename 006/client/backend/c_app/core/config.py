import os
import secrets
from typing import List, Optional, Union

from pydantic_settings import BaseSettings


# 定义一个函数返回默认CORS源
def get_default_cors():
    return ["http://localhost:3000", "http://localhost:8000", "http://localhost", 
            "http://127.0.0.1:3000", "http://127.0.0.1:8000", "http://127.0.0.1",
            "https://localhost:3000", "https://localhost:8000", "https://localhost",
            "https://127.0.0.1:3000", "https://127.0.0.1:8000", "https://127.0.0.1",
            "ws://localhost:3000", "ws://localhost:8000", "ws://localhost",
            "ws://127.0.0.1:3000", "ws://127.0.0.1:8000", "ws://127.0.0.1",
            "wss://localhost:3000", "wss://localhost:8000", "wss://localhost",
            "wss://127.0.0.1:3000", "wss://127.0.0.1:8000", "wss://127.0.0.1",
            "http://localhost:3000/api", "http://localhost:8000/api", "http://localhost/api",
            "http://127.0.0.1:3000/api", "http://127.0.0.1:8000/api", "http://127.0.0.1/api",
            "http://localhost:3000/api/v1", "http://localhost:8000/api/v1", "http://localhost/api/v1",
            "http://127.0.0.1:3000/api/v1", "http://127.0.0.1:8000/api/v1", "http://127.0.0.1/api/v1",
            "*"]  # 添加通配符以支持所有来源（仅用于开发环境）


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 访问令牌过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS允许的源 - 不使用默认值，通过验证器设置
    BACKEND_CORS_ORIGINS: Optional[List[str]] = None
    
    # 大语言模型相关配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    LLM_MODEL: str = "deepseek-chat"  # 默认使用的模型
    
    # 知识库相关配置
    KNOWLEDGE_BASE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge_base")

    CHROMA_DB_HOST: str = "localhost"
    CHROMA_DB_PORT: int = 8000
    CHROMA_DB_SSL: bool = False

    # VLLM Configuration
    VLLM_API_KEY: str = os.environ.get("VLLM_API_KEY", "sk-44013fb58d4d4ff39919d7eeeaa0979f")
    VLLM_API_URL: str = os.environ.get("VLLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    VLLM_API_MODEL: str = os.environ.get("VLLM_API_MODEL", "qwen-vl-max-latest")

    def model_post_init(self, __context):
        """在模型初始化后设置默认值"""
        if self.BACKEND_CORS_ORIGINS is None:
            self.BACKEND_CORS_ORIGINS = get_default_cors()
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
    }


# 创建全局设置实例
settings = Settings()