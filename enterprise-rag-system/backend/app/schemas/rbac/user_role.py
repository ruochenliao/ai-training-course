"""
用户角色相关数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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
    expires_at: Optional[datetime] = None
    dept_ids: List[int] = []
    
    # 关联信息
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    granted_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


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
    expires_at: Optional[datetime] = None
    permission_type: str = "grant"
    
    # 关联信息
    user_name: Optional[str] = None
    permission_name: Optional[str] = None
    permission_code: Optional[str] = None
    granted_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True
