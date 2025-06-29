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
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentListResponse,
    RoleListResponse, PermissionListResponse,
    UserRoleAssign, UserRoleResponse,
    UserPermissionAssign, UserPermissionResponse,
    PermissionCheck, PermissionCheckResponse,
    MenuTree
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

    # RBAC schemas
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentListResponse",
    "RoleListResponse",
    "PermissionListResponse",
    "UserRoleAssign",
    "UserRoleResponse",
    "UserPermissionAssign",
    "UserPermissionResponse",
    "PermissionCheck",
    "PermissionCheckResponse",
    "MenuTree",

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
