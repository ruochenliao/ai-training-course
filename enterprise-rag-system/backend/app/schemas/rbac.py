"""
RBAC权限系统Pydantic模式
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator


# ============ 部门相关模式 ============

class DepartmentBase(BaseModel):
    """部门基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=50, description="部门代码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: int = Field(0, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")


class DepartmentCreate(DepartmentBase):
    """创建部门模式"""
    pass


class DepartmentUpdate(BaseModel):
    """更新部门模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: Optional[int] = Field(None, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")
    status: Optional[str] = Field(None, description="状态")


class DepartmentResponse(DepartmentBase):
    """部门响应模式"""
    id: int
    level: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    children: Optional[List["DepartmentResponse"]] = None
    parent: Optional["DepartmentResponse"] = None
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ 角色相关模式 ============

class RoleBase(BaseModel):
    """角色基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    parent_id: Optional[int] = Field(None, description="父角色ID")
    sort_order: int = Field(0, description="排序")
    role_type: str = Field("custom", description="角色类型")
    data_scope: str = Field("custom", description="数据权限范围")


class RoleCreate(RoleBase):
    """创建角色模式"""
    permission_ids: Optional[List[int]] = Field([], description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    parent_id: Optional[int] = Field(None, description="父角色ID")
    sort_order: Optional[int] = Field(None, description="排序")
    data_scope: Optional[str] = Field(None, description="数据权限范围")
    status: Optional[str] = Field(None, description="状态")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleResponse(RoleBase):
    """角色响应模式"""
    id: int
    level: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    permissions: Optional[List["PermissionResponse"]] = None
    children: Optional[List["RoleResponse"]] = None
    parent: Optional["RoleResponse"] = None
    user_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# ============ 权限相关模式 ============

class PermissionBase(BaseModel):
    """权限基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    group: str = Field(..., min_length=1, max_length=50, description="权限分组")
    resource: str = Field(..., min_length=1, max_length=50, description="资源")
    action: str = Field(..., min_length=1, max_length=50, description="操作")
    permission_type: str = Field("api", description="权限类型")
    
    # 菜单相关
    menu_path: Optional[str] = Field(None, max_length=255, description="菜单路径")
    menu_component: Optional[str] = Field(None, max_length=255, description="菜单组件")
    menu_icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: int = Field(0, description="排序")


class PermissionCreate(PermissionBase):
    """创建权限模式"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="权限名称")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    group: Optional[str] = Field(None, min_length=1, max_length=50, description="权限分组")
    resource: Optional[str] = Field(None, min_length=1, max_length=50, description="资源")
    action: Optional[str] = Field(None, min_length=1, max_length=50, description="操作")
    permission_type: Optional[str] = Field(None, description="权限类型")
    menu_path: Optional[str] = Field(None, max_length=255, description="菜单路径")
    menu_component: Optional[str] = Field(None, max_length=255, description="菜单组件")
    menu_icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: Optional[int] = Field(None, description="排序")
    status: Optional[str] = Field(None, description="状态")


class PermissionResponse(PermissionBase):
    """权限响应模式"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    children: Optional[List["PermissionResponse"]] = None
    parent: Optional["PermissionResponse"] = None
    
    class Config:
        from_attributes = True


# ============ 用户角色关联模式 ============

class UserRoleAssign(BaseModel):
    """用户角色分配模式"""
    user_id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(..., description="角色ID列表")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    dept_ids: Optional[List[int]] = Field([], description="数据权限部门ID列表")


class UserRoleResponse(BaseModel):
    """用户角色响应模式"""
    id: int
    user_id: int
    role_id: int
    granted_by: int
    granted_at: datetime
    expires_at: Optional[datetime]
    dept_ids: List[int]
    
    # 关联信息
    role: Optional[RoleResponse] = None
    
    class Config:
        from_attributes = True


# ============ 用户权限关联模式 ============

class UserPermissionAssign(BaseModel):
    """用户权限分配模式"""
    user_id: int = Field(..., description="用户ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")
    permission_type: str = Field("grant", description="权限类型：grant/deny")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class UserPermissionResponse(BaseModel):
    """用户权限响应模式"""
    id: int
    user_id: int
    permission_id: int
    granted_by: int
    granted_at: datetime
    expires_at: Optional[datetime]
    permission_type: str
    
    # 关联信息
    permission: Optional[PermissionResponse] = None
    
    class Config:
        from_attributes = True


# ============ 权限检查模式 ============

class PermissionCheck(BaseModel):
    """权限检查模式"""
    user_id: int = Field(..., description="用户ID")
    permission_codes: List[str] = Field(..., description="权限代码列表")


class PermissionCheckResponse(BaseModel):
    """权限检查响应模式"""
    user_id: int
    permissions: Dict[str, bool]  # 权限代码 -> 是否有权限


# ============ 菜单树模式 ============

class MenuTree(BaseModel):
    """菜单树模式"""
    id: int
    name: str
    code: str
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int
    children: Optional[List["MenuTree"]] = None


# ============ 列表响应模式 ============

class DepartmentListResponse(BaseModel):
    """部门列表响应模式"""
    departments: List[DepartmentResponse]
    total: int


class RoleListResponse(BaseModel):
    """角色列表响应模式"""
    roles: List[RoleResponse]
    total: int
    page: int
    size: int
    pages: int


class PermissionListResponse(BaseModel):
    """权限列表响应模式"""
    permissions: List[PermissionResponse]
    total: int
    page: int
    size: int
    pages: int


# 解决前向引用
DepartmentResponse.model_rebuild()
RoleResponse.model_rebuild()
PermissionResponse.model_rebuild()
MenuTree.model_rebuild()
