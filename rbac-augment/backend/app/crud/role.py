"""
角色CRUD操作
处理角色相关的数据库操作
"""

from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from .base import CRUDBase
from ..models.role import Role
from ..models.permission import Permission
from ..models.menu import Menu
from ..schemas.role import RoleCreate, RoleUpdate
from ..schemas.common import PaginationParams


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """角色CRUD操作类"""
    
    def _build_search_query(self, search: str) -> Optional[Q]:
        """构建角色搜索查询条件"""
        return Q(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    async def get_by_code(self, code: str) -> Optional[Role]:
        """根据角色代码获取角色"""
        return await self.model.get_or_none(code=code)
    
    async def create_with_permissions(self, obj_in: RoleCreate) -> Role:
        """创建角色并分配权限"""
        # 提取权限ID和菜单ID
        permission_ids = obj_in.permission_ids
        menu_ids = obj_in.menu_ids
        obj_data = obj_in.dict(exclude={"permission_ids", "menu_ids"})
        
        # 创建角色
        role = await self.model.create(**obj_data)
        
        # 分配权限
        if permission_ids:
            permissions = await Permission.filter(id__in=permission_ids).all()
            await role.permissions.add(*permissions)
        
        # 分配菜单
        if menu_ids:
            menus = await Menu.filter(id__in=menu_ids).all()
            await role.menus.add(*menus)
        
        return role
    
    async def update_with_permissions(
        self,
        role: Role,
        obj_in: RoleUpdate
    ) -> Role:
        """更新角色并分配权限"""
        # 提取权限ID和菜单ID
        permission_ids = obj_in.permission_ids
        menu_ids = obj_in.menu_ids
        obj_data = obj_in.dict(exclude={"permission_ids", "menu_ids"}, exclude_unset=True)
        
        # 更新角色基本信息
        for field, value in obj_data.items():
            if hasattr(role, field):
                setattr(role, field, value)
        
        await role.save()
        
        # 更新权限
        if permission_ids is not None:
            await role.permissions.clear()
            if permission_ids:
                permissions = await Permission.filter(id__in=permission_ids).all()
                await role.permissions.add(*permissions)
        
        # 更新菜单
        if menu_ids is not None:
            await role.menus.clear()
            if menu_ids:
                menus = await Menu.filter(id__in=menu_ids).all()
                await role.menus.add(*menus)
        
        return role
    
    async def get_with_permissions(self, role_id: int) -> Optional[Role]:
        """获取角色及其权限信息"""
        return await self.model.get_or_none(id=role_id).prefetch_related("permissions", "menus")
    
    async def assign_permissions(self, role: Role, permission_ids: List[int]) -> Role:
        """为角色分配权限"""
        await role.permissions.clear()
        if permission_ids:
            permissions = await Permission.filter(id__in=permission_ids).all()
            await role.permissions.add(*permissions)
        return role
    
    async def remove_permissions(self, role: Role, permission_ids: List[int]) -> Role:
        """移除角色权限"""
        if permission_ids:
            permissions = await Permission.filter(id__in=permission_ids).all()
            await role.permissions.remove(*permissions)
        return role
    
    async def assign_menus(self, role: Role, menu_ids: List[int]) -> Role:
        """为角色分配菜单"""
        await role.menus.clear()
        if menu_ids:
            menus = await Menu.filter(id__in=menu_ids).all()
            await role.menus.add(*menus)
        return role
    
    async def remove_menus(self, role: Role, menu_ids: List[int]) -> Role:
        """移除角色菜单"""
        if menu_ids:
            menus = await Menu.filter(id__in=menu_ids).all()
            await role.menus.remove(*menus)
        return role
    
    async def get_active_roles(self) -> List[Role]:
        """获取所有激活的角色"""
        return await self.model.filter(is_active=True).order_by("sort_order").all()
    
    async def get_role_permissions(self, role: Role) -> List[str]:
        """获取角色所有权限代码"""
        return await role.get_permission_codes()
    
    async def get_role_menus(self, role: Role) -> List[int]:
        """获取角色所有菜单ID"""
        return await role.get_menu_ids()
    
    async def check_code_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """检查角色代码是否已存在"""
        query = self.model.filter(code=code)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """检查角色名称是否已存在"""
        query = self.model.filter(name=name)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def get_roles_by_permission(self, permission_id: int) -> List[Role]:
        """根据权限ID获取角色列表"""
        return await self.model.filter(permissions__id=permission_id).all()
    
    async def get_roles_by_menu(self, menu_id: int) -> List[Role]:
        """根据菜单ID获取角色列表"""
        return await self.model.filter(menus__id=menu_id).all()
    
    async def can_delete(self, role: Role) -> bool:
        """检查角色是否可以删除"""
        return await role.can_delete()
    
    async def get_paginated_with_stats(
        self,
        params: PaginationParams,
        **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """分页获取角色及统计信息"""
        query = self.model.filter(**filters).prefetch_related("users", "permissions")
        
        # 添加搜索条件
        if params.search:
            search_query = self._build_search_query(params.search)
            if search_query:
                query = query.filter(search_query)
        
        # 获取总数
        total = await query.count()
        
        # 添加排序
        if params.sort_field:
            order_field = params.sort_field
            if params.sort_order == "desc":
                order_field = f"-{order_field}"
            query = query.order_by(order_field)
        else:
            query = query.order_by("sort_order", "-created_at")
        
        # 分页
        skip = (params.page - 1) * params.page_size
        roles = await query.offset(skip).limit(params.page_size).all()
        
        # 构建返回数据
        result = []
        for role in roles:
            # 安全地获取关联数据的数量
            try:
                user_count = await role.users.all().count()
            except:
                user_count = 0

            try:
                permission_count = await role.permissions.all().count()
            except:
                permission_count = 0

            role_data = {
                "id": role.id,
                "name": role.name,
                "code": role.code,
                "description": role.description,
                "is_active": role.is_active,
                "sort_order": role.sort_order,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
                "user_count": user_count,
                "permission_count": permission_count
            }
            result.append(role_data)
        
        return result, total
    
    async def get_select_options(self) -> List[Dict[str, Any]]:
        """获取角色选择选项"""
        roles = await self.model.filter(is_active=True).order_by("sort_order").all()
        return [
            {
                "id": role.id,
                "name": role.name,
                "code": role.code,
                "is_active": role.is_active
            }
            for role in roles
        ]

    async def get_role_users(self, role_id: int) -> List:
        """获取角色关联的用户列表"""
        from ..models.user import User
        return await User.filter(roles__id=role_id, is_active=True).all()

    async def get_active_roles(self) -> List[Role]:
        """获取所有活跃的角色"""
        return await self.model.filter(is_active=True).order_by("sort_order").all()


# 创建角色CRUD实例
crud_role = CRUDRole(Role)
