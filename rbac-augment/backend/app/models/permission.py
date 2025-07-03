"""
权限模型
定义权限表结构和相关方法
"""

from tortoise import fields

from .base import BaseModel


class Permission(BaseModel):
    """权限模型"""

    name = fields.CharField(max_length=100, description="权限名称")
    code = fields.CharField(max_length=100, unique=True, description="权限编码")
    description = fields.TextField(null=True, description="权限描述")
    module = fields.CharField(max_length=50, null=True, description="权限模块")
    resource = fields.CharField(max_length=50, description="资源")
    action = fields.CharField(max_length=50, description="操作")
    type = fields.CharField(max_length=20, description="权限类型", default="功能")
    sort_order = fields.IntField(default=0, description="排序")

    # 自关联（父子权限）
    parent = fields.ForeignKeyField(
        'models.Permission',
        related_name='children',
        null=True,
        on_delete=fields.CASCADE,
        description="父权限"
    )

    # 关联角色（多对多，反向关系由Role模型定义）
    
    class Meta:
        table = "permissions"
        table_description = "权限表"
        unique_together = (("module", "code"),)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    async def can_delete(self):
        """检查权限是否可以删除"""
        # 检查是否有角色使用此权限
        from app.models.role import Role
        role_count = await Role.filter(permissions=self).count()
        return role_count == 0

    @classmethod
    async def get_tree(cls):
        """获取权限树结构"""
        # 获取所有顶级权限
        root_permissions = await cls.filter(parent_id__isnull=True, is_deleted=False).order_by("sort_order").all()

        # 递归构建树结构
        result = []
        for perm in root_permissions:
            perm_dict = await perm.to_dict_async(include_children=True)
            result.append(perm_dict)
        return result

    def to_dict(self, include_children=False):
        """将权限转换为字典"""
        base_dict = super().to_dict()
        result = {
            **base_dict,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "module": self.module,
            "resource": self.resource,
            "action": self.action,
            "type": self.type
        }

        if include_children:
            result["children"] = []

        return result

    async def to_dict_async(self, include_children=False):
        """异步将权限转换为字典"""
        base_dict = super().to_dict()
        result = {
            **base_dict,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "module": self.module,
            "resource": self.resource,
            "action": self.action,
            "type": self.type
        }

        if include_children:
            children = await Permission.filter(parent=self, is_deleted=False).order_by("sort_order").all()
            result["children"] = [await child.to_dict_async(include_children=True) for child in children]

        return result
