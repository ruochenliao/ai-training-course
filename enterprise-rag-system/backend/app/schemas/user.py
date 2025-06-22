"""
用户相关数据模式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    language: Optional[str] = "zh-CN"
    timezone: Optional[str] = "Asia/Shanghai"
    theme: Optional[str] = "light"


class UserCreate(UserBase):
    """用户创建模式"""
    password: str
    
    @validator('username')
    def username_validation(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        if len(v.strip()) < 3:
            raise ValueError('用户名至少3个字符')
        if len(v.strip()) > 50:
            raise ValueError('用户名不能超过50个字符')
        return v.strip()
    
    @validator('password')
    def password_validation(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        if len(v) < 6:
            raise ValueError('密码至少6个字符')
        if len(v) > 128:
            raise ValueError('密码不能超过128个字符')
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    
    @validator('full_name')
    def full_name_validation(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError('姓名不能超过100个字符')
        return v.strip() if v else None
    
    @validator('phone')
    def phone_validation(cls, v):
        if v and len(v.strip()) > 20:
            raise ValueError('手机号不能超过20个字符')
        return v.strip() if v else None
    
    @validator('bio')
    def bio_validation(cls, v):
        if v and len(v.strip()) > 500:
            raise ValueError('个人简介不能超过500个字符')
        return v.strip() if v else None
    
    @validator('avatar_url')
    def avatar_url_validation(cls, v):
        if v and len(v.strip()) > 500:
            raise ValueError('头像URL不能超过500个字符')
        return v.strip() if v else None


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_email_verified: bool = False
    is_phone_verified: bool = False
    is_superuser: bool = False
    is_staff: bool = False
    status: str
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    theme: str = "light"
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应模式"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserProfile(BaseModel):
    """用户档案模式"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_email_verified: bool = False
    is_phone_verified: bool = False
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    theme: str = "light"
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """用户统计模式"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    login_count_today: int
    login_count_this_week: int
    login_count_this_month: int


class RoleBase(BaseModel):
    """角色基础模式"""
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int = 0
    sort_order: int = 0


class RoleCreate(RoleBase):
    """角色创建模式"""
    pass


class RoleUpdate(BaseModel):
    """角色更新模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class RoleResponse(BaseModel):
    """角色响应模式"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """权限基础模式"""
    name: str
    code: str
    description: Optional[str] = None
    group: str
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """权限创建模式"""
    pass


class PermissionUpdate(BaseModel):
    """权限更新模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    group: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None


class PermissionResponse(BaseModel):
    """权限响应模式"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    group: str
    resource: str
    action: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    """用户角色分配模式"""
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None


class UserRoleResponse(BaseModel):
    """用户角色响应模式"""
    id: int
    user_id: int
    role_id: int
    role: RoleResponse
    granted_by: int
    granted_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RolePermissionAssign(BaseModel):
    """角色权限分配模式"""
    role_id: int
    permission_id: int


class UserSessionResponse(BaseModel):
    """用户会话响应模式"""
    id: int
    session_id: str
    ip_address: str
    user_agent: str
    device_info: Dict[str, Any]
    is_active: bool
    last_activity_at: datetime
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
