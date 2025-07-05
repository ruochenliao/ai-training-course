"""
数据权限管理API
处理数据权限的CRUD操作和分配功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from ...schemas.data_permission import (
    DataPermissionCreate, DataPermissionUpdate, DataPermissionResponse,
    DataPermissionListResponse, DataPermissionSearchParams,
    DataPermissionAssignRequest, DataPermissionAssignResponse,
    DataPermissionCheckRequest, DataPermissionCheckResponse,
    DataPermissionSelectOption, BulkOperationRequest, BulkOperationResponse
)
from ...schemas.common import BaseResponse, PaginationParams, IDResponse
from ...crud.data_permission import crud_data_permission
from ...models.user import User
from ...utils.deps import get_current_user, get_pagination_params
from ...utils.permissions import require_permissions, PermissionLogic
from ...utils.response import ResponseHelper

router = APIRouter()

# 权限要求
require_data_permission_read = require_permissions(["data_permission:read"])
require_data_permission_write = require_permissions(["data_permission:write"])
require_data_permission_delete = require_permissions(["data_permission:delete"])


@router.get("/options", response_model=BaseResponse, summary="获取数据权限选项")
async def get_data_permission_options(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """获取数据权限选择选项（用于下拉选择）"""
    try:
        options = await crud_data_permission.get_select_options()
        return ResponseHelper.success(options, "获取数据权限选项成功", request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("", response_model=BaseResponse, summary="获取数据权限列表")
async def get_data_permissions(
    request: Request,
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    permission_type: Optional[str] = Query(None, description="权限类型"),
    scope: Optional[str] = Query(None, description="权限范围"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    is_active: Optional[bool] = Query(None, description="是否启用")
):
    """获取数据权限列表"""
    try:
        # 构建搜索参数
        search_params = DataPermissionSearchParams(
            keyword=keyword,
            permission_type=permission_type,
            scope=scope,
            resource_type=resource_type,
            is_active=is_active
        )
        
        # 搜索数据权限
        permissions, total = await crud_data_permission.search(
            search_params, 
            pagination.page, 
            pagination.page_size
        )
        
        # 转换为响应格式
        permission_list = []
        for permission in permissions:
            permission_data = await permission.to_dict()
            permission_list.append(permission_data)
        
        # 构建分页响应
        from app.utils.pagination import create_pagination_response
        pagination_data = create_pagination_response(permission_list, total, pagination)
        
        return ResponseHelper.success(pagination_data, "获取数据权限列表成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/{permission_id}", response_model=BaseResponse, summary="获取数据权限详情")
async def get_data_permission(
    request: Request,
    permission_id: int,
    current_user: User = Depends(require_data_permission_read)
):
    """获取数据权限详情"""
    try:
        permission = await crud_data_permission.get(permission_id)
        if not permission:
            return ResponseHelper.not_found("数据权限不存在", request=request)
        
        permission_data = await permission.to_dict()
        return ResponseHelper.success(permission_data, "获取数据权限详情成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("", response_model=BaseResponse, summary="创建数据权限")
async def create_data_permission(
    request: Request,
    permission_in: DataPermissionCreate,
    current_user: User = Depends(require_data_permission_write)
):
    """创建数据权限"""
    try:
        permission = await crud_data_permission.create_with_validation(permission_in)
        permission_data = await permission.to_dict()
        
        return ResponseHelper.success(
            permission_data,
            "数据权限创建成功",
            request=request
        )
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.put("/{permission_id}", response_model=BaseResponse, summary="更新数据权限")
async def update_data_permission(
    request: Request,
    permission_id: int,
    permission_in: DataPermissionUpdate,
    current_user: User = Depends(require_data_permission_write)
):
    """更新数据权限"""
    try:
        permission = await crud_data_permission.get(permission_id)
        if not permission:
            return ResponseHelper.not_found("数据权限不存在", request=request)
        
        updated_permission = await crud_data_permission.update_with_validation(
            permission, permission_in
        )
        permission_data = await updated_permission.to_dict()
        
        return ResponseHelper.success(
            permission_data,
            "数据权限更新成功",
            request=request
        )
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.delete("/{permission_id}", response_model=BaseResponse, summary="删除数据权限")
async def delete_data_permission(
    request: Request,
    permission_id: int,
    current_user: User = Depends(require_data_permission_delete)
):
    """删除数据权限"""
    try:
        permission = await crud_data_permission.get(permission_id)
        if not permission:
            return ResponseHelper.not_found("数据权限不存在", request=request)
        
        await crud_data_permission.remove(permission_id)
        
        return ResponseHelper.success(None, "数据权限删除成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/{permission_id}/assign-users", response_model=BaseResponse, summary="分配数据权限给用户")
async def assign_permission_to_users(
    request: Request,
    permission_id: int,
    assign_data: DataPermissionAssignRequest,
    current_user: User = Depends(require_data_permission_write)
):
    """将数据权限分配给用户"""
    try:
        if not assign_data.user_ids:
            return ResponseHelper.validation_error([], "用户ID列表不能为空", request=request)
        
        result = await crud_data_permission.assign_to_users(
            permission_id, assign_data.user_ids, current_user.id
        )
        
        return ResponseHelper.success(result, "数据权限分配成功", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/{permission_id}/assign-roles", response_model=BaseResponse, summary="分配数据权限给角色")
async def assign_permission_to_roles(
    request: Request,
    permission_id: int,
    assign_data: DataPermissionAssignRequest,
    current_user: User = Depends(require_data_permission_write)
):
    """将数据权限分配给角色"""
    try:
        if not assign_data.role_ids:
            return ResponseHelper.validation_error([], "角色ID列表不能为空", request=request)
        
        result = await crud_data_permission.assign_to_roles(
            permission_id, assign_data.role_ids, current_user.id
        )
        
        return ResponseHelper.success(result, "数据权限分配成功", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/check", response_model=BaseResponse, summary="检查数据权限")
async def check_data_permission(
    request: Request,
    check_data: DataPermissionCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """检查用户数据权限"""
    try:
        has_permission, reason = await crud_data_permission.check_user_permission(
            check_data.user_id,
            check_data.resource_type,
            check_data.resource_id,
            **check_data.extra_params or {}
        )
        
        result = DataPermissionCheckResponse(
            has_permission=has_permission,
            reason=reason
        )
        
        return ResponseHelper.success(
            result.model_dump(),
            "数据权限检查完成",
            request=request
        )
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/bulk-delete", response_model=BaseResponse, summary="批量删除数据权限")
async def bulk_delete_data_permissions(
    request: Request,
    bulk_data: BulkOperationRequest,
    current_user: User = Depends(require_data_permission_delete)
):
    """批量删除数据权限"""
    try:
        success_count = 0
        failed_count = 0
        errors = []
        
        for permission_id in bulk_data.ids:
            try:
                permission = await crud_data_permission.get(permission_id)
                if permission:
                    await crud_data_permission.remove(permission_id)
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"权限ID {permission_id} 不存在")
            except Exception as e:
                failed_count += 1
                errors.append(f"删除权限ID {permission_id} 失败: {str(e)}")
        
        result = BulkOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )
        
        return ResponseHelper.success(
            result.model_dump(),
            f"批量删除完成，成功 {success_count} 个，失败 {failed_count} 个",
            request=request
        )
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)
