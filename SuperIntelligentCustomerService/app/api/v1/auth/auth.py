from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.models.admin import User
from app.schemas import Success, Fail
from app.schemas.auth import LoginDTO, RegisterDTO, EmailCodeDTO, LoginVO, LoginUser
from app.settings import settings
from app.utils.jwt import create_access_token
from app.utils.password import get_password_hash, verify_password
from app.schemas.login import JWTPayload

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/login", summary="用户登录")
async def login(credentials: LoginDTO):
    """用户登录接口"""
    try:
        # 验证用户凭据
        user = await user_controller.authenticate_by_username(credentials.username, credentials.password)
        if not user:
            return Fail(msg="用户名或密码错误")
        
        if not user.is_active:
            return Fail(msg="用户账户已被禁用")
        
        # 更新最后登录时间
        await user_controller.update_last_login(user.id)
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires
        
        access_token = create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        )
        
        # 构建用户信息
        user_info = LoginUser(
            user_id=user.id,
            username=user.username,
            nick_name=user.alias or user.username,
            dept_id=user.dept_id,
            token=access_token,
            login_time=int(datetime.now().timestamp()),
            expire_time=int(expire.timestamp())
        )
        
        login_vo = LoginVO(
            access_token=access_token,
            token=access_token,
            user_info=user_info
        )
        
        return Success(data=login_vo.model_dump())
        
    except Exception as e:
        return Fail(msg=f"登录失败: {str(e)}")


@router.post("/register", summary="用户注册")
async def register(register_data: RegisterDTO):
    """用户注册接口"""
    try:
        # 检查用户是否已存在
        existing_user = await user_controller.get_by_email(register_data.username)
        if existing_user:
            return Fail(msg="该邮箱已被注册")
        
        # 验证密码确认
        if register_data.confirm_password and register_data.password != register_data.confirm_password:
            return Fail(msg="两次输入的密码不一致")
        
        # TODO: 验证邮箱验证码
        # 这里应该验证验证码的有效性
        
        # 创建新用户
        hashed_password = get_password_hash(register_data.password)
        user_data = {
            "username": register_data.username.split("@")[0],  # 使用邮箱前缀作为用户名
            "email": register_data.username,
            "password": hashed_password,
            "is_active": True,
            "is_superuser": False
        }
        
        user = await user_controller.create_user(user_data)
        
        return Success(msg="注册成功", data={"user_id": user.id})
        
    except Exception as e:
        return Fail(msg=f"注册失败: {str(e)}")


@router.post("/email/code", summary="发送邮箱验证码")
async def send_email_code(email_data: EmailCodeDTO):
    """发送邮箱验证码"""
    try:
        # TODO: 实现邮箱验证码发送逻辑
        # 这里应该：
        # 1. 生成6位数字验证码
        # 2. 将验证码存储到Redis或数据库中，设置过期时间
        # 3. 发送邮件
        
        # 模拟发送成功
        return Success(msg="验证码已发送到您的邮箱，请查收")
        
    except Exception as e:
        return Fail(msg=f"发送验证码失败: {str(e)}")


# 添加用户控制器的辅助方法
async def authenticate_by_username(username: str, password: str) -> Optional[User]:
    """通过用户名或邮箱认证用户"""
    # 尝试通过用户名查找
    user = await User.filter(username=username).first()
    if not user:
        # 尝试通过邮箱查找
        user = await User.filter(email=username).first()

    if user and verify_password(password, user.password):
        return user
    return None


async def get_by_email(email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return await User.filter(email=email).first()


async def create_user_account(user_data: dict) -> User:
    """创建用户"""
    return await User.create(**user_data)


async def update_last_login(user_id: int):
    """更新最后登录时间"""
    from datetime import datetime
    await User.filter(id=user_id).update(updated_at=datetime.now())


# 将方法添加到用户控制器
user_controller.authenticate_by_username = authenticate_by_username
user_controller.get_by_email = get_by_email
user_controller.create_user = create_user_account
user_controller.update_last_login = update_last_login
