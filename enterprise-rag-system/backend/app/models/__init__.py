"""
数据模型模块
"""

from .base import BaseModel, TimestampMixin
from .conversation import Conversation, Message
from .knowledge import KnowledgeBase, Document, DocumentChunk
from .system import SystemConfig, AuditLog
from .user import User, UserSession, UserEvent
from .rbac import (
    Department, Role, Permission, PermissionGroup,
    UserRole, RolePermission, UserPermission, RoleDepartment
)

__all__ = [
    "BaseModel",
    "TimestampMixin",
    "User",
    "UserSession",
    "UserEvent",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "UserPermission",
    "Department",
    "RoleDepartment",
    "PermissionGroup",
    "KnowledgeBase",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "SystemConfig",
    "AuditLog",
]
