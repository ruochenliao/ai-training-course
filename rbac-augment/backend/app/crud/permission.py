"""
权限CRUD操作
处理权限相关的数据库操作
"""

from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from app.crud.base import CRUDBase
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.schemas.common import PaginationParams


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    """权限CRUD操作类"""
    
    def _build_search_query(self, search: str) -> Optional[Q]:
        """构建权限搜索查询条件"""
        return Q(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search) |
            Q(resource__icontains=search) |
            Q(action__icontains=search)
        )
    
    async def get_by_code(self, code: str) -> Optional[Permission]:
        """根据权限代码获取权限"""
        return await self.model.get_or_none(code=code)
    
    async def get_by_resource_action(self, resource: str, action: str) -> Optional[Permission]:
        """根据资源和操作获取权限"""
        return await self.model.get_or_none(resource=resource, action=action)
    
    async def get_tree(self) -> List[Dict[str, Any]]:
        """获取权限树形结构"""
        return await self.model.get_tree()
    
    async def get_children(self, parent_id: int) -> List[Permission]:
        """获取子权限列表"""
        return await self.model.filter(parent_id=parent_id).order_by("sort_order").all()
    
    async def get_root_permissions(self) -> List[Permission]:
        """获取根权限列表"""
        return await self.model.filter(parent_id__isnull=True).order_by("sort_order").all()
    
    async def get_descendants(self, permission: Permission) -> List[Permission]:
        """获取所有后代权限"""
        return await permission.get_all_descendants()
    
    async def get_ancestors(self, permission: Permission) -> List[Permission]:
        """获取所有祖先权限"""
        return await permission.get_ancestors()
    
    async def check_code_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """检查权限代码是否已存在"""
        query = self.model.filter(code=code)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def check_resource_action_exists(
        self,
        resource: str,
        action: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """检查资源和操作组合是否已存在"""
        query = self.model.filter(resource=resource, action=action)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def can_delete(self, permission: Permission) -> bool:
        """检查权限是否可以删除"""
        return await permission.can_delete()
    
    async def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """根据资源获取权限列表"""
        return await self.model.filter(resource=resource).order_by("sort_order").all()
    
    async def get_permissions_by_action(self, action: str) -> List[Permission]:
        """根据操作获取权限列表"""
        return await self.model.filter(action=action).order_by("sort_order").all()
    
    async def get_permissions_by_parent(self, parent_id: Optional[int]) -> List[Permission]:
        """根据父权限ID获取权限列表"""
        if parent_id is None:
            return await self.model.filter(parent_id__isnull=True).order_by("sort_order").all()
        else:
            return await self.model.filter(parent_id=parent_id).order_by("sort_order").all()
    
    async def get_role_count(self, permission: Permission) -> int:
        """获取拥有此权限的角色数量"""
        return await permission.get_role_count()
    
    async def get_paginated_with_parent(
        self,
        params: PaginationParams,
        **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """分页获取权限及父权限信息"""
        query = self.model.filter(**filters).prefetch_related("parent", "roles")
        
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
        permissions = await query.offset(skip).limit(params.page_size).all()
        
        # 构建返回数据
        result = []
        for permission in permissions:
            permission_data = {
                "id": permission.id,
                "name": permission.name,
                "code": permission.code,
                "description": permission.description,
                "resource": permission.resource,
                "action": permission.action,
                "parent_id": permission.parent_id,
                "parent_name": permission.parent.name if permission.parent else None,
                "sort_order": permission.sort_order,
                "created_at": permission.created_at,
                "updated_at": permission.updated_at,
                "role_count": len(permission.roles)
            }
            result.append(permission_data)
        
        return result, total
    
    async def get_select_options(self) -> List[Dict[str, Any]]:
        """获取权限选择选项"""
        permissions = await self.model.all().order_by("sort_order")
        return [
            {
                "id": permission.id,
                "name": permission.name,
                "code": permission.code,
                "resource": permission.resource,
                "action": permission.action
            }
            for permission in permissions
        ]
    
    async def get_grouped_permissions(self) -> List[Dict[str, Any]]:
        """获取按资源分组的权限"""
        permissions = await self.model.all().order_by("resource", "sort_order")
        
        # 按资源分组
        grouped = {}
        for permission in permissions:
            if permission.resource not in grouped:
                grouped[permission.resource] = []
            grouped[permission.resource].append({
                "id": permission.id,
                "name": permission.name,
                "code": permission.code,
                "description": permission.description,
                "action": permission.action,
                "sort_order": permission.sort_order
            })
        
        # 转换为列表格式
        result = []
        for resource, perms in grouped.items():
            result.append({
                "resource": resource,
                "permissions": perms
            })
        
        return result
    
    async def create_batch(self, permissions_data: List[Dict[str, Any]]) -> List[Permission]:
        """批量创建权限"""
        permissions = []
        for data in permissions_data:
            permission = await self.model.create(**data)
            permissions.append(permission)
        return permissions


# 创建权限CRUD实例
crud_permission = CRUDPermission(Permission)
