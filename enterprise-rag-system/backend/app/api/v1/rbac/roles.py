"""
角色管理API端点
"""

from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.core import get_current_user, PermissionChecker
from app.core.response import Response
from app.models import User
from app.schemas.rbac import RoleCreate, RoleUpdate
from app.services.rbac import RoleService

router = APIRouter()

# 权限检查器
require_role_manage = PermissionChecker("role:manage")
require_role_view = PermissionChecker("role:view")


@router.get("/", summary="获取角色列表")
async def get_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_role_view)
):
    """获取角色列表"""
    try:
        roles, total = await RoleService.get_roles_with_pagination(page, page_size, search)
        return Response.pagination(
            items=roles,
            total=total,
            page=page,
            page_size=page_size,
            msg="获取角色列表成功"
        )
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return Response.internal_error("获取角色列表失败")


@router.post("/", summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role_manage)
):
    """创建角色"""
    try:
        role_dict = await RoleService.create_role(role_data, current_user)
        return Response.created(data=role_dict, msg="创建角色成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        return Response.internal_error("创建角色失败")


@router.put("/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_role_manage)
):
    """更新角色"""
    try:
        role_dict = await RoleService.update_role(role_id, role_data, current_user)
        return Response.updated(data=role_dict, msg="更新角色成功")
    except ValueError as e:
        return Response.not_found(str(e))
    except Exception as e:
        logger.error(f"更新角色失败: {e}")
        return Response.internal_error("更新角色失败")


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_role_manage)
):
    """删除角色"""
    try:
        await RoleService.delete_role(role_id)
        return Response.deleted("角色删除成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"删除角色失败: {e}")
        return Response.internal_error("删除角色失败")
