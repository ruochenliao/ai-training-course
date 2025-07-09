from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr


class LoginDTO(BaseModel):
    username: str = Field(..., description="用户名", example="admin")
    password: str = Field(..., description="密码", example="123456")
    code: Optional[str] = Field(None, description="验证码")
    confirm_password: Optional[str] = Field(None, description="确认密码")


class RegisterDTO(BaseModel):
    username: EmailStr = Field(..., description="邮箱", example="user@example.com")
    password: str = Field(..., description="密码", example="123456")
    code: str = Field(..., description="验证码", example="123456")
    confirm_password: Optional[str] = Field(None, description="确认密码")


class EmailCodeDTO(BaseModel):
    username: Optional[str] = Field(None, description="用户名/邮箱")


class RoleDTO(BaseModel):
    role_id: Optional[int] = Field(None, description="角色ID")
    role_name: Optional[str] = Field(None, description="角色名称")
    role_key: Optional[str] = Field(None, description="角色权限")
    data_scope: Optional[str] = Field(None, description="数据范围")


class LoginUser(BaseModel):
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    nick_name: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像")
    dept_id: Optional[int] = Field(None, description="部门ID")
    dept_name: Optional[str] = Field(None, description="部门名")
    role_id: Optional[int] = Field(None, description="角色ID")
    roles: Optional[List[RoleDTO]] = Field(None, description="角色列表")
    menu_permission: Optional[List[str]] = Field(None, description="菜单权限")
    role_permission: Optional[List[str]] = Field(None, description="角色权限")
    token: Optional[str] = Field(None, description="令牌")
    login_id: Optional[str] = Field(None, description="登录ID")
    login_time: Optional[int] = Field(None, description="登录时间")
    expire_time: Optional[int] = Field(None, description="过期时间")
    ipaddr: Optional[str] = Field(None, description="登录IP")
    login_location: Optional[str] = Field(None, description="登录地点")
    browser: Optional[str] = Field(None, description="浏览器")
    os: Optional[str] = Field(None, description="操作系统")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    user_type: Optional[str] = Field(None, description="用户类型")


class LoginVO(BaseModel):
    access_token: Optional[str] = Field(None, description="访问令牌")
    token: Optional[str] = Field(None, description="令牌")
    user_info: Optional[LoginUser] = Field(None, description="用户信息")
