"""
用户相关Pydantic模式
定义用户相关的请求和响应模式
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    is_active: bool = Field(True, description="是否激活")


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role_ids: Optional[List[int]] = Field(default_factory=list, description="角色ID列表")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")


class UserPasswordUpdate(BaseModel):
    """用户密码更新模式"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证密码确认"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserPasswordReset(BaseModel):
    """用户密码重置模式"""
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UserProfileUpdate(BaseModel):
    """用户个人资料更新模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")

    @validator('phone')
    def validate_phone(cls, v):
        """验证手机号格式"""
        if v and not v.isdigit():
            raise ValueError('手机号只能包含数字')
        return v


class UserRoleAssign(BaseModel):
    """用户角色分配模式"""
    role_ids: List[int] = Field(..., description="角色ID列表")


class UserResponse(UserBase):
    """用户响应模式"""
    id: int = Field(..., description="用户ID")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """用户详情响应模式"""
    roles: List["RoleResponse"] = Field(default_factory=list, description="用户角色")
    permissions: List[str] = Field(default_factory=list, description="用户权限")


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    role_names: List[str] = Field(default_factory=list, description="角色名称列表")
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")


class LoginResponse(BaseModel):
    """登录响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模式"""
    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserProfileResponse(UserResponse):
    """用户个人资料响应模式"""
    roles: List[str] = Field(default_factory=list, description="角色列表")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    menus: List[dict] = Field(default_factory=list, description="菜单列表")


# 前向引用
from .role import RoleResponse
UserDetailResponse.model_rebuild()
