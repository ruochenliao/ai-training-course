"""
菜单模型
定义菜单表结构和相关方法
"""

from tortoise import fields
from typing import List, Optional, Dict, Any

from app.models.base import BaseModel


class Menu(BaseModel):
    """菜单模型"""
    
    name = fields.CharField(max_length=50, description="菜单名称")
    title = fields.CharField(max_length=50, null=True, description="菜单标题")
    path = fields.CharField(max_length=100, null=True, description="路由路径")
    component = fields.CharField(max_length=100, null=True, description="组件路径")
    redirect = fields.CharField(max_length=100, null=True, description="重定向路径")
    permission = fields.CharField(max_length=100, null=True, description="权限标识")
    icon = fields.CharField(max_length=50, null=True, description="图标")
    sort = fields.IntField(default=0, description="排序")
    sort_order = fields.IntField(default=0, description="排序顺序")
    hidden = fields.BooleanField(default=False, description="是否隐藏")
    is_visible = fields.BooleanField(default=True, description="是否可见")
    is_external = fields.BooleanField(default=False, description="是否外链")
    type = fields.CharField(max_length=20, default="menu", description="类型：menu-菜单, button-按钮")
    is_cache = fields.BooleanField(default=False, description="是否缓存")
    cache = fields.BooleanField(default=False, description="是否缓存")

    # 自关联（父子菜单）
    parent = fields.ForeignKeyField(
        'models.Menu',
        related_name='children',
        null=True,
        on_delete=fields.CASCADE,
        description="父菜单"
    )
    
    # 关联角色（多对多，反向关系由Role模型定义）
    
    class Meta:
        table = "menus"
        table_description = "菜单表"
        ordering = ["sort", "id"]
    
    def __str__(self):
        return self.name
    
    async def to_dict(self, include_children: bool = False) -> Dict[str, Any]:
        """将菜单转换为字典"""
        base_dict = super().to_dict()
        result = {
            **base_dict,
            "name": self.name,
            "title": self.title,
            "path": self.path,
            "component": self.component,
            "redirect": self.redirect,
            "permission": self.permission,
            "parent_id": self.parent_id if self.parent else None,
            "icon": self.icon,
            "sort": self.sort,
            "sort_order": self.sort_order,
            "hidden": self.hidden,
            "is_visible": self.is_visible,
            "is_external": self.is_external,
            "type": self.type,
            "is_cache": self.is_cache,
            "cache": self.cache,
        }
        
        if include_children:
            children = await self.children.filter(is_deleted=False).order_by("sort").all()
            result["children"] = [await child.to_dict(include_children=True) for child in children]
        
        return result
    
    async def can_delete(self):
        """检查菜单是否可以删除"""
        # 检查是否有子菜单
        children_count = await Menu.filter(parent=self, is_deleted=False).count()
        return children_count == 0

    @classmethod
    async def get_menu_tree(cls) -> List[Dict[str, Any]]:
        """获取菜单树结构"""
        # 获取所有顶级菜单
        root_menus = await cls.filter(parent_id__isnull=True, is_deleted=False).order_by("sort").all()

        # 递归构建树结构
        return [await menu.to_dict(include_children=True) for menu in root_menus]
