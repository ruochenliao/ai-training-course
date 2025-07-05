"""
API v1版本
包含v1版本的所有API路由
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .permissions import router as permissions_router
from .menus import router as menus_router
from .departments import router as departments_router
from .data_permissions import router as data_permissions_router
from .audit_logs import router as audit_logs_router

# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(roles_router, prefix="/roles", tags=["角色管理"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["权限管理"])
api_router.include_router(menus_router, prefix="/menus", tags=["菜单管理"])
api_router.include_router(departments_router, prefix="/departments", tags=["部门管理"])
api_router.include_router(data_permissions_router, prefix="/data-permissions", tags=["数据权限管理"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["审计日志"])
