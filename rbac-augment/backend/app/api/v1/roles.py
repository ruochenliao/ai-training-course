"""
角色管理API
处理角色的CRUD操作
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ...schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse,
    RoleListResponse, RolePermissionAssign, RoleMenuAssign, RoleSelectOption
)
from ...schemas.common import BaseResponse, PaginationResponse, IDResponse, BulkOperationRequest
from ...crud.role import crud_role
from ...crud.permission import crud_permission
from ...crud.menu import crud_menu
from ...utils.deps import get_current_user, get_pagination_params, require_role_read, require_role_write, require_role_delete
from ...utils.pagination import create_pagination_response
from ...models.user import User

router = APIRouter()


@router.get("", response_model=BaseResponse, summary="获取角色列表")
async def get_roles(
    pagination = Depends(get_pagination_params),
    current_user: User = Depends(require_role_read)
):
    """获取角色列表（分页）"""
    roles, total = await crud_role.get_paginated_with_stats(pagination)
    
    pagination_data = create_pagination_response(roles, total, pagination)
    
    return BaseResponse(
        message="获取角色列表成功",
        data=pagination_data
    )


@router.post("", response_model=BaseResponse, summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role_write)
):
    """创建新角色"""
    # 检查角色代码是否已存在
    if await crud_role.check_code_exists(role_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色代码已存在"
        )
    
    # 检查角色名称是否已存在
    if await crud_role.check_name_exists(role_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名称已存在"
        )
    
    # 验证权限是否存在
    if role_data.permission_ids:
        for permission_id in role_data.permission_ids:
            permission = await crud_permission.get(permission_id)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限ID {permission_id} 不存在"
                )
    
    # 验证菜单是否存在
    if role_data.menu_ids:
        for menu_id in role_data.menu_ids:
            menu = await crud_menu.get(menu_id)
            if not menu:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"菜单ID {menu_id} 不存在"
                )
    
    # 创建角色
    role = await crud_role.create_with_permissions(role_data)
    
    return BaseResponse(
        message="角色创建成功",
        data=IDResponse(id=role.id)
    )


@router.get("/options", response_model=BaseResponse, summary="获取角色选项")
async def get_role_options_list(
    current_user: User = Depends(require_role_read)
):
    """获取角色选项列表（用于下拉选择）"""
    roles = await crud_role.get_active_roles()

    role_options = [
        {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description
        }
        for role in roles
    ]

    return BaseResponse(
        message="获取角色选项成功",
        data=role_options
    )


@router.get("/{role_id}", response_model=BaseResponse, summary="获取角色详情")
async def get_role(
    role_id: int,
    current_user: User = Depends(require_role_read)
):
    """获取角色详情"""
    role = await crud_role.get_with_permissions(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 获取用户数量
    user_count = await role.get_user_count()
    
    # 构建响应数据
    role_detail = RoleDetailResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_active=role.is_active,
        sort_order=role.sort_order,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[{
            "id": perm.id,
            "name": perm.name,
            "code": perm.code,
            "description": perm.description,
            "resource": perm.resource,
            "action": perm.action,
            "parent_id": perm.parent_id,
            "sort_order": perm.sort_order,
            "created_at": perm.created_at,
            "updated_at": perm.updated_at
        } for perm in role.permissions],
        menus=[{
            "id": menu.id,
            "name": menu.name,
            "title": menu.title,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "parent_id": menu.parent_id,
            "sort_order": menu.sort_order,
            "is_visible": menu.is_visible,
            "is_external": menu.is_external,
            "cache": menu.cache,
            "redirect": menu.redirect,
            "created_at": menu.created_at,
            "updated_at": menu.updated_at
        } for menu in role.menus],
        user_count=user_count
    )
    
    return BaseResponse(
        message="获取角色详情成功",
        data=role_detail
    )


@router.put("/{role_id}", response_model=BaseResponse, summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_role_write)
):
    """更新角色信息"""
    role = await crud_role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查角色名称是否已被其他角色使用
    if role_data.name and await crud_role.check_name_exists(role_data.name, role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名称已被其他角色使用"
        )
    
    # 验证权限是否存在
    if role_data.permission_ids is not None:
        for permission_id in role_data.permission_ids:
            permission = await crud_permission.get(permission_id)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限ID {permission_id} 不存在"
                )
    
    # 验证菜单是否存在
    if role_data.menu_ids is not None:
        for menu_id in role_data.menu_ids:
            menu = await crud_menu.get(menu_id)
            if not menu:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"菜单ID {menu_id} 不存在"
                )
    
    # 更新角色
    await crud_role.update_with_permissions(role, role_data)
    
    return BaseResponse(message="角色更新成功")


@router.delete("/{role_id}", response_model=BaseResponse, summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_role_delete)
):
    """删除角色"""
    role = await crud_role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否可以删除
    if not await crud_role.can_delete(role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该角色已被用户使用，无法删除"
        )
    
    await crud_role.delete(role_id)
    
    return BaseResponse(message="角色删除成功")


@router.post("/{role_id}/permissions", response_model=BaseResponse, summary="分配角色权限")
async def assign_role_permissions(
    role_id: int,
    permission_data: RolePermissionAssign,
    current_user: User = Depends(require_role_write)
):
    """为角色分配权限"""
    role = await crud_role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 验证权限是否存在
    for permission_id in permission_data.permission_ids:
        permission = await crud_permission.get(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"权限ID {permission_id} 不存在"
            )
    
    await crud_role.assign_permissions(role, permission_data.permission_ids)
    
    return BaseResponse(message="权限分配成功")


@router.post("/{role_id}/menus", response_model=BaseResponse, summary="分配角色菜单")
async def assign_role_menus(
    role_id: int,
    menu_data: RoleMenuAssign,
    current_user: User = Depends(require_role_write)
):
    """为角色分配菜单"""
    role = await crud_role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 验证菜单是否存在
    for menu_id in menu_data.menu_ids:
        menu = await crud_menu.get(menu_id)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"菜单ID {menu_id} 不存在"
            )
    
    await crud_role.assign_menus(role, menu_data.menu_ids)
    
    return BaseResponse(message="菜单分配成功")


@router.get("/options/select", response_model=BaseResponse, summary="获取角色选择选项")
async def get_role_options(current_user: User = Depends(require_role_read)):
    """获取角色选择选项（用于下拉框等）"""
    options = await crud_role.get_select_options()
    
    return BaseResponse(
        message="获取角色选项成功",
        data=options
    )


@router.post("/bulk-delete", response_model=BaseResponse, summary="批量删除角色")
async def bulk_delete_roles(
    bulk_data: BulkOperationRequest,
    current_user: User = Depends(require_role_delete)
):
    """批量删除角色"""
    # 检查所有角色是否可以删除
    for role_id in bulk_data.ids:
        role = await crud_role.get(role_id)
        if role and not await crud_role.can_delete(role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"角色 {role.name} 已被用户使用，无法删除"
            )
    
    deleted_count = await crud_role.delete_multi(bulk_data.ids)
    
    return BaseResponse(
        message=f"成功删除 {deleted_count} 个角色",
        data={"deleted_count": deleted_count}
    )


@router.get("/{role_id}/permissions", response_model=BaseResponse, summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    current_user: User = Depends(require_role_read)
):
    """获取角色的权限列表"""
    role = await crud_role.get_with_permissions(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 获取角色的权限ID列表
    permission_ids = [perm.id for perm in role.permissions] if role.permissions else []

    return BaseResponse(
        message="获取角色权限成功",
        data={"permission_ids": permission_ids}
    )


@router.get("/{role_id}/menus", response_model=BaseResponse, summary="获取角色菜单")
async def get_role_menus(
    role_id: int,
    current_user: User = Depends(require_role_read)
):
    """获取角色的菜单列表"""
    role = await crud_role.get_with_menus(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 获取角色的菜单ID列表
    menu_ids = [menu.id for menu in role.menus] if role.menus else []

    return BaseResponse(
        message="获取角色菜单成功",
        data={"menu_ids": menu_ids}
    )



