"""
部门管理API
处理部门的CRUD操作和相关功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentDetailResponse,
    DepartmentTreeResponse, DepartmentListResponse, DepartmentSelectOption,
    DepartmentUserAssign, DepartmentUserResponse, DepartmentStatistics,
    DepartmentSearchParams, DepartmentBatchOperation, DepartmentBatchOperationResponse,
    DepartmentMove, DepartmentImportData, DepartmentImportResponse
)
from app.schemas.common import BaseResponse, PaginationParams, IDResponse
from app.crud.department import crud_department
from app.models.user import User
from app.utils.deps import get_current_user, get_pagination_params
from app.utils.permissions import require_permissions, require_any_permission, PermissionLogic
from app.utils.response import ResponseHelper

router = APIRouter()


@router.get("/tree", response_model=BaseResponse[DepartmentTreeResponse])
@require_permissions(["department:read"])
async def get_department_tree(
    request: Request,
    current_user: User = Depends(get_current_user),
    parent_id: Optional[int] = Query(None, description="父部门ID"),
    include_inactive: bool = Query(False, description="是否包含非活跃部门")
):
    """获取部门树"""
    try:
        tree = await crud_department.get_tree(parent_id, include_inactive)
        
        # 转换为树形响应格式
        tree_nodes = []
        for dept in tree:
            node_data = await dept.to_dict(include_children=True)
            tree_nodes.append(node_data)
        
        total = await crud_department.count()
        
        response_data = DepartmentTreeResponse(
            tree=tree_nodes,
            total=total
        )
        
        return ResponseHelper.success(response_data, "获取部门树成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/", response_model=BaseResponse[DepartmentListResponse])
@require_permissions(["department:read"])
async def get_departments(
    request: Request,
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    parent_id: Optional[int] = Query(None, description="父部门ID"),
    level: Optional[int] = Query(None, description="部门层级"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    manager_id: Optional[int] = Query(None, description="负责人ID")
):
    """获取部门列表"""
    try:
        search_params = DepartmentSearchParams(
            keyword=keyword,
            parent_id=parent_id,
            level=level,
            is_active=is_active,
            manager_id=manager_id
        )
        
        departments, total = await crud_department.search(
            search_params,
            skip=(pagination.page - 1) * pagination.page_size,
            limit=pagination.page_size
        )
        
        # 转换为响应格式
        department_list = []
        for dept in departments:
            dept_data = await dept.to_dict()
            department_list.append(DepartmentResponse(**dept_data))
        
        response_data = DepartmentListResponse(
            departments=department_list,
            total=total
        )
        
        return ResponseHelper.paginated(
            items=department_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            message="获取部门列表成功",
            request=request
        )
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/select-options", response_model=BaseResponse[List[DepartmentSelectOption]])
@require_permissions(["department:read"])
async def get_department_select_options(
    request: Request,
    current_user: User = Depends(get_current_user),
    include_inactive: bool = Query(False, description="是否包含非活跃部门"),
    exclude_id: Optional[int] = Query(None, description="排除的部门ID")
):
    """获取部门选择选项"""
    try:
        departments = await crud_department.get_all()
        
        options = []
        for dept in departments:
            if exclude_id and dept.id == exclude_id:
                continue
            
            if not include_inactive and not dept.is_active:
                continue
            
            option = DepartmentSelectOption(
                id=dept.id,
                name=dept.name,
                code=dept.code,
                level=dept.level,
                parent_id=dept.parent_id,
                is_active=dept.is_active,
                disabled=not dept.is_active
            )
            options.append(option)
        
        return ResponseHelper.success(options, "获取部门选项成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/{department_id}", response_model=BaseResponse[DepartmentDetailResponse])
@require_permissions(["department:read"])
async def get_department(
    request: Request,
    department_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取部门详情"""
    try:
        department = await crud_department.get(department_id)
        if not department:
            return ResponseHelper.not_found("部门不存在", request=request)
        
        # 获取详细信息
        dept_data = await department.to_dict(include_children=True, include_users=True)
        
        # 获取父部门信息
        parent = await department.get_parent()
        if parent:
            dept_data["parent"] = await parent.to_dict()
        
        # 获取负责人信息
        manager = await department.get_manager()
        if manager:
            dept_data["manager"] = await manager.to_dict()
        
        # 获取路径和完整编码
        dept_data["path"] = await department.get_path()
        dept_data["full_code"] = await department.get_full_code()
        
        response_data = DepartmentDetailResponse(**dept_data)
        
        return ResponseHelper.success(response_data, "获取部门详情成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/", response_model=BaseResponse[DepartmentResponse])
@require_permissions(["department:create"])
async def create_department(
    request: Request,
    department_in: DepartmentCreate,
    current_user: User = Depends(get_current_user)
):
    """创建部门"""
    try:
        department = await crud_department.create_with_validation(department_in)
        dept_data = await department.to_dict()
        response_data = DepartmentResponse(**dept_data)
        
        return ResponseHelper.created(response_data, "创建部门成功", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.put("/{department_id}", response_model=BaseResponse[DepartmentResponse])
@require_permissions(["department:update"])
async def update_department(
    request: Request,
    department_id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新部门"""
    try:
        department = await crud_department.get(department_id)
        if not department:
            return ResponseHelper.not_found("部门不存在", request=request)
        
        updated_department = await crud_department.update_with_validation(department, department_in)
        dept_data = await updated_department.to_dict()
        response_data = DepartmentResponse(**dept_data)
        
        return ResponseHelper.updated(response_data, "更新部门成功", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.delete("/{department_id}", response_model=BaseResponse)
@require_permissions(["department:delete"])
async def delete_department(
    request: Request,
    department_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除部门"""
    try:
        department = await crud_department.get(department_id)
        if not department:
            return ResponseHelper.not_found("部门不存在", request=request)
        
        # 检查是否可以删除
        can_delete, reason = await department.can_delete()
        if not can_delete:
            return ResponseHelper.validation_error([], reason, request=request)
        
        await crud_department.remove(department_id)
        
        return ResponseHelper.deleted("删除部门成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/{department_id}/move", response_model=BaseResponse)
@require_permissions(["department:update"])
async def move_department(
    request: Request,
    department_id: int,
    move_data: DepartmentMove,
    current_user: User = Depends(get_current_user)
):
    """移动部门"""
    try:
        success = await crud_department.move_department(department_id, move_data.new_parent_id)
        
        if success:
            return ResponseHelper.success(None, "移动部门成功", request=request)
        else:
            return ResponseHelper.validation_error([], "移动部门失败，可能会形成循环引用", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/{department_id}/users", response_model=BaseResponse[List[DepartmentUserResponse]])
@require_permissions(["department:read", "user:read"], logic=PermissionLogic.AND)
async def get_department_users(
    request: Request,
    department_id: int,
    current_user: User = Depends(get_current_user),
    include_descendants: bool = Query(False, description="是否包含子部门用户")
):
    """获取部门用户"""
    try:
        users = await crud_department.get_department_users(department_id, include_descendants)
        
        user_list = []
        for user in users:
            user_data = await user.to_dict()
            user_response = DepartmentUserResponse(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
                is_active=user.is_active,
                is_manager=(user.id == getattr(user, 'department_manager_id', None))
            )
            user_list.append(user_response)
        
        return ResponseHelper.success(user_list, "获取部门用户成功", request=request)
        
    except ValueError as e:
        return ResponseHelper.validation_error([], str(e), request=request)
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.post("/batch-operation", response_model=BaseResponse[DepartmentBatchOperationResponse])
@require_permissions(["department:update", "department:delete"], logic=PermissionLogic.OR)
async def batch_operation_departments(
    request: Request,
    operation: DepartmentBatchOperation,
    current_user: User = Depends(get_current_user)
):
    """批量操作部门"""
    try:
        result = await crud_department.batch_operation(operation)
        response_data = DepartmentBatchOperationResponse(**result)
        
        return ResponseHelper.success(response_data, "批量操作完成", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)


@router.get("/statistics/overview", response_model=BaseResponse[DepartmentStatistics])
@require_permissions(["department:read"])
async def get_department_statistics(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """获取部门统计信息"""
    try:
        statistics = await crud_department.get_statistics()
        response_data = DepartmentStatistics(**statistics)
        
        return ResponseHelper.success(response_data, "获取统计信息成功", request=request)
        
    except Exception as e:
        return ResponseHelper.internal_error(detail=str(e), request=request)
