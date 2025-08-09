"""
# Copyright (c) 2025 左岚. All rights reserved.

用户相关的Pydantic模式
"""

# # Standard library imports
from datetime import datetime
from typing import Optional

# # Third-party imports
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    """
    用户基础模式
    """
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserResponse(UserBase):
    """
    用户响应模式
    """
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """
    用户更新模式
    """
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('姓名不能超过100个字符')
        return v


class ChangePassword(BaseModel):
    """
    修改密码模式
    """
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('新密码至少需要6个字符')
        return v


class UserCreate(UserBase):
    """
    用户创建模式
    """
    password: str
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少需要3个字符')
        if len(v) > 50:
            raise ValueError('用户名不能超过50个字符')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v
