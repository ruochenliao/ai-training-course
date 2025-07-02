"""
角色模型
定义角色表结构和相关方法
"""

from tortoise import fields

from app.models.base import BaseModel


class Role(BaseModel):
    """角色模型"""
    
    name = fields.CharField(max_length=50, unique=True, description="角色名称")
    code = fields.CharField(max_length=50, unique=True, description="角色编码")
    description = fields.TextField(null=True, description="角色描述")
    
    # 关联用户（多对多，反向关系由User模型定义）
    
    # 关联权限（多对多）
    permissions = fields.ManyToManyField(
        'models.Permission',
        related_name='roles',
        through='role_permission',
        description="角色权限"
    )

    # 关联菜单（多对多）
    menus = fields.ManyToManyField(
        'models.Menu',
        related_name='roles',
        through='role_menu',
        description="角色菜单"
    )
    
    class Meta:
        table = "roles"
        table_description = "角色表"
    
    def __str__(self):
        return self.name
    
    async def to_dict(self):
        """将角色转换为字典"""
        base_dict = super().to_dict()
        
        # 获取角色权限
        permissions = await self.permissions.all()
        perm_list = [{"id": p.id, "name": p.name, "code": p.code} for p in permissions]
        
        # 获取角色菜单
        menus = await self.menus.all()
        menu_list = [{"id": m.id, "name": m.name, "path": m.path} for m in menus]
        
        return {
            **base_dict,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "permissions": perm_list,
            "menus": menu_list
        }
