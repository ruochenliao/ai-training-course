"""
权限相关数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """权限基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    group: str = Field(..., min_length=1, max_length=50, description="权限分组")
    resource: str = Field(..., min_length=1, max_length=50, description="资源")
    action: str = Field(..., min_length=1, max_length=50, description="操作")
    permission_type: str = Field("api", description="权限类型")
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


class PermissionCheck(BaseModel):
    """权限检查请求模式"""
    user_id: int = Field(..., description="用户ID")
    permission_codes: List[str] = Field(..., description="权限代码列表")


class PermissionCheckResponse(BaseModel):
    """权限检查响应模式"""
    user_id: int = Field(..., description="用户ID")
    permissions: dict = Field(..., description="权限检查结果")


class MenuTree(BaseModel):
    """菜单树模式"""
    id: int
    name: str
    code: str
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    children: List["MenuTree"] = []


# 解决前向引用问题
PermissionResponse.model_rebuild()
MenuTree.model_rebuild()
