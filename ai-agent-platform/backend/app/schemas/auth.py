"""
认证相关的Pydantic模式
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class UserLogin(BaseModel):
    """
    用户登录模式
    """
    username: str
    password: str


class UserCreate(BaseModel):
    """
    用户创建模式
    """
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
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


class UserInToken(BaseModel):
    """
    Token中的用户信息
    """
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool


class Token(BaseModel):
    """
    Token响应模式
    """
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserInToken] = None


class TokenPayload(BaseModel):
    """
    Token载荷模式
    """
    sub: Optional[str] = None
    exp: Optional[int] = None


class UserResponse(BaseModel):
    """
    用户响应模式
    """
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
