"""
应用配置模块
使用Pydantic Settings管理环境变量和应用配置
"""

from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "RBAC管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite://./rbac.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # 分页配置
    PAGINATION_PAGE_SIZE: int = 10
    PAGINATION_MAX_PAGE_SIZE: int = 1000
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_HASH_ROUNDS: int = 12
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # 缓存配置（可选）
    REDIS_URL: Optional[str] = None
    CACHE_EXPIRE_SECONDS: int = 3600

    # 企业级API配置
    API_VERSION: str = "v1.0.0"
    SERVER_ID: str = "server-001"
    ENABLE_REQUEST_TRACING: bool = True
    ENABLE_PERFORMANCE_MONITORING: bool = True

    # 安全配置
    ENABLE_IP_WHITELIST: bool = False
    IP_WHITELIST: List[str] = []
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # 权限配置
    ENABLE_DATA_PERMISSION: bool = True
    DEFAULT_DATA_SCOPE: str = "department"  # all, department, self
    PERMISSION_CACHE_EXPIRE: int = 300  # 5分钟

    # 审计配置
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90
    SENSITIVE_OPERATIONS: List[str] = [
        "user:create", "user:delete", "role:create", "role:delete",
        "permission:create", "permission:delete"
    ]

    # 错误处理配置
    ENABLE_DETAILED_ERRORS: bool = True
    ERROR_HELP_BASE_URL: str = "https://docs.example.com/errors"

    # 健康检查配置
    HEALTH_CHECK_ENDPOINT: str = "/health"
    ENABLE_DEPENDENCY_CHECKS: bool = True
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """处理CORS origins配置"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """验证数据库URL"""
        if not v:
            raise ValueError("DATABASE_URL不能为空")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        """验证密钥"""
        if not v or v == "your-secret-key-change-this-in-production":
            # 在开发环境中允许使用默认密钥
            debug_mode = os.getenv("DEBUG", "true").lower() == "true"
            if not debug_mode:
                raise ValueError("生产环境必须设置安全的SECRET_KEY")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
