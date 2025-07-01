"""
认证相关API端点
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.services.auth import AuthService
from app.core import create_access_token, get_current_user
from app.core import settings
from app.core.response import Response
from app.models import User
from app.schemas import Token, UserLogin, UserRegister
from app.schemas import UserResponse

router = APIRouter()


@router.post("/register", summary="用户注册")
async def register(user_data: UserRegister):
    """
    用户注册
    """
    auth_service = AuthService()

    # 检查用户名是否已存在
    existing_user = await User.get_or_none(username=user_data.username)
    if existing_user:
        return Response.bad_request("用户名已存在")

    # 检查邮箱是否已存在
    existing_email = await User.get_or_none(email=user_data.email)
    if existing_email:
        return Response.bad_request("邮箱已存在")

    # 创建用户
    user = await auth_service.create_user(user_data)
    user_dict = await user.to_dict()
    return Response.created(data=user_dict, msg="注册成功")


@router.post("/login", summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录
    """
    auth_service = AuthService()

    # 验证用户
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        return Response.unauthorized("用户名或密码错误")

    # 检查账户状态
    if user.is_locked():
        return Response.error("账户已被锁定，请稍后再试", code=423)

    if not user.is_active():
        return Response.forbidden("账户未激活")

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # 记录登录
    user.record_login()
    await user.save()

    # 构建响应数据
    token_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }
    }

    return Response.success(data=token_data, msg="登录成功")


@router.post("/login/json", response_model=Token, summary="JSON登录")
async def login_json(user_data: UserLogin) -> Any:
    """
    JSON格式登录
    """
    auth_service = AuthService()
    
    # 验证用户
    user = await auth_service.authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查账户状态
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账户已被锁定，请稍后再试"
        )
    
    if not user.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # 记录登录
    user.record_login()
    await user.save()
    
    # 手动构建用户信息，避免序列化问题
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_info
    }


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)) -> Any:
    """
    用户登出
    """
    # 这里可以实现令牌黑名单等逻辑
    return {"message": "登出成功"}


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """
    获取当前用户信息
    """
    # 手动构建用户信息，避免序列化问题
    user_info = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "phone": current_user.phone,
        "is_email_verified": current_user.is_email_verified,
        "is_phone_verified": current_user.is_phone_verified,
        "is_superuser": current_user.is_superuser,
        "is_staff": current_user.is_staff,
        "status": current_user.status,
        "language": current_user.language,
        "timezone": current_user.timezone,
        "theme": current_user.theme,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "login_count": current_user.login_count
    }
    return user_info


@router.post("/refresh", response_model=Token, summary="刷新令牌")
async def refresh_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    刷新访问令牌
    """
    # 生成新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": await current_user.to_dict(exclude_fields=["password_hash"])
    }


@router.post("/change-password", summary="修改密码")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    修改密码
    """
    # 验证旧密码
    if not current_user.verify_password(old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 设置新密码
    current_user.set_password(new_password)
    await current_user.save()
    
    return {"message": "密码修改成功"}


@router.post("/forgot-password", summary="忘记密码")
async def forgot_password(email: str) -> Any:
    """
    忘记密码
    """
    # 查找用户
    user = await User.get_or_none(email=email)
    if not user:
        # 为了安全，不暴露用户是否存在
        return {"message": "如果邮箱存在，重置链接已发送"}
    
    # 这里应该发送重置密码邮件
    # 实际实现需要邮件服务
    
    return {"message": "如果邮箱存在，重置链接已发送"}


@router.post("/reset-password", summary="重置密码")
async def reset_password(token: str, new_password: str) -> Any:
    """
    重置密码
    """
    # 这里应该验证重置令牌
    # 实际实现需要令牌验证逻辑
    
    return {"message": "密码重置成功"}
