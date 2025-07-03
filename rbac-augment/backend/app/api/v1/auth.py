"""
认证API
处理用户登录、登出、Token刷新等认证相关操作
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from ...schemas.user import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    UserProfileResponse, UserPasswordUpdate, UserCreate, UserProfileUpdate
)
from ...schemas.common import BaseResponse
from ...crud.user import crud_user
from ...core.security import verify_token, generate_token_pair, verify_password, get_password_hash
from ...utils.deps import get_current_user
from ...models.user import User
import os
import uuid
from pathlib import Path

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
            "last_login_at": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    )
    
    return BaseResponse(
        message="登录成功",
        data=login_response
    )


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(user_data: UserCreate):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = await crud_user.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = await crud_user.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )

    # 创建用户
    user = await crud_user.create_with_roles(user_data)

    return BaseResponse(
        message="注册成功",
        data={"id": user.id, "username": user.username}
    )


@router.get("/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    user_data = await current_user.to_dict()
    return BaseResponse(
        message="获取用户信息成功",
        data=user_data
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


@router.put("/profile", response_model=BaseResponse, summary="更新个人资料")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新当前用户个人资料"""
    # 检查邮箱是否已被其他用户使用
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = await crud_user.get_by_email(profile_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )

    # 检查用户名是否已被其他用户使用
    if profile_data.username and profile_data.username != current_user.username:
        existing_user = await crud_user.get_by_username(profile_data.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被其他用户使用"
            )

    # 更新用户信息
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await current_user.save()

    return BaseResponse(message="个人资料更新成功")


@router.post("/avatar", response_model=BaseResponse, summary="上传头像")
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传用户头像"""
    # 检查文件类型
    if not avatar.content_type or not avatar.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持图片文件"
        )

    # 检查文件大小（2MB）
    if avatar.size and avatar.size > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过2MB"
        )

    # 创建上传目录
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_extension = avatar.filename.split('.')[-1] if avatar.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / filename

    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            content = await avatar.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败"
        )

    # 删除旧头像文件（如果存在）
    if current_user.avatar and current_user.avatar.startswith('/uploads/'):
        old_file_path = Path(current_user.avatar.lstrip('/'))
        if old_file_path.exists():
            try:
                old_file_path.unlink()
            except:
                pass  # 忽略删除失败

    # 更新用户头像路径
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar = avatar_url
    await current_user.save()

    return BaseResponse(
        message="头像上传成功",
        data={"avatar_url": avatar_url}
    )


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
