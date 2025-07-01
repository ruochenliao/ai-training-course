"""
权限管理API端点
"""



from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.core import get_current_user, PermissionChecker
from app.core.response import Response
from app.models import User
from app.schemas.rbac import PermissionCreate, PermissionUpdate
from app.services.rbac import PermissionService

router = APIRouter()

# 权限检查器
require_permission_manage = PermissionChecker("permission:manage")
require_permission_view = PermissionChecker("permission:view")


@router.get("/", summary="获取权限列表")
async def get_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    group: str = Query(None, description="权限分组"),
    permission_type: str = Query(None, description="权限类型"),
    current_user: User = Depends(require_permission_view)
):
    """获取权限列表"""
    try:
        permissions, total = await PermissionService.get_permissions_with_pagination(
            page, page_size, search, group, permission_type
        )
        return Response.pagination(
            items=permissions,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取权限列表成功"
        )
    except Exception as e:
        logger.error(f"获取权限列表失败: {e}")
        return Response.internal_error("获取权限列表失败")


@router.post("/", summary="创建权限")
async def create_permission(
    perm_data: PermissionCreate,
    current_user: User = Depends(require_permission_manage)
):
    """创建权限"""
    try:
        perm_dict = await PermissionService.create_permission(perm_data, current_user)
        return Response.created(data=perm_dict, msg="创建权限成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"创建权限失败: {e}")
        return Response.internal_error("创建权限失败")


@router.put("/{perm_id}", summary="更新权限")
async def update_permission(
    perm_id: int,
    perm_data: PermissionUpdate,
    current_user: User = Depends(require_permission_manage)
):
    """更新权限"""
    try:
        perm_dict = await PermissionService.update_permission(perm_id, perm_data, current_user)
        return Response.updated(data=perm_dict, msg="更新权限成功")
    except ValueError as e:
        return Response.not_found(str(e))
    except Exception as e:
        logger.error(f"更新权限失败: {e}")
        return Response.internal_error("更新权限失败")


@router.delete("/{perm_id}", summary="删除权限")
async def delete_permission(
    perm_id: int,
    current_user: User = Depends(require_permission_manage)
):
    """删除权限"""
    try:
        await PermissionService.delete_permission(perm_id)
        return Response.deleted("权限删除成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"删除权限失败: {e}")
        return Response.internal_error("删除权限失败")
