"""
RBAC权限管理API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from app.core.security import get_current_user, PermissionChecker
from app.models.user import User
from app.models.rbac import Department, Role, Permission, UserRole, RolePermission, UserPermission
from app.schemas.rbac import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentListResponse,
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse,
    UserRoleAssign, UserRoleResponse,
    UserPermissionAssign, UserPermissionResponse,
    PermissionCheck, PermissionCheckResponse,
    MenuTree
)

router = APIRouter()

# 权限检查器
require_dept_manage = PermissionChecker("dept:manage")
require_role_manage = PermissionChecker("role:manage")
require_permission_manage = PermissionChecker("permission:manage")
require_user_role_manage = PermissionChecker("user_role:manage")


# ============ 部门管理 ============

@router.get("/departments", response_model=DepartmentListResponse, summary="获取部门列表")
async def get_departments(
    current_user: User = Depends(get_current_user)
):
    """获取部门列表（树形结构）"""
    try:
        # 获取用户有权限访问的部门
        accessible_depts = await current_user.get_data_scope_departments()
        
        # 构建树形结构
        dept_dict = {dept.id: dept for dept in accessible_depts}
        tree_depts = []
        
        for dept in accessible_depts:
            if dept.parent_id is None or dept.parent_id not in dept_dict:
                # 根部门
                dept_response = DepartmentResponse.from_orm(dept)
                dept_response.children = await _build_dept_tree(dept, dept_dict)
                tree_depts.append(dept_response)
        
        return DepartmentListResponse(
            departments=tree_depts,
            total=len(accessible_depts)
        )
    except Exception as e:
        logger.error(f"获取部门列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取部门列表失败")


@router.post("/departments", response_model=DepartmentResponse, summary="创建部门")
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_dept_manage)
):
    """创建部门"""
    try:
        # 检查部门代码是否已存在
        existing_dept = await Department.get_or_none(code=dept_data.code)
        if existing_dept:
            raise HTTPException(status_code=400, detail="部门代码已存在")
        
        # 创建部门
        dept = await Department.create(
            **dept_data.dict(),
            created_by=current_user.id
        )
        
        return DepartmentResponse.from_orm(dept)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建部门失败: {e}")
        raise HTTPException(status_code=500, detail="创建部门失败")


@router.put("/departments/{dept_id}", response_model=DepartmentResponse, summary="更新部门")
async def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(require_dept_manage)
):
    """更新部门"""
    try:
        dept = await Department.get_or_none(id=dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 更新部门信息
        update_data = dept_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user.id
            await dept.update_from_dict(update_data)
            await dept.save()
        
        return DepartmentResponse.from_orm(dept)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新部门失败: {e}")
        raise HTTPException(status_code=500, detail="更新部门失败")


@router.delete("/departments/{dept_id}", summary="删除部门")
async def delete_department(
    dept_id: int,
    current_user: User = Depends(require_dept_manage)
):
    """删除部门"""
    try:
        dept = await Department.get_or_none(id=dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 检查是否有子部门
        children = await dept.get_children()
        if children:
            raise HTTPException(status_code=400, detail="请先删除子部门")
        
        # 检查是否有用户
        users = await User.filter(department_id=dept_id)
        if users:
            raise HTTPException(status_code=400, detail="部门下还有用户，无法删除")
        
        await dept.delete()
        return {"message": "部门删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除部门失败: {e}")
        raise HTTPException(status_code=500, detail="删除部门失败")


# ============ 角色管理 ============

@router.get("/roles", response_model=RoleListResponse, summary="获取角色列表")
async def get_roles(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    try:
        query = Role.filter(status="active")
        
        if search:
            query = query.filter(
                name__icontains=search
            )
        
        total = await query.count()
        roles = await query.offset((page - 1) * size).limit(size).all()
        
        # 获取角色权限信息
        role_responses = []
        for role in roles:
            role_response = RoleResponse.from_orm(role)
            role_response.permissions = await role.get_permissions()
            role_response.user_count = await UserRole.filter(role_id=role.id).count()
            role_responses.append(role_response)
        
        return RoleListResponse(
            roles=role_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取角色列表失败")


@router.post("/roles", response_model=RoleResponse, summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_role_manage)
):
    """创建角色"""
    try:
        # 检查角色代码是否已存在
        existing_role = await Role.get_or_none(code=role_data.code)
        if existing_role:
            raise HTTPException(status_code=400, detail="角色代码已存在")
        
        # 创建角色
        permission_ids = role_data.permission_ids
        role_dict = role_data.dict(exclude={"permission_ids"})
        role = await Role.create(
            **role_dict,
            created_by=current_user.id
        )
        
        # 分配权限
        if permission_ids:
            for perm_id in permission_ids:
                await RolePermission.create(role_id=role.id, permission_id=perm_id)
        
        # 获取完整信息
        role_response = RoleResponse.from_orm(role)
        role_response.permissions = await role.get_permissions()
        
        return role_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        raise HTTPException(status_code=500, detail="创建角色失败")


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_role_manage)
):
    """更新角色"""
    try:
        role = await Role.get_or_none(id=role_id)
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 更新角色信息
        permission_ids = role_data.permission_ids
        update_data = role_data.dict(exclude_unset=True, exclude={"permission_ids"})
        if update_data:
            update_data["updated_by"] = current_user.id
            await role.update_from_dict(update_data)
            await role.save()
        
        # 更新权限
        if permission_ids is not None:
            # 删除现有权限
            await RolePermission.filter(role_id=role.id).delete()
            # 添加新权限
            for perm_id in permission_ids:
                await RolePermission.create(role_id=role.id, permission_id=perm_id)
        
        # 获取完整信息
        role_response = RoleResponse.from_orm(role)
        role_response.permissions = await role.get_permissions()
        
        return role_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {e}")
        raise HTTPException(status_code=500, detail="更新角色失败")


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_role_manage)
):
    """删除角色"""
    try:
        role = await Role.get_or_none(id=role_id)
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 检查是否有用户使用该角色
        user_roles = await UserRole.filter(role_id=role_id)
        if user_roles:
            raise HTTPException(status_code=400, detail="角色正在使用中，无法删除")
        
        # 删除角色权限关联
        await RolePermission.filter(role_id=role_id).delete()
        
        # 删除角色
        await role.delete()
        return {"message": "角色删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {e}")
        raise HTTPException(status_code=500, detail="删除角色失败")


# ============ 权限管理 ============

@router.get("/permissions", response_model=PermissionListResponse, summary="获取权限列表")
async def get_permissions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    group: Optional[str] = Query(None, description="权限分组"),
    permission_type: Optional[str] = Query(None, description="权限类型"),
    current_user: User = Depends(get_current_user)
):
    """获取权限列表"""
    try:
        query = Permission.filter(status="active")

        if search:
            query = query.filter(name__icontains=search)

        if group:
            query = query.filter(group=group)

        if permission_type:
            query = query.filter(permission_type=permission_type)

        total = await query.count()
        permissions = await query.offset((page - 1) * size).limit(size).all()

        permission_responses = [PermissionResponse.from_orm(perm) for perm in permissions]

        return PermissionListResponse(
            permissions=permission_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        logger.error(f"获取权限列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取权限列表失败")


@router.post("/permissions", response_model=PermissionResponse, summary="创建权限")
async def create_permission(
    perm_data: PermissionCreate,
    current_user: User = Depends(require_permission_manage)
):
    """创建权限"""
    try:
        # 检查权限代码是否已存在
        existing_perm = await Permission.get_or_none(code=perm_data.code)
        if existing_perm:
            raise HTTPException(status_code=400, detail="权限代码已存在")

        # 创建权限
        permission = await Permission.create(
            **perm_data.dict(),
            created_by=current_user.id
        )

        return PermissionResponse.from_orm(permission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建权限失败: {e}")
        raise HTTPException(status_code=500, detail="创建权限失败")


@router.put("/permissions/{perm_id}", response_model=PermissionResponse, summary="更新权限")
async def update_permission(
    perm_id: int,
    perm_data: PermissionUpdate,
    current_user: User = Depends(require_permission_manage)
):
    """更新权限"""
    try:
        permission = await Permission.get_or_none(id=perm_id)
        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")

        # 更新权限信息
        update_data = perm_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user.id
            await permission.update_from_dict(update_data)
            await permission.save()

        return PermissionResponse.from_orm(permission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新权限失败: {e}")
        raise HTTPException(status_code=500, detail="更新权限失败")


@router.delete("/permissions/{perm_id}", summary="删除权限")
async def delete_permission(
    perm_id: int,
    current_user: User = Depends(require_permission_manage)
):
    """删除权限"""
    try:
        permission = await Permission.get_or_none(id=perm_id)
        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")

        # 检查是否有角色使用该权限
        role_permissions = await RolePermission.filter(permission_id=perm_id)
        if role_permissions:
            raise HTTPException(status_code=400, detail="权限正在使用中，无法删除")

        # 删除用户权限关联
        await UserPermission.filter(permission_id=perm_id).delete()

        # 删除权限
        await permission.delete()
        return {"message": "权限删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除权限失败: {e}")
        raise HTTPException(status_code=500, detail="删除权限失败")


# ============ 用户角色分配 ============

@router.post("/user-roles", response_model=List[UserRoleResponse], summary="分配用户角色")
async def assign_user_roles(
    assignment: UserRoleAssign,
    current_user: User = Depends(require_user_role_manage)
):
    """分配用户角色"""
    try:
        # 检查用户是否存在
        user = await User.get_or_none(id=assignment.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 删除现有角色
        await UserRole.filter(user_id=assignment.user_id).delete()

        # 分配新角色
        user_roles = []
        for role_id in assignment.role_ids:
            role = await Role.get_or_none(id=role_id)
            if not role:
                raise HTTPException(status_code=404, detail=f"角色ID {role_id} 不存在")

            user_role = await UserRole.create(
                user_id=assignment.user_id,
                role_id=role_id,
                granted_by=current_user.id,
                expires_at=assignment.expires_at,
                dept_ids=assignment.dept_ids or []
            )

            user_role_response = UserRoleResponse.from_orm(user_role)
            user_role_response.role = RoleResponse.from_orm(role)
            user_roles.append(user_role_response)

        return user_roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配用户角色失败: {e}")
        raise HTTPException(status_code=500, detail="分配用户角色失败")


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse], summary="获取用户角色")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取用户角色"""
    try:
        user_roles = await UserRole.filter(user_id=user_id).prefetch_related("role")

        user_role_responses = []
        for ur in user_roles:
            if not ur.is_expired() and ur.role.status == "active":
                user_role_response = UserRoleResponse.from_orm(ur)
                user_role_response.role = RoleResponse.from_orm(ur.role)
                user_role_responses.append(user_role_response)

        return user_role_responses
    except Exception as e:
        logger.error(f"获取用户角色失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户角色失败")


# ============ 权限检查 ============

@router.post("/check-permissions", response_model=PermissionCheckResponse, summary="检查用户权限")
async def check_permissions(
    check_data: PermissionCheck,
    current_user: User = Depends(get_current_user)
):
    """检查用户权限"""
    try:
        user = await User.get_or_none(id=check_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        permissions = {}
        for perm_code in check_data.permission_codes:
            permissions[perm_code] = await user.has_permission(perm_code)

        return PermissionCheckResponse(
            user_id=check_data.user_id,
            permissions=permissions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="检查用户权限失败")


@router.get("/menu-tree", response_model=List[MenuTree], summary="获取菜单树")
async def get_menu_tree(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的菜单树"""
    try:
        # 获取用户权限
        user_permissions = await current_user.get_permissions()
        menu_permissions = [p for p in user_permissions if p.permission_type == "menu"]

        # 构建菜单树
        menu_dict = {}
        for perm in menu_permissions:
            menu_dict[perm.id] = MenuTree(
                id=perm.id,
                name=perm.name,
                code=perm.code,
                path=perm.menu_path,
                component=perm.menu_component,
                icon=perm.menu_icon,
                sort_order=perm.sort_order,
                children=[]
            )

        # 构建树形结构
        tree_menus = []
        for menu in menu_dict.values():
            perm = next(p for p in menu_permissions if p.id == menu.id)
            if perm.parent_id is None or perm.parent_id not in menu_dict:
                # 根菜单
                menu.children = _build_menu_tree(menu, menu_dict, menu_permissions)
                tree_menus.append(menu)

        # 排序
        tree_menus.sort(key=lambda x: x.sort_order)
        return tree_menus
    except Exception as e:
        logger.error(f"获取菜单树失败: {e}")
        raise HTTPException(status_code=500, detail="获取菜单树失败")


# ============ 辅助函数 ============

async def _build_dept_tree(dept: Department, dept_dict: dict) -> List[DepartmentResponse]:
    """构建部门树"""
    children = []
    for child_dept in dept_dict.values():
        if child_dept.parent_id == dept.id:
            child_response = DepartmentResponse.from_orm(child_dept)
            child_response.children = await _build_dept_tree(child_dept, dept_dict)
            children.append(child_response)
    return children


def _build_menu_tree(menu: MenuTree, menu_dict: dict, permissions: list) -> List[MenuTree]:
    """构建菜单树"""
    children = []
    for perm in permissions:
        if perm.parent_id == menu.id:
            child_menu = menu_dict.get(perm.id)
            if child_menu:
                child_menu.children = _build_menu_tree(child_menu, menu_dict, permissions)
                children.append(child_menu)

    children.sort(key=lambda x: x.sort_order)
    return children
