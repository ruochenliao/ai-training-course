"""
数据模式模块
"""

from .auth import Token, UserLogin, UserRegister
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleBase, RoleCreate, RoleUpdate, RoleResponse,
    PermissionBase, PermissionCreate, PermissionUpdate, PermissionResponse,
    UserRoleResponse
)
from .rbac import (
    # 通用响应
    StandardResponse, PaginationResponse, ErrorResponse, SuccessResponse,
    DepartmentListResponse, RoleListResponse, PermissionListResponse, UserRoleListResponse,
    # 部门相关
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    # 角色相关
    RoleCreate, RoleUpdate, RoleResponse,
    # 权限相关
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionCheck, PermissionCheckResponse, MenuTree,
    # 用户角色相关
    UserRoleAssign, UserRoleResponse,
    UserPermissionAssign, UserPermissionResponse
)
from .document import (
    ProcessingResult, DocumentMetadata, DocumentResponse, DocumentListResponse,
    DocumentUploadResponse, DocumentSearchRequest, DocumentSearchResponse,
    DocumentStats, BatchProcessRequest, BatchProcessResponse
)

__all__ = [
    # Auth schemas
    "Token",
    "UserLogin",
    "UserRegister",

    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",

    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",

    # Permission schemas
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",

    # User Role schemas
    "UserRoleResponse",

    # RBAC通用响应schemas
    "StandardResponse",
    "PaginationResponse",
    "ErrorResponse",
    "SuccessResponse",
    "DepartmentListResponse",
    "RoleListResponse",
    "PermissionListResponse",
    "UserRoleListResponse",

    # RBAC部门schemas
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",

    # RBAC角色schemas
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",

    # RBAC权限schemas
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionCheck",
    "PermissionCheckResponse",
    "MenuTree",

    # RBAC用户角色schemas
    "UserRoleAssign",
    "UserRoleResponse",
    "UserPermissionAssign",
    "UserPermissionResponse",

    # Document schemas
    "ProcessingResult",
    "DocumentMetadata",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUploadResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    "DocumentStats",
    "BatchProcessRequest",
    "BatchProcessResponse",
]
