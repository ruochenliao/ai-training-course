"""
数据模型包
包含所有Tortoise ORM数据模型
"""

from app.models.base import BaseModel
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.menu import Menu
from app.models.department import Department

__all__ = [
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "Menu",
    "Department"
]
