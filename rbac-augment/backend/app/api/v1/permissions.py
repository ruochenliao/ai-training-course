"""
权限管理API
处理权限的CRUD操作
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ...schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionTreeResponse, PermissionListResponse, PermissionSelectOption,
    PermissionGroupResponse
)
from ...schemas.common import BaseResponse, PaginationResponse, IDResponse, BulkOperationRequest
from ...crud.permission import crud_permission
from ...utils.deps import get_current_user, get_pagination_params, require_permission_read, require_permission_write, require_permission_delete
from ...utils.pagination import create_pagination_response
from ...models.user import User

router = APIRouter()


@router.get("", response_model=BaseResponse, summary="获取权限列表")
async def get_permissions(
    pagination = Depends(get_pagination_params),
    current_user: User = Depends(require_permission_read)
):
    """获取权限列表（分页）"""
    permissions, total = await crud_permission.get_paginated_with_parent(pagination)
    
    pagination_data = create_pagination_response(permissions, total, pagination)
    
    return BaseResponse(
        message="获取权限列表成功",
        data=pagination_data
    )


@router.get("/tree", response_model=BaseResponse, summary="获取权限树")
async def get_permission_tree(current_user: User = Depends(require_permission_read)):
    """获取权限树形结构"""
    tree = await crud_permission.get_tree()
    
    return BaseResponse(
        message="获取权限树成功",
        data=tree
    )


@router.get("/groups", response_model=BaseResponse, summary="获取权限分组")
async def get_permission_groups(current_user: User = Depends(require_permission_read)):
    """获取按资源分组的权限"""
    groups = await crud_permission.get_grouped_permissions()
    
    return BaseResponse(
        message="获取权限分组成功",
        data=groups
    )


@router.post("", response_model=BaseResponse, summary="创建权限")
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_permission_write)
):
    """创建新权限"""
    # 检查权限代码是否已存在
    if await crud_permission.check_code_exists(permission_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限代码已存在"
        )
    
    # 检查资源和操作组合是否已存在
    if await crud_permission.check_resource_action_exists(
        permission_data.resource, 
        permission_data.action
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该资源的操作权限已存在"
        )
    
    # 验证父权限是否存在
    if permission_data.parent_id:
        parent = await crud_permission.get(permission_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父权限不存在"
            )
    
    # 创建权限
    permission = await crud_permission.create(permission_data)
    
    return BaseResponse(
        message="权限创建成功",
        data=IDResponse(id=permission.id)
    )


@router.get("/{permission_id}", response_model=BaseResponse, summary="获取权限详情")
async def get_permission(
    permission_id: int,
    current_user: User = Depends(require_permission_read)
):
    """获取权限详情"""
    permission = await crud_permission.get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 获取父权限信息
    await permission.fetch_related("parent")
    
    permission_data = PermissionResponse(
        id=permission.id,
        name=permission.name,
        code=permission.code,
        description=permission.description,
        resource=permission.resource,
        action=permission.action,
        parent_id=permission.parent_id,
        sort_order=permission.sort_order,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )
    
    return BaseResponse(
        message="获取权限详情成功",
        data=permission_data
    )


@router.put("/{permission_id}", response_model=BaseResponse, summary="更新权限")
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_permission_write)
):
    """更新权限信息"""
    permission = await crud_permission.get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 验证父权限是否存在（如果指定了）
    if permission_data.parent_id:
        # 不能将自己设为父权限
        if permission_data.parent_id == permission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将自己设为父权限"
            )

        parent = await crud_permission.get(permission_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父权限不存在"
            )

        # 检查是否会形成循环引用
        ancestors = await parent.get_ancestors()
        if permission in ancestors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能设置会形成循环引用的父权限"
            )

    # 更新权限
    await crud_permission.update(permission, permission_data)

    return BaseResponse(message="权限更新成功")


@router.patch("/{permission_id}/status", response_model=BaseResponse, summary="更新权限状态")
async def update_permission_status(
    permission_id: int,
    status_data: dict,
    current_user: User = Depends(require_permission_write)
):
    """更新权限状态"""
    permission = await crud_permission.get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 更新状态
    permission.is_active = status_data.get('is_active', permission.is_active)
    await permission.save()

    return BaseResponse(message="权限状态更新成功")


@router.delete("/{permission_id}", response_model=BaseResponse, summary="删除权限")
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(require_permission_delete)
):
    """删除权限"""
    permission = await crud_permission.get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 检查是否可以删除
    if not await crud_permission.can_delete(permission):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该权限已被角色使用或存在子权限，无法删除"
        )
    
    await crud_permission.delete(permission_id)
    
    return BaseResponse(message="权限删除成功")


@router.get("/{permission_id}/children", response_model=BaseResponse, summary="获取子权限")
async def get_permission_children(
    permission_id: int,
    current_user: User = Depends(require_permission_read)
):
    """获取权限的子权限列表"""
    permission = await crud_permission.get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    children = await crud_permission.get_children(permission_id)
    
    children_data = [
        PermissionResponse(
            id=child.id,
            name=child.name,
            code=child.code,
            description=child.description,
            resource=child.resource,
            action=child.action,
            parent_id=child.parent_id,
            sort_order=child.sort_order,
            created_at=child.created_at,
            updated_at=child.updated_at
        )
        for child in children
    ]
    
    return BaseResponse(
        message="获取子权限成功",
        data=children_data
    )


@router.get("/options/select", response_model=BaseResponse, summary="获取权限选择选项")
async def get_permission_options(current_user: User = Depends(require_permission_read)):
    """获取权限选择选项（用于下拉框等）"""
    options = await crud_permission.get_select_options()
    
    return BaseResponse(
        message="获取权限选项成功",
        data=options
    )


@router.get("/resource/{resource}", response_model=BaseResponse, summary="获取资源权限")
async def get_permissions_by_resource(
    resource: str,
    current_user: User = Depends(require_permission_read)
):
    """根据资源获取权限列表"""
    permissions = await crud_permission.get_permissions_by_resource(resource)
    
    permissions_data = [
        PermissionResponse(
            id=perm.id,
            name=perm.name,
            code=perm.code,
            description=perm.description,
            resource=perm.resource,
            action=perm.action,
            parent_id=perm.parent_id,
            sort_order=perm.sort_order,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        )
        for perm in permissions
    ]
    
    return BaseResponse(
        message="获取资源权限成功",
        data=permissions_data
    )


@router.post("/bulk-delete", response_model=BaseResponse, summary="批量删除权限")
async def bulk_delete_permissions(
    bulk_data: BulkOperationRequest,
    current_user: User = Depends(require_permission_delete)
):
    """批量删除权限"""
    # 检查所有权限是否可以删除
    for permission_id in bulk_data.ids:
        permission = await crud_permission.get(permission_id)
        if permission and not await crud_permission.can_delete(permission):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"权限 {permission.name} 已被角色使用或存在子权限，无法删除"
            )
    
    deleted_count = await crud_permission.delete_multi(bulk_data.ids)
    
    return BaseResponse(
        message=f"成功删除 {deleted_count} 个权限",
        data={"deleted_count": deleted_count}
    )
