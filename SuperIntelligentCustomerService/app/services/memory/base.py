"""
记忆服务基础类和数据结构
提供统一的记忆服务抽象接口和数据结构定义
"""
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型枚举"""
    CHAT = "chat"           # 聊天历史记忆
    PRIVATE = "private"     # 用户私有记忆
    PUBLIC = "public"       # 公共知识库记忆


class ServiceStatus(Enum):
    """服务状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    memory_type: Optional[MemoryType] = None
    relevance_score: Optional[float] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "relevance_score": self.relevance_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建记忆项"""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            memory_type=MemoryType(data["memory_type"]) if data.get("memory_type") else None,
            relevance_score=data.get("relevance_score")
        )


@dataclass
class QueryResult:
    """查询结果数据结构"""
    items: List[MemoryItem]
    total_count: int
    query_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMemoryService(ABC):
    """
    记忆服务抽象基类
    定义统一的记忆服务接口，支持异步操作和生命周期管理
    """

    def __init__(self, service_id: str, memory_type: MemoryType):
        """
        初始化记忆服务

        Args:
            service_id: 服务唯一标识
            memory_type: 记忆类型
        """
        self.service_id = service_id
        self.memory_type = memory_type
        self.status = ServiceStatus.INITIALIZING
        self.created_at = datetime.now()
        self.last_accessed = None
        self.error_count = 0
        self.total_operations = 0

        # 服务元数据
        self.metadata = {
            "service_id": service_id,
            "memory_type": memory_type.value,
            "created_at": self.created_at.isoformat(),
            "version": "1.0.0"
        }

        logger.info(f"初始化记忆服务: {service_id} (类型: {memory_type.value})")

    @abstractmethod
    async def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加记忆内容

        Args:
            content: 记忆内容
            metadata: 元数据

        Returns:
            记忆项ID
        """
        pass

    @abstractmethod
    async def query(self, query: str, limit: int = 5, **kwargs) -> QueryResult:
        """
        查询记忆内容

        Args:
            query: 查询内容
            limit: 返回数量限制
            **kwargs: 其他查询参数

        Returns:
            查询结果
        """
        pass

    @abstractmethod
    async def clear(self, **kwargs) -> bool:
        """
        清空记忆内容

        Args:
            **kwargs: 清空参数

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭服务，释放资源"""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        return {
            "service_id": self.service_id,
            "memory_type": self.memory_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "error_count": self.error_count,
            "total_operations": self.total_operations,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds()
        }

    def _update_access_time(self):
        """更新最后访问时间"""
        self.last_accessed = datetime.now()
        self.total_operations += 1

    def _handle_error(self, error: Exception):
        """处理错误"""
        self.error_count += 1
        self.status = ServiceStatus.ERROR
        logger.error(f"记忆服务 {self.service_id} 发生错误: {error}")

    def _set_ready(self):
        """设置服务为就绪状态"""
        self.status = ServiceStatus.READY
        logger.info(f"记忆服务 {self.service_id} 已就绪")
