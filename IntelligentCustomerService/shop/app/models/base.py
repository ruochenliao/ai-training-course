from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    """基础模型"""
    
    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="是否删除")
    
    class Meta:
        abstract = True
