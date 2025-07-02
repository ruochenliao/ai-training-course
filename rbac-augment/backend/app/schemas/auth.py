from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名/邮箱")
    password: str = Field(..., description="密码")
    
    @validator("password")
    def password_length(cls, v):
        """验证密码长度"""
        if len(v) < 6:
            raise ValueError("密码长度不能少于6个字符")
        return v


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    refresh_token: str = Field(..., description="刷新令牌")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenData(BaseModel):
    """令牌数据模型，用于JWT解析"""
    user_id: int
    username: str
    is_superuser: bool
    exp: Optional[int] = None 