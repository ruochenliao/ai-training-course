"""
数据库配置
"""
from typing import Dict, Any
from .base import settings


class DatabaseConfig:
    """数据库配置类"""
    
    @staticmethod
    def get_engine_config() -> Dict[str, Any]:
        """获取数据库引擎配置"""
        return {
            "url": settings.database_url,
            "echo": settings.database_echo,
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_recycle": settings.database_pool_recycle,
            "pool_pre_ping": True,
        }
    
    @staticmethod
    def get_session_config() -> Dict[str, Any]:
        """获取会话配置"""
        return {
            "autocommit": False,
            "autoflush": False,
            "expire_on_commit": False,
        }
    
    @staticmethod
    def get_alembic_config() -> Dict[str, Any]:
        """获取Alembic迁移配置"""
        return {
            "script_location": "alembic",
            "sqlalchemy.url": settings.database_url,
            "file_template": "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s",
            "timezone": "UTC",
        }
    
    @staticmethod
    def get_connection_test_query() -> str:
        """获取连接测试查询"""
        return "SELECT 1"
    
    @staticmethod
    def is_mysql() -> bool:
        """检查是否为MySQL数据库"""
        return "mysql" in settings.database_url.lower()
    
    @staticmethod
    def is_postgresql() -> bool:
        """检查是否为PostgreSQL数据库"""
        return "postgresql" in settings.database_url.lower()
    
    @staticmethod
    def is_sqlite() -> bool:
        """检查是否为SQLite数据库"""
        return "sqlite" in settings.database_url.lower()
    
    @staticmethod
    def get_database_name() -> str:
        """获取数据库名称"""
        try:
            # 从URL中提取数据库名
            url_parts = settings.database_url.split("/")
            if len(url_parts) > 1:
                db_name = url_parts[-1]
                # 移除查询参数
                if "?" in db_name:
                    db_name = db_name.split("?")[0]
                return db_name
            return "ai_document"
        except Exception:
            return "ai_document"
