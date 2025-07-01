"""
RBAC权限系统服务模块
"""

from .department_service import DepartmentService
from .role_service import RoleService
from .permission_service import PermissionService
from .user_role_service import UserRoleService

__all__ = [
    "DepartmentService",
    "RoleService",
    "PermissionService",
    "UserRoleService",
]
