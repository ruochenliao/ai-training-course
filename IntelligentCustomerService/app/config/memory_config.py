"""
记忆服务配置
"""
import os
from typing import Dict, Any


class MemoryConfig:
    """记忆服务配置"""
    
    # 数据库配置
    DATABASE_PATH: str = os.getenv("MEMORY_DB_PATH", "./customer_service.db")
    
    # 记忆限制
    MAX_CHAT_MEMORIES_PER_USER: int = int(os.getenv("MAX_CHAT_MEMORIES_PER_USER", "1000"))
    MAX_PRIVATE_MEMORIES_PER_USER: int = int(os.getenv("MAX_PRIVATE_MEMORIES_PER_USER", "500"))
    MAX_PUBLIC_MEMORIES: int = int(os.getenv("MAX_PUBLIC_MEMORIES", "10000"))
    
    # 检索配置
    DEFAULT_RETRIEVAL_LIMIT: int = int(os.getenv("DEFAULT_RETRIEVAL_LIMIT", "5"))
    RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.1"))
    
    # 嵌入向量配置
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "100"))
    
    # 清理配置
    CHAT_MEMORY_RETENTION_DAYS: int = int(os.getenv("CHAT_MEMORY_RETENTION_DAYS", "30"))
    PRIVATE_MEMORY_RETENTION_DAYS: int = int(os.getenv("PRIVATE_MEMORY_RETENTION_DAYS", "365"))
    
    # AutoGen Memory配置
    AUTOGEN_MEMORY_ENABLED: bool = os.getenv("AUTOGEN_MEMORY_ENABLED", "true").lower() == "true"
    AUTOGEN_MEMORY_CONTEXT_LIMIT: int = int(os.getenv("AUTOGEN_MEMORY_CONTEXT_LIMIT", "3"))
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "database_path": cls.DATABASE_PATH,
            "max_chat_memories_per_user": cls.MAX_CHAT_MEMORIES_PER_USER,
            "max_private_memories_per_user": cls.MAX_PRIVATE_MEMORIES_PER_USER,
            "max_public_memories": cls.MAX_PUBLIC_MEMORIES,
            "default_retrieval_limit": cls.DEFAULT_RETRIEVAL_LIMIT,
            "relevance_threshold": cls.RELEVANCE_THRESHOLD,
            "embedding_dimension": cls.EMBEDDING_DIMENSION,
            "chat_memory_retention_days": cls.CHAT_MEMORY_RETENTION_DAYS,
            "private_memory_retention_days": cls.PRIVATE_MEMORY_RETENTION_DAYS,
            "autogen_memory_enabled": cls.AUTOGEN_MEMORY_ENABLED,
            "autogen_memory_context_limit": cls.AUTOGEN_MEMORY_CONTEXT_LIMIT
        }


# 全局配置实例
memory_config = MemoryConfig()
