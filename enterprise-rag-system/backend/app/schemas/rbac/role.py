"""
角色相关数据模式
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .permission import PermissionResponse


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


# 解决前向引用问题将在__init__.py中处理
