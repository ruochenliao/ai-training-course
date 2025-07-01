"""
部门管理API端点
"""

from fastapi import APIRouter, Depends
from loguru import logger

from app.core import get_current_user, PermissionChecker
from app.core.response import Response
from app.models import User
from app.schemas.rbac import DepartmentCreate, DepartmentUpdate
from app.services.rbac import DepartmentService

router = APIRouter()

# 权限检查器
require_dept_manage = PermissionChecker("dept:manage")
require_dept_view = PermissionChecker("dept:view")


@router.get("/", summary="获取部门列表")
async def get_departments(
    current_user: User = Depends(require_dept_view)
):
    """获取部门列表（树形结构）"""
    try:
        departments = await DepartmentService.get_departments_tree(current_user)
        return Response.success(data=departments, msg="获取部门列表成功")
    except Exception as e:
        logger.error(f"获取部门列表失败: {e}")
        return Response.internal_error("获取部门列表失败")


@router.post("/", summary="创建部门")
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_dept_manage)
):
    """创建部门"""
    try:
        dept = await DepartmentService.create_department(dept_data, current_user)
        dept_dict = await dept.to_dict()
        return Response.created(data=dept_dict, msg="创建部门成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"创建部门失败: {e}")
        return Response.internal_error("创建部门失败")


@router.put("/{dept_id}", summary="更新部门")
async def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(require_dept_manage)
):
    """更新部门"""
    try:
        dept = await DepartmentService.update_department(dept_id, dept_data, current_user)
        dept_dict = await dept.to_dict()
        return Response.updated(data=dept_dict, msg="更新部门成功")
    except ValueError as e:
        return Response.not_found(str(e))
    except Exception as e:
        logger.error(f"更新部门失败: {e}")
        return Response.internal_error("更新部门失败")


@router.delete("/{dept_id}", summary="删除部门")
async def delete_department(
    dept_id: int,
    current_user: User = Depends(require_dept_manage)
):
    """删除部门"""
    try:
        await DepartmentService.delete_department(dept_id)
        return Response.deleted("部门删除成功")
    except ValueError as e:
        return Response.bad_request(str(e))
    except Exception as e:
        logger.error(f"删除部门失败: {e}")
        return Response.internal_error("删除部门失败")
