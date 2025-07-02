"""
认证API
处理用户登录、登出、Token刷新等认证相关操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    UserProfileResponse, UserPasswordUpdate
)
from app.schemas.common import BaseResponse
from app.crud.user import crud_user
from app.core.security import verify_token, generate_token_pair, verify_password, get_password_hash
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=BaseResponse, summary="用户登录")
async def login(login_data: LoginRequest):
    """用户登录"""
    # 验证用户凭据
    user = await crud_user.authenticate(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 更新最后登录时间
    await crud_user.update_last_login(user)
    
    # 生成Token
    tokens = generate_token_pair(user.id)
    
    # 获取用户角色和权限
    await user.fetch_related("roles")
    
    # 构建响应数据
    login_response = LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar": user.avatar,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    )
    
    return BaseResponse(
        message="登录成功",
        data=login_response
    )


@router.post("/refresh", response_model=BaseResponse, summary="刷新Token")
async def refresh_token(refresh_data: RefreshTokenRequest):
    """刷新访问Token"""
    # 验证刷新Token
    user_id = verify_token(refresh_data.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 检查用户是否存在且激活
    user = await crud_user.get(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 生成新的访问Token
    tokens = generate_token_pair(user.id)
    
    refresh_response = RefreshTokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"]
    )
    
    return BaseResponse(
        message="Token刷新成功",
        data=refresh_response
    )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    # 这里可以实现Token黑名单机制
    # 目前只是简单返回成功响应
    return BaseResponse(message="登出成功")


@router.get("/profile", response_model=BaseResponse, summary="获取用户个人资料")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人资料"""
    # 获取用户角色和权限
    await current_user.fetch_related("roles__permissions", "roles__menus")
    
    # 获取用户权限
    permissions = await current_user.get_permissions()
    
    # 获取用户角色
    roles = [role.name for role in current_user.roles]
    
    # 获取用户菜单
    role_ids = [role.id for role in current_user.roles]
    from app.crud.menu import crud_menu
    menus = await crud_menu.get_menu_routes(role_ids)
    
    profile_data = UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar=current_user.avatar,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        roles=roles,
        permissions=permissions,
        menus=menus
    )
    
    return BaseResponse(
        message="获取个人资料成功",
        data=profile_data
    )


@router.put("/password", response_model=BaseResponse, summary="修改密码")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user)
):
    """修改当前用户密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    await crud_user.update_password(current_user, password_data.new_password)
    
    return BaseResponse(message="密码修改成功")


@router.get("/permissions", response_model=BaseResponse, summary="获取用户权限")
async def get_user_permissions(current_user: User = Depends(get_current_user)):
    """获取当前用户权限列表"""
    permissions = await current_user.get_permissions()
    
    return BaseResponse(
        message="获取用户权限成功",
        data=permissions
    )


@router.get("/menus", response_model=BaseResponse, summary="获取用户菜单")
async def get_user_menus(current_user: User = Depends(get_current_user)):
    """获取当前用户菜单"""
    # 获取用户角色ID
    await current_user.fetch_related("roles")
    role_ids = [role.id for role in current_user.roles]
    
    # 获取菜单
    from app.crud.menu import crud_menu
    menus = await crud_menu.get_menu_routes(role_ids)
    
    return BaseResponse(
        message="获取用户菜单成功",
        data=menus
    )
