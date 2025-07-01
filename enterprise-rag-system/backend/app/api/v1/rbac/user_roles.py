"""
用户角色管理API端点
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.core import get_current_user, PermissionChecker
from app.models import User
from app.schemas.rbac import (
    UserRoleAssign, UserRoleResponse, UserPermissionAssign, UserPermissionResponse,
    StandardResponse
)
from app.services.rbac import UserRoleService

router = APIRouter()

# 权限检查器
require_user_role_manage = PermissionChecker("user_role:manage")


@router.post("/assign", response_model=StandardResponse[List[Dict[str, Any]]], summary="分配用户角色")
async def assign_user_roles(
    assign_data: UserRoleAssign,
    current_user: User = Depends(require_user_role_manage)
):
    """分配用户角色"""
    try:
        user_roles = await UserRoleService.assign_user_roles(assign_data, current_user)
        
        return StandardResponse(
            code=200,
            message="分配用户角色成功",
            data=user_roles
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分配用户角色失败: {e}")
        raise HTTPException(status_code=500, detail="分配用户角色失败")


@router.get("/users/{user_id}/roles", response_model=StandardResponse[List[Dict[str, Any]]], summary="获取用户角色")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取用户角色"""
    try:
        user_roles = await UserRoleService.get_user_roles(user_id)
        
        return StandardResponse(
            code=200,
            message="获取用户角色成功",
            data=user_roles
        )
    except Exception as e:
        logger.error(f"获取用户角色失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户角色失败")


@router.post("/assign_permissions", response_model=StandardResponse[List[Dict[str, Any]]], summary="分配用户权限")
async def assign_user_permissions(
    assign_data: UserPermissionAssign,
    current_user: User = Depends(require_user_role_manage)
):
    """分配用户权限"""
    try:
        user_permissions = await UserRoleService.assign_user_permissions(assign_data, current_user)
        
        return StandardResponse(
            code=200,
            message="分配用户权限成功",
            data=user_permissions
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分配用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="分配用户权限失败")


@router.get("/users/{user_id}/permissions", response_model=StandardResponse[List[Dict[str, Any]]], summary="获取用户权限")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取用户权限"""
    try:
        user_permissions = await UserRoleService.get_user_permissions(user_id)
        
        return StandardResponse(
            code=200,
            message="获取用户权限成功",
            data=user_permissions
        )
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户权限失败")
