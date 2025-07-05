"""
数据模型包
包含所有Tortoise ORM数据模型
"""

from .base import BaseModel
from .user import User
from .role import Role
from .permission import Permission
from .menu import Menu
from .department import Department
from .data_permission import DataPermission, UserDataPermission, RoleDataPermission

__all__ = [
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "Menu",
    "Department",
    "DataPermission",
    "UserDataPermission",
    "RoleDataPermission"
]
