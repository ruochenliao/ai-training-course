"""
用户管理API
处理用户的CRUD操作
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from ...schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserDetailResponse,
    UserListResponse, UserPasswordReset, UserRoleAssign, UserOption
)
from ...schemas.common import BaseResponse, PaginationResponse, IDResponse, BulkOperationRequest
from ...crud.user import crud_user
from ...crud.role import crud_role
from ...utils.deps import get_current_user, get_pagination_params, require_user_read, require_user_write, require_user_delete
from ...utils.pagination import create_pagination_response
from ...models.user import User

router = APIRouter()


@router.get("", response_model=BaseResponse, summary="获取用户列表")
async def get_users(
    pagination = Depends(get_pagination_params),
    current_user: User = Depends(require_user_read)
):
    """获取用户列表（分页）"""
    users, total = await crud_user.get_paginated_with_roles(pagination)
    
    pagination_data = create_pagination_response(users, total, pagination)
    
    return BaseResponse(
        message="获取用户列表成功",
        data=pagination_data
    )


@router.get("/stats", response_model=BaseResponse, summary="获取用户统计")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """获取用户统计信息"""
    total_users = await crud_user.count()
    active_users = await User.filter(is_active=True, is_deleted=False).count()
    inactive_users = total_users - active_users

    stats = {
        "total": total_users,
        "active": active_users,
        "inactive": inactive_users
    }

    return BaseResponse(
        message="获取用户统计成功",
        data=stats
    )


@router.post("", response_model=BaseResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_user_write)
):
    """创建新用户"""
    # 检查用户名是否已存在
    if await crud_user.check_username_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if await crud_user.check_email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 验证角色是否存在
    if user_data.role_ids:
        for role_id in user_data.role_ids:
            role = await crud_role.get(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"角色ID {role_id} 不存在"
                )
    
    # 创建用户
    user = await crud_user.create_with_roles(user_data)
    
    return BaseResponse(
        message="用户创建成功",
        data=IDResponse(id=user.id)
    )


@router.get("/options", response_model=BaseResponse[List[UserOption]], summary="获取用户选项列表")
async def get_user_options(
    current_user: User = Depends(get_current_user)
):
    """获取用户选项列表，用于下拉选择等场景"""
    users = await User.filter(is_active=True).order_by('username')

    options = []
    for user in users:
        options.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email
        })

    return BaseResponse(data=options)


@router.get("/{user_id}", response_model=BaseResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_user_read)
):
    """获取用户详情"""
    user = await crud_user.get_with_roles(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取用户权限
    permissions = await user.get_permissions()
    
    # 构建响应数据
    user_detail = UserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        avatar=user.avatar,
        phone=user.phone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[{
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "is_active": role.is_active,
            "sort_order": role.sort_order,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        } for role in user.roles],
        permissions=permissions
    )
    
    return BaseResponse(
        message="获取用户详情成功",
        data=user_detail
    )


@router.put("/{user_id}", response_model=BaseResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_user_write)
):
    """更新用户信息"""
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and await crud_user.check_email_exists(user_data.email, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被其他用户使用"
        )
    
    # 验证角色是否存在
    if user_data.role_ids is not None:
        for role_id in user_data.role_ids:
            role = await crud_role.get(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"角色ID {role_id} 不存在"
                )
    
    # 更新用户
    await crud_user.update_with_roles(user, user_data)
    
    return BaseResponse(message="用户更新成功")


@router.delete("/{user_id}", response_model=BaseResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_user_delete)
):
    """删除用户"""
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除超级用户（除非自己也是超级用户）
    if user.is_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除超级用户"
        )
    
    await crud_user.delete(user_id)
    
    return BaseResponse(message="用户删除成功")


@router.put("/{user_id}/password", response_model=BaseResponse, summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    password_data: UserPasswordReset,
    current_user: User = Depends(require_user_write)
):
    """重置用户密码"""
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await crud_user.update_password(user, password_data.new_password)
    
    return BaseResponse(message="密码重置成功")


@router.post("/{user_id}/roles", response_model=BaseResponse, summary="分配用户角色")
async def assign_user_roles(
    user_id: int,
    role_data: UserRoleAssign,
    current_user: User = Depends(require_user_write)
):
    """为用户分配角色"""
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证角色是否存在
    for role_id in role_data.role_ids:
        role = await crud_role.get(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色ID {role_id} 不存在"
            )
    
    await crud_user.assign_roles(user, role_data.role_ids)
    
    return BaseResponse(message="角色分配成功")


@router.put("/{user_id}/status", response_model=BaseResponse, summary="切换用户状态")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_user_write)
):
    """切换用户激活状态"""
    # 不能操作自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能操作自己的状态"
        )
    
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 切换状态
    if user.is_active:
        await crud_user.deactivate_user(user)
        message = "用户已停用"
    else:
        await crud_user.activate_user(user)
        message = "用户已激活"
    
    return BaseResponse(message=message)


@router.post("/bulk-delete", response_model=BaseResponse, summary="批量删除用户")
async def bulk_delete_users(
    bulk_data: BulkOperationRequest,
    current_user: User = Depends(require_user_delete)
):
    """批量删除用户"""
    # 检查是否包含当前用户
    if current_user.id in bulk_data.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 检查是否包含超级用户
    if not current_user.is_superuser:
        superusers = await crud_user.get_multi_by_field("id", bulk_data.ids)
        for user in superusers:
            if user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权删除超级用户"
                )
    
    deleted_count = await crud_user.delete_multi(bulk_data.ids)
    
    return BaseResponse(
        message=f"成功删除 {deleted_count} 个用户",
        data={"deleted_count": deleted_count}
    )


@router.post("/{user_id}/disable", response_model=BaseResponse, summary="禁用用户")
async def disable_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """禁用用户"""
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user.is_active = False
    await user.save()

    return BaseResponse(message="用户已禁用")


@router.post("/{user_id}/enable", response_model=BaseResponse, summary="启用用户")
async def enable_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """启用用户"""
    user = await crud_user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user.is_active = True
    await user.save()

    return BaseResponse(message="用户已启用")
