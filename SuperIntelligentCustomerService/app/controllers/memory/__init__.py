"""
智能体记忆系统模块
基于ChromaDB向量数据库的高质量记忆服务，提供统一的抽象接口和多种实现

核心组件：
- BaseMemoryService: 抽象记忆服务基类
- ChatMemoryService: 聊天历史记忆服务
- PrivateMemoryService: 用户私有向量记忆服务
- PublicMemoryService: 公共知识库记忆服务
- MemoryServiceFactory: 记忆服务工厂，管理服务生命周期
- AutoGenMemoryAdapter: AutoGen Memory协议适配器
"""

# 导入基础类和枚举
from .base import (
    BaseMemoryService,
    MemoryItem,
    MemoryType,
    ServiceStatus,
    QueryResult
)

# 导入具体实现
from .chat_memory import ChatMemoryService
from .private_memory import PrivateMemoryService
from .public_memory import PublicMemoryService

# 导入工厂和适配器
from .factory import MemoryServiceFactory
from .autogen_memory import AutoGenMemoryAdapter, ConversationMemoryAdapter

# 导出所有公共接口
__all__ = [
    # 基础类和枚举
    'BaseMemoryService',
    'MemoryItem',
    'MemoryType',
    'ServiceStatus',
    'QueryResult',

    # 具体实现
    'ChatMemoryService',
    'PrivateMemoryService',
    'PublicMemoryService',

    # 工厂和适配器
    'MemoryServiceFactory',
    'AutoGenMemoryAdapter',
    'ConversationMemoryAdapter'
]

# 版本信息
__version__ = "2.0.0"
__author__ = "Intelligent Customer Service Team"
__description__ = "智能体记忆系统 - 基于向量数据库的高质量记忆服务"
