"""
基础配置
包含应用的核心配置项
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用基础配置"""
    
    # 应用信息
    app_name: str = "AI写作平台"
    app_version: str = "1.0.0"
    app_description: str = "基于FastAPI + AutoGen的智能写作平台"
    
    # 环境配置
    environment: str = "development"  # development, staging, production
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS配置
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/json"
    ]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # 安全配置
    allowed_hosts: List[str] = ["*"]
    
    # 数据库配置
    database_url: str = "mysql+pymysql://root:mysql@localhost:3306/ai_document"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Redis配置（可选）
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # JWT配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # OpenAI配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7

    # DeepSeek配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 4000
    deepseek_temperature: float = 0.7

    # 默认模型提供商配置
    default_model_provider: str = "deepseek"  # openai, deepseek
    default_model_name: str = "deepseek-chat"
    
    # AutoGen配置
    autogen_enabled: bool = True
    autogen_cache_enabled: bool = True
    autogen_cache_duration: int = 3600
    autogen_max_rounds: int = 5
    autogen_timeout: int = 300
    
    # 监控配置
    enable_metrics: bool = True
    metrics_endpoint: str = "/metrics"
    health_check_endpoint: str = "/health"
    
    # 限流配置
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    class Config:
        # 确保能找到.env文件，无论从哪个目录运行
        env_file = [
            ".env",  # 当前目录
            "backend/.env",  # 从根目录运行时
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env")  # 绝对路径
        ]
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.upload_dir,
            "logs",
            "cache",
            "temp"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


# 创建全局设置实例
settings = Settings()

# 根据环境调整配置
if settings.is_production:
    settings.debug = False
    settings.reload = False
    settings.log_level = "WARNING"
    settings.database_echo = False
elif settings.is_testing:
    settings.debug = True
    settings.database_url = settings.database_url.replace("/ai_document", "/ai_document_test")
    settings.log_level = "DEBUG"
