"""
RBAC权限系统API路由模块
"""

from fastapi import APIRouter

from . import departments, roles, permissions, user_roles, permission_check

# 创建RBAC路由器
rbac_router = APIRouter()

# 注册子路由
rbac_router.include_router(departments.router, prefix="/departments", tags=["部门管理"])
rbac_router.include_router(roles.router, prefix="/roles", tags=["角色管理"])
rbac_router.include_router(permissions.router, prefix="/permissions", tags=["权限管理"])
rbac_router.include_router(user_roles.router, prefix="/user_roles", tags=["用户角色管理"])
rbac_router.include_router(permission_check.router, prefix="/permission_check", tags=["权限检查"])

__all__ = ["rbac_router"]
