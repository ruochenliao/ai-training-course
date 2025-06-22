"""
用户管理API端点
"""

from typing import Any

from app.core.security import get_current_user, get_current_superuser
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前用户信息
    """
    return await current_user.to_dict(exclude_fields=["password_hash"])


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新当前用户信息
    """
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await current_user.save()
    
    return await current_user.to_dict(exclude_fields=["password_hash"])


@router.get("/", response_model=UserListResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="用户状态"),
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    获取用户列表（仅超级用户）
    """
    # 构建查询
    query = User.all()
    
    if search:
        query = query.filter(
            username__icontains=search
        ).union(
            User.filter(email__icontains=search)
        ).union(
            User.filter(full_name__icontains=search)
        )
    
    if status:
        query = query.filter(status=status)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    users = await query.offset(offset).limit(size).order_by("-created_at")
    
    # 转换为响应格式
    user_list = []
    for user in users:
        user_dict = await user.to_dict(exclude_fields=["password_hash"])
        user_list.append(user_dict)
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    获取用户详情（仅超级用户）
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return await user.to_dict(exclude_fields=["password_hash"])


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    更新用户信息（仅超级用户）
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await user.save()
    
    return await user.to_dict(exclude_fields=["password_hash"])


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    删除用户（仅超级用户）
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 软删除
    await user.soft_delete()
    
    return {"message": "用户已删除"}


@router.post("/{user_id}/activate", summary="激活用户")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    激活用户（仅超级用户）
    """
    auth_service = AuthService()
    success = await auth_service.activate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "用户已激活"}


@router.post("/{user_id}/deactivate", summary="停用用户")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    停用用户（仅超级用户）
    """
    auth_service = AuthService()
    success = await auth_service.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "用户已停用"}


@router.post("/{user_id}/lock", summary="锁定用户")
async def lock_user(
    user_id: int,
    duration_minutes: int = 30,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    锁定用户（仅超级用户）
    """
    auth_service = AuthService()
    success = await auth_service.lock_user(user_id, duration_minutes)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": f"用户已锁定 {duration_minutes} 分钟"}


@router.post("/{user_id}/unlock", summary="解锁用户")
async def unlock_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    解锁用户（仅超级用户）
    """
    auth_service = AuthService()
    success = await auth_service.unlock_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "用户已解锁"}


@router.get("/stats/overview", summary="获取用户统计")
async def get_user_stats(
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    获取用户统计信息（仅超级用户）
    """
    auth_service = AuthService()
    stats = await auth_service.get_user_stats()
    
    return stats
