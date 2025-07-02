from tortoise import fields, models
import datetime


class BaseModel(models.Model):
    """基础模型，包含通用字段"""
    
    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    
    class Meta:
        abstract = True

    def to_dict(self):
        """将模型转换为字典"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 