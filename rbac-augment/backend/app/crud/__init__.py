"""
CRUD操作包
包含所有数据库CRUD操作类
"""

from .base import CRUDBase
from .user import crud_user
from .role import crud_role
from .permission import crud_permission
from .menu import crud_menu
from .audit_log import CRUDAuditLog
from .department import crud_department

__all__ = [
    "CRUDBase",
    "crud_user",
    "crud_role",
    "crud_permission",
    "crud_menu",
    "crud_department"
]
