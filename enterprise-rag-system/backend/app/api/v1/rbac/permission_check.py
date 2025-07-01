"""
权限检查API端点
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.core import get_current_user
from app.models import User
from app.schemas.rbac import (
    PermissionCheck, PermissionCheckResponse, MenuTree,
    StandardResponse
)
from app.services.rbac import PermissionService

router = APIRouter()


@router.post("/check", response_model=StandardResponse[PermissionCheckResponse], summary="检查用户权限")
async def check_permissions(
    check_data: PermissionCheck,
    current_user: User = Depends(get_current_user)
):
    """检查用户权限"""
    try:
        permissions = await PermissionService.check_user_permissions(check_data)
        
        response_data = PermissionCheckResponse(
            user_id=check_data.user_id,
            permissions=permissions
        )
        
        return StandardResponse(
            code=200,
            message="权限检查成功",
            data=response_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"检查用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="检查用户权限失败")


@router.get("/menu_tree", response_model=StandardResponse[List[MenuTree]], summary="获取菜单树")
async def get_menu_tree(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的菜单树"""
    try:
        menu_tree = await PermissionService.get_user_menu_tree(current_user)
        
        return StandardResponse(
            code=200,
            message="获取菜单树成功",
            data=menu_tree
        )
    except Exception as e:
        logger.error(f"获取菜单树失败: {e}")
        raise HTTPException(status_code=500, detail="获取菜单树失败")
