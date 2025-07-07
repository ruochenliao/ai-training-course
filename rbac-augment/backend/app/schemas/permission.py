"""
权限相关Pydantic模式
定义权限相关的请求和响应模式
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PermissionBase(BaseModel):
    """权限基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., min_length=1, max_length=50, description="资源")
    action: str = Field(..., min_length=1, max_length=50, description="操作")
    parent_id: Optional[int] = Field(None, description="父权限ID")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('code')
    def validate_code(cls, v):
        """验证权限代码格式"""
        if ':' not in v:
            raise ValueError('权限代码格式应为 resource:action')
        parts = v.split(':')
        if len(parts) < 2:
            raise ValueError('权限代码格式应为 resource:action')
        return v.lower()
    
    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        valid_actions = ['create', 'read', 'update', 'delete', 'list', 'export', 'import']
        if v.lower() not in valid_actions:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(valid_actions)}')
        return v.lower()


class PermissionCreate(PermissionBase):
    """权限创建模式"""
    pass


class PermissionUpdate(BaseModel):
    """权限更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    parent_id: Optional[int] = Field(None, description="父权限ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PermissionResponse(BaseModel):
    """权限响应模式"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")
    parent_id: Optional[int] = Field(None, description="父权限ID")
    sort_order: int = Field(..., description="排序")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class PermissionTreeResponse(BaseModel):
    """权限树形响应模式"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")
    sort_order: int = Field(..., description="排序")
    is_active: bool = Field(..., description="是否启用")
    children: List["PermissionTreeResponse"] = Field(default_factory=list, description="子权限")
    
    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """权限列表响应模式"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")
    parent_id: Optional[int] = Field(None, description="父权限ID")
    parent_name: Optional[str] = Field(None, description="父权限名称")
    sort_order: int = Field(..., description="排序")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    role_count: int = Field(0, description="拥有此权限的角色数量")
    
    class Config:
        from_attributes = True


class PermissionSelectOption(BaseModel):
    """权限选择选项模式"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    resource: str = Field(..., description="资源")
    action: str = Field(..., description="操作")
    
    class Config:
        from_attributes = True


class PermissionGroupResponse(BaseModel):
    """权限分组响应模式"""
    resource: str = Field(..., description="资源名称")
    permissions: List[PermissionResponse] = Field(..., description="权限列表")


# 更新前向引用
PermissionTreeResponse.model_rebuild()
