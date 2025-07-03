"""
菜单管理API
处理菜单的CRUD操作
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ...schemas.menu import (
    MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse,
    MenuListResponse, MenuSelectOption, MenuRouteResponse, BreadcrumbResponse
)
from ...schemas.common import BaseResponse, PaginationResponse, IDResponse, BulkOperationRequest
from ...crud.menu import crud_menu
from ...utils.deps import get_current_user, get_pagination_params, require_menu_read, require_menu_write, require_menu_delete
from ...utils.pagination import create_pagination_response
from ...models.user import User

router = APIRouter()


@router.get("", response_model=BaseResponse, summary="获取菜单列表")
async def get_menus(
    pagination = Depends(get_pagination_params),
    current_user: User = Depends(require_menu_read)
):
    """获取菜单列表（分页）"""
    menus, total = await crud_menu.get_paginated_with_parent(pagination)
    
    pagination_data = create_pagination_response(menus, total, pagination)
    
    return BaseResponse(
        message="获取菜单列表成功",
        data=pagination_data
    )


@router.get("/tree", response_model=BaseResponse, summary="获取菜单树")
async def get_menu_tree(current_user: User = Depends(require_menu_read)):
    """获取菜单树形结构"""
    tree = await crud_menu.get_tree()
    
    return BaseResponse(
        message="获取菜单树成功",
        data=tree
    )


@router.get("/routes", response_model=BaseResponse, summary="获取菜单路由")
async def get_menu_routes(current_user: User = Depends(get_current_user)):
    """获取当前用户的菜单路由"""
    # 获取用户角色ID
    await current_user.fetch_related("roles")
    role_ids = [role.id for role in current_user.roles]
    
    # 获取菜单路由
    routes = await crud_menu.get_menu_routes(role_ids)
    
    return BaseResponse(
        message="获取菜单路由成功",
        data=routes
    )


@router.post("", response_model=BaseResponse, summary="创建菜单")
async def create_menu(
    menu_data: MenuCreate,
    current_user: User = Depends(require_menu_write)
):
    """创建新菜单"""
    # 检查菜单名称是否已存在
    if await crud_menu.check_name_exists(menu_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单名称已存在"
        )
    
    # 检查路径是否已存在
    if menu_data.path and await crud_menu.check_path_exists(menu_data.path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单路径已存在"
        )
    
    # 验证父菜单是否存在
    if menu_data.parent_id:
        parent = await crud_menu.get(menu_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父菜单不存在"
            )
    
    # 创建菜单
    menu = await crud_menu.create(menu_data)
    
    return BaseResponse(
        message="菜单创建成功",
        data=IDResponse(id=menu.id)
    )


@router.get("/{menu_id}", response_model=BaseResponse, summary="获取菜单详情")
async def get_menu(
    menu_id: int,
    current_user: User = Depends(require_menu_read)
):
    """获取菜单详情"""
    menu = await crud_menu.get(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 获取父菜单信息
    await menu.fetch_related("parent")
    
    menu_data = MenuResponse(
        id=menu.id,
        name=menu.name,
        title=menu.title,
        path=menu.path,
        component=menu.component,
        icon=menu.icon,
        parent_id=menu.parent_id,
        sort_order=menu.sort_order,
        is_visible=menu.is_visible,
        is_external=menu.is_external,
        cache=menu.cache,
        redirect=menu.redirect,
        created_at=menu.created_at,
        updated_at=menu.updated_at
    )
    
    return BaseResponse(
        message="获取菜单详情成功",
        data=menu_data
    )


@router.put("/{menu_id}", response_model=BaseResponse, summary="更新菜单")
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    current_user: User = Depends(require_menu_write)
):
    """更新菜单信息"""
    menu = await crud_menu.get(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 检查菜单名称是否已被其他菜单使用
    if menu_data.name and await crud_menu.check_name_exists(menu_data.name, menu_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单名称已被其他菜单使用"
        )
    
    # 检查路径是否已被其他菜单使用
    if menu_data.path and await crud_menu.check_path_exists(menu_data.path, menu_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单路径已被其他菜单使用"
        )
    
    # 验证父菜单是否存在（如果指定了）
    if menu_data.parent_id:
        # 不能将自己设为父菜单
        if menu_data.parent_id == menu_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将自己设为父菜单"
            )
        
        parent = await crud_menu.get(menu_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父菜单不存在"
            )
        
        # 检查是否会形成循环引用
        ancestors = await parent.get_ancestors()
        if menu in ancestors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能设置会形成循环引用的父菜单"
            )
    
    # 更新菜单
    await crud_menu.update(menu, menu_data)
    
    return BaseResponse(message="菜单更新成功")


@router.delete("/{menu_id}", response_model=BaseResponse, summary="删除菜单")
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(require_menu_delete)
):
    """删除菜单"""
    menu = await crud_menu.get(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 检查是否可以删除
    if not await crud_menu.can_delete(menu):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该菜单存在子菜单，无法删除"
        )
    
    await crud_menu.delete(menu_id)
    
    return BaseResponse(message="菜单删除成功")


@router.get("/{menu_id}/children", response_model=BaseResponse, summary="获取子菜单")
async def get_menu_children(
    menu_id: int,
    current_user: User = Depends(require_menu_read)
):
    """获取菜单的子菜单列表"""
    menu = await crud_menu.get(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    children = await crud_menu.get_children(menu_id)
    
    children_data = [
        MenuResponse(
            id=child.id,
            name=child.name,
            title=child.title,
            path=child.path,
            component=child.component,
            icon=child.icon,
            parent_id=child.parent_id,
            sort_order=child.sort_order,
            is_visible=child.is_visible,
            is_external=child.is_external,
            cache=child.cache,
            redirect=child.redirect,
            created_at=child.created_at,
            updated_at=child.updated_at
        )
        for child in children
    ]
    
    return BaseResponse(
        message="获取子菜单成功",
        data=children_data
    )


@router.get("/{menu_id}/breadcrumb", response_model=BaseResponse, summary="获取面包屑导航")
async def get_menu_breadcrumb(
    menu_id: int,
    current_user: User = Depends(require_menu_read)
):
    """获取菜单的面包屑导航"""
    menu = await crud_menu.get(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    breadcrumb = await crud_menu.get_breadcrumb(menu)
    
    return BaseResponse(
        message="获取面包屑导航成功",
        data={"items": breadcrumb}
    )


@router.get("/options/select", response_model=BaseResponse, summary="获取菜单选择选项")
async def get_menu_options(current_user: User = Depends(require_menu_read)):
    """获取菜单选择选项（用于下拉框等）"""
    options = await crud_menu.get_select_options()
    
    return BaseResponse(
        message="获取菜单选项成功",
        data=options
    )


@router.put("/sort", response_model=BaseResponse, summary="更新菜单排序")
async def update_menu_sort(
    sort_data: List[dict],
    current_user: User = Depends(require_menu_write)
):
    """批量更新菜单排序"""
    success = await crud_menu.update_sort_order(sort_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单排序更新失败"
        )
    
    return BaseResponse(message="菜单排序更新成功")


@router.post("/bulk-delete", response_model=BaseResponse, summary="批量删除菜单")
async def bulk_delete_menus(
    bulk_data: BulkOperationRequest,
    current_user: User = Depends(require_menu_delete)
):
    """批量删除菜单"""
    # 检查所有菜单是否可以删除
    for menu_id in bulk_data.ids:
        menu = await crud_menu.get(menu_id)
        if menu and not await crud_menu.can_delete(menu):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"菜单 {menu.title} 存在子菜单，无法删除"
            )
    
    deleted_count = await crud_menu.delete_multi(bulk_data.ids)
    
    return BaseResponse(
        message=f"成功删除 {deleted_count} 个菜单",
        data={"deleted_count": deleted_count}
    )
