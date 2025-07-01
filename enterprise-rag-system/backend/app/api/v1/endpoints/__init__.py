"""
API端点模块
"""

from . import auth
from . import users
from . import knowledge_bases
from . import documents
from . import conversations
from . import chat
from . import search
from . import admin
from . import system
from . import advanced_search
from . import graph
from . import autogen_chat
# rbac 模块已重构为独立模块，不在此处导入
from . import monitoring
from . import permission_management
from . import monitoring_dashboard
from . import database_optimization
from . import cache_management
from . import validation_management
from . import file_upload

__all__ = [
    "auth",
    "users",
    "knowledge_bases",
    "documents",
    "conversations",
    "chat",
    "search",
    "admin",
    "system",
    "advanced_search",
    "graph",
    "autogen_chat",
    # "rbac" 已重构为独立模块
    "monitoring",
    "permission_management",
    "monitoring_dashboard",
    "database_optimization",
    "cache_management",
    "validation_management",
    "file_upload",
]
