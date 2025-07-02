"""
权限模型
定义权限表结构和相关方法
"""

from tortoise import fields

from app.models.base import BaseModel


class Permission(BaseModel):
    """权限模型"""
    
    name = fields.CharField(max_length=100, description="权限名称")
    code = fields.CharField(max_length=100, unique=True, description="权限编码")
    description = fields.TextField(null=True, description="权限描述")
    module = fields.CharField(max_length=50, description="权限模块")
    type = fields.CharField(max_length=20, description="权限类型", default="功能")
    
    # 关联角色（多对多，反向关系由Role模型定义）
    
    class Meta:
        table = "permissions"
        table_description = "权限表"
        unique_together = (("module", "code"),)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def to_dict(self):
        """将权限转换为字典"""
        base_dict = super().to_dict()
        return {
            **base_dict,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "module": self.module,
            "type": self.type
        }
