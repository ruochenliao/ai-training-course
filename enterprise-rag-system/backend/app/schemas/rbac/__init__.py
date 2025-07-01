"""
RBAC权限系统数据模式模块
"""

from .common import (
    StandardResponse, PaginationResponse, ErrorResponse, SuccessResponse,
    DepartmentListResponse, RoleListResponse, PermissionListResponse, UserRoleListResponse
)
from .department import DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentResponse
from .role import RoleBase, RoleCreate, RoleUpdate, RoleResponse
from .permission import (
    PermissionBase, PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionCheck, PermissionCheckResponse, MenuTree
)
from .user_role import (
    UserRoleAssign, UserRoleResponse, UserPermissionAssign, UserPermissionResponse
)

# 解决前向引用问题
from .permission import PermissionResponse
from .role import RoleResponse
from .department import DepartmentResponse

# 重建模型以解决前向引用
RoleResponse.model_rebuild()
DepartmentResponse.model_rebuild()
PermissionResponse.model_rebuild()

__all__ = [
    # 通用响应
    "StandardResponse",
    "PaginationResponse",
    "ErrorResponse",
    "SuccessResponse",
    "DepartmentListResponse",
    "RoleListResponse",
    "PermissionListResponse",
    "UserRoleListResponse",

    # 部门相关
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",

    # 角色相关
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",

    # 权限相关
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionCheck",
    "PermissionCheckResponse",
    "MenuTree",

    # 用户角色相关
    "UserRoleAssign",
    "UserRoleResponse",
    "UserPermissionAssign",
    "UserPermissionResponse",
]
