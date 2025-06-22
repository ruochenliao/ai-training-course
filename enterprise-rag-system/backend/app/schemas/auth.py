"""
认证相关数据模式
"""

from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr, validator


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str
    password: str
    remember_me: Optional[bool] = False
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()
    
    @validator('password')
    def password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        return v


class UserRegister(BaseModel):
    """用户注册模式"""
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
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
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
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


class Token(BaseModel):
    """令牌模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[Dict[str, Any]] = None


class TokenData(BaseModel):
    """令牌数据模式"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: list[str] = []


class PasswordChange(BaseModel):
    """密码修改模式"""
    old_password: str
    new_password: str
    confirm_password: str
    
    @validator('old_password')
    def old_password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('原密码不能为空')
        return v
    
    @validator('new_password')
    def new_password_validation(cls, v):
        if not v:
            raise ValueError('新密码不能为空')
        if len(v) < 6:
            raise ValueError('新密码至少6个字符')
        if len(v) > 128:
            raise ValueError('新密码不能超过128个字符')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v


class PasswordReset(BaseModel):
    """密码重置模式"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认模式"""
    token: str
    new_password: str
    confirm_password: str
    
    @validator('token')
    def token_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('重置令牌不能为空')
        return v.strip()
    
    @validator('new_password')
    def new_password_validation(cls, v):
        if not v:
            raise ValueError('新密码不能为空')
        if len(v) < 6:
            raise ValueError('新密码至少6个字符')
        if len(v) > 128:
            raise ValueError('新密码不能超过128个字符')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v


class EmailVerification(BaseModel):
    """邮箱验证模式"""
    token: str
    
    @validator('token')
    def token_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('验证令牌不能为空')
        return v.strip()


class PhoneVerification(BaseModel):
    """手机验证模式"""
    phone: str
    code: str
    
    @validator('phone')
    def phone_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('手机号不能为空')
        return v.strip()
    
    @validator('code')
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('验证码不能为空')
        return v.strip()


class RefreshToken(BaseModel):
    """刷新令牌模式"""
    refresh_token: str
    
    @validator('refresh_token')
    def refresh_token_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('刷新令牌不能为空')
        return v.strip()
