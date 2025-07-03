"""
菜单CRUD操作
处理菜单相关的数据库操作
"""

from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from .base import CRUDBase
from ..models.menu import Menu
from ..schemas.menu import MenuCreate, MenuUpdate
from ..schemas.common import PaginationParams


class CRUDMenu(CRUDBase[Menu, MenuCreate, MenuUpdate]):
    """菜单CRUD操作类"""
    
    def _build_search_query(self, search: str) -> Optional[Q]:
        """构建菜单搜索查询条件"""
        return Q(
            Q(name__icontains=search) |
            Q(title__icontains=search) |
            Q(path__icontains=search) |
            Q(component__icontains=search)
        )
    
    async def get_by_name(self, name: str) -> Optional[Menu]:
        """根据菜单名称获取菜单"""
        return await self.model.get_or_none(name=name)
    
    async def get_by_path(self, path: str) -> Optional[Menu]:
        """根据路径获取菜单"""
        return await self.model.get_or_none(path=path)
    
    async def get_tree(self, user_role_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """获取菜单树形结构"""
        return await self.model.get_menu_tree()
    
    async def get_children(self, parent_id: int) -> List[Menu]:
        """获取子菜单列表"""
        return await self.model.filter(parent_id=parent_id, is_visible=True).order_by("sort_order").all()
    
    async def get_root_menus(self) -> List[Menu]:
        """获取根菜单列表"""
        return await self.model.filter(parent_id__isnull=True, is_visible=True).order_by("sort_order").all()
    
    async def get_visible_menus(self) -> List[Menu]:
        """获取所有可见菜单"""
        return await self.model.filter(is_visible=True).order_by("sort_order").all()
    
    async def get_descendants(self, menu: Menu) -> List[Menu]:
        """获取所有后代菜单"""
        return await menu.get_all_descendants()
    
    async def get_ancestors(self, menu: Menu) -> List[Menu]:
        """获取所有祖先菜单"""
        return await menu.get_ancestors()
    
    async def get_breadcrumb(self, menu: Menu) -> List[Dict[str, Any]]:
        """获取面包屑导航"""
        return await menu.get_breadcrumb()
    
    async def check_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """检查菜单名称是否已存在"""
        query = self.model.filter(name=name)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def check_path_exists(self, path: str, exclude_id: Optional[int] = None) -> bool:
        """检查路径是否已存在"""
        if not path:
            return False
        query = self.model.filter(path=path)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def can_delete(self, menu: Menu) -> bool:
        """检查菜单是否可以删除"""
        return await menu.can_delete()
    
    async def get_menus_by_parent(self, parent_id: Optional[int]) -> List[Menu]:
        """根据父菜单ID获取菜单列表"""
        if parent_id is None:
            return await self.model.filter(parent_id__isnull=True).order_by("sort_order").all()
        else:
            return await self.model.filter(parent_id=parent_id).order_by("sort_order").all()
    
    async def get_user_menus(self, user_role_ids: List[int]) -> List[Menu]:
        """获取用户有权限的菜单"""
        return await self.model.filter(
            roles__id__in=user_role_ids,
            is_visible=True
        ).distinct().order_by("sort_order").all()
    
    async def get_menu_routes(self, user_role_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """获取菜单路由（前端路由使用）"""
        tree = await self.get_tree(user_role_ids)
        return self._convert_to_routes(tree)
    
    def _convert_to_routes(self, menus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将菜单树转换为路由格式"""
        routes = []
        for menu in menus:
            route = {
                "id": menu["id"],
                "name": menu["name"],
                "path": menu["path"] or "/",
                "component": menu["component"],
                "redirect": menu["redirect"],
                "meta": {
                    "title": menu["title"],
                    "icon": menu["icon"],
                    "cache": menu["cache"],
                    "hidden": not menu["is_visible"],
                    "external": menu["is_external"]
                },
                "children": self._convert_to_routes(menu["children"]) if menu["children"] else []
            }
            routes.append(route)
        return routes
    
    async def get_paginated_with_parent(
        self,
        params: PaginationParams,
        **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """分页获取菜单及父菜单信息"""
        query = self.model.filter(**filters).prefetch_related("parent")
        
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
        menus = await query.offset(skip).limit(params.page_size).all()
        
        # 构建返回数据
        result = []
        for menu in menus:
            menu_data = {
                "id": menu.id,
                "name": menu.name,
                "title": menu.title,
                "path": menu.path,
                "component": menu.component,
                "icon": menu.icon,
                "parent_id": menu.parent_id,
                "parent_name": menu.parent.title if menu.parent else None,
                "sort_order": menu.sort_order,
                "is_visible": menu.is_visible,
                "is_external": menu.is_external,
                "created_at": menu.created_at,
                "updated_at": menu.updated_at
            }
            result.append(menu_data)
        
        return result, total
    
    async def get_select_options(self) -> List[Dict[str, Any]]:
        """获取菜单选择选项"""
        menus = await self.model.all().order_by("sort_order")
        return [
            {
                "id": menu.id,
                "name": menu.name,
                "title": menu.title,
                "parent_id": menu.parent_id
            }
            for menu in menus
        ]
    
    async def update_sort_order(self, menu_orders: List[Dict[str, Any]]) -> bool:
        """批量更新菜单排序"""
        try:
            for order_data in menu_orders:
                menu_id = order_data.get("id")
                sort_order = order_data.get("sort_order")
                parent_id = order_data.get("parent_id")
                
                await self.model.filter(id=menu_id).update(
                    sort_order=sort_order,
                    parent_id=parent_id
                )
            return True
        except Exception:
            return False


# 创建菜单CRUD实例
crud_menu = CRUDMenu(Menu)
