"""
核心配置模块
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    PROJECT_NAME: str = "企业级Agent+RAG知识库系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30天
    ALGORITHM: str = "HS256"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = []
    ALLOWED_HOSTS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            elif not v.startswith("["):
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []
    
    # 数据库配置
    DATABASE_URL: str = "mysql://root:password@localhost:3306/enterprise_rag?charset=utf8mb4"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1小时
    
    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_DATABASE: str = "default"
    MILVUS_COLLECTION_NAME: str = "knowledge_base_vectors"

    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "enterprise-rag"
    MINIO_SECURE: bool = False
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # AI模型配置
    # LLM配置
    LLM_MODEL_NAME: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_API_KEY: str = ""
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1
    
    # VLM配置
    VLM_MODEL_NAME: str = "qwen-vl-max"
    VLM_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    VLM_API_KEY: str = ""
    
    # 嵌入模型配置
    EMBEDDING_MODEL_NAME: str = "text-embedding-v1"
    EMBEDDING_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_BATCH_SIZE: int = 100
    
    # 重排模型配置
    RERANKER_MODEL_NAME: str = "gte-rerank"
    RERANKER_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    RERANKER_API_KEY: str = ""
    
    # AutoGen配置
    AUTOGEN_CONFIG_LIST: List[Dict[str, Any]] = [
        {
            "model": "deepseek-chat",
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "api_type": "openai",
        }
    ]
    
    # 文档处理配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FILE_TYPES: List[str] = [
        ".pdf", ".docx", ".pptx", ".txt", ".md",
        ".html", ".csv", ".xlsx", ".json"
    ]

    @field_validator("SUPPORTED_FILE_TYPES", mode="before")
    @classmethod
    def parse_supported_file_types(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    # 分块配置
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    CHUNK_STRATEGY: str = "semantic"  # semantic, recursive, fixed
    
    # 检索配置
    DEFAULT_TOP_K: int = 10
    DEFAULT_SCORE_THRESHOLD: float = 0.7
    MAX_SEARCH_RESULTS: int = 50
    
    # 图谱配置
    GRAPH_MAX_DEPTH: int = 3
    GRAPH_MAX_NODES: int = 100

    # 实体抽取配置
    ENTITY_EXTRACTION_ENABLED: bool = True
    ENTITY_EXTRACTION_BATCH_SIZE: int = 10
    ENTITY_EXTRACTION_TIMEOUT: int = 30

    # 高级搜索配置
    SEARCH_MAX_CONCURRENT: int = 5
    SEARCH_TIMEOUT: int = 30
    SEARCH_DEFAULT_TOP_K: int = 10
    SEARCH_ENABLE_RERANK: bool = True
    SEARCH_RERANK_TOP_K: int = 20

    # 智能问答配置
    QA_MAX_CONTEXT_LENGTH: int = 8000
    QA_MAX_SOURCES: int = 10
    QA_CONFIDENCE_THRESHOLD: float = 0.7
    QA_ENABLE_STREAM: bool = True

    # Marker文档解析配置
    MARKER_ENABLED: bool = True
    MARKER_MAX_PAGES: Optional[int] = None
    MARKER_LANGUAGES: List[str] = ["Chinese", "English"]
    MARKER_BATCH_MULTIPLIER: int = 2

    @field_validator("MARKER_LANGUAGES", mode="before")
    @classmethod
    def parse_marker_languages(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v
    
    # 缓存配置
    CACHE_TTL_SHORT: int = 300  # 5分钟
    CACHE_TTL_MEDIUM: int = 1800  # 30分钟
    CACHE_TTL_LONG: int = 3600  # 1小时
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @field_validator("EMAILS_FROM_NAME", mode="before")
    @classmethod
    def get_project_name(cls, v: Optional[str]) -> str:
        if not v:
            return "企业级Agent+RAG知识库系统"  # 默认项目名称
        return v
    
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "app/email-templates/build"
    EMAILS_ENABLED: bool = False
    
    @model_validator(mode="after")
    def validate_emails_enabled(self) -> "Settings":
        if not self.EMAILS_ENABLED:
            self.EMAILS_ENABLED = bool(
                self.SMTP_HOST
                and self.SMTP_PORT
                and self.EMAILS_FROM_EMAIL
            )
        return self
    
    # 测试配置
    TEST_DATABASE_URL: str = "sqlite://./test.db"
    
    # 环境变量
    ENVIRONMENT: str = "development"  # development, staging, production
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_parse_none_str": "None",
        "env_parse_enums": True,
        "extra": "ignore",  # 忽略额外的字段
        "json_schema_extra": {
            "env_prefix": "",
        }
    }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # 自定义设置源，避免复杂类型的 JSON 解析
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


# 创建全局配置实例
settings = Settings()
