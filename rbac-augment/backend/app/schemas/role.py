"""
角色相关Pydantic模式
定义角色相关的请求和响应模式
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class RoleBase(BaseModel):
    """角色基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(True, description="是否激活")
    sort_order: int = Field(0, description="排序")
    
    @validator('code')
    def validate_code(cls, v):
        """验证角色代码格式"""
        if not v.replace('_', '').isalnum():
            raise ValueError('角色代码只能包含字母、数字和下划线')
        return v.lower()


class RoleCreate(RoleBase):
    """角色创建模式"""
    permission_ids: Optional[List[int]] = Field(default_factory=list, description="权限ID列表")
    menu_ids: Optional[List[int]] = Field(default_factory=list, description="菜单ID列表")


class RoleUpdate(BaseModel):
    """角色更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    sort_order: Optional[int] = Field(None, description="排序")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")
    menu_ids: Optional[List[int]] = Field(None, description="菜单ID列表")


class RolePermissionAssign(BaseModel):
    """角色权限分配模式"""
    permission_ids: List[int] = Field(..., description="权限ID列表")


class RoleMenuAssign(BaseModel):
    """角色菜单分配模式"""
    menu_ids: List[int] = Field(..., description="菜单ID列表")


class RoleResponse(BaseModel):
    """角色响应模式"""
    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(..., description="是否激活")
    sort_order: int = Field(..., description="排序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class RoleDetailResponse(RoleResponse):
    """角色详情响应模式"""
    permissions: List["PermissionResponse"] = Field(default_factory=list, description="角色权限")
    menus: List["MenuResponse"] = Field(default_factory=list, description="角色菜单")
    user_count: int = Field(0, description="拥有此角色的用户数量")


class RoleListResponse(BaseModel):
    """角色列表响应模式"""
    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(..., description="是否激活")
    sort_order: int = Field(..., description="排序")
    created_at: datetime = Field(..., description="创建时间")
    user_count: int = Field(0, description="拥有此角色的用户数量")
    permission_count: int = Field(0, description="权限数量")
    
    class Config:
        from_attributes = True


class RoleSelectOption(BaseModel):
    """角色选择选项模式"""
    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    is_active: bool = Field(..., description="是否激活")
    
    class Config:
        from_attributes = True


# 前向引用
from .permission import PermissionResponse
from .menu import MenuResponse
RoleDetailResponse.model_rebuild()
