"""
配置模块
统一管理所有应用配置
"""

from .base import settings
from .database import DatabaseConfig
from .auth import AuthConfig
from .ai import AIConfig
from .autogen import AutoGenConfig

__all__ = [
    "settings",
    "DatabaseConfig", 
    "AuthConfig",
    "AIConfig",
    "AutoGenConfig"
]
