"""
基础数据模型
"""

from datetime import datetime
from typing import Any, Dict

from tortoise import fields
from tortoise.models import Model


class TimestampMixin:
    """时间戳混入类"""
    
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")


class BaseModel(Model):
    """基础模型类"""
    
    id = fields.IntField(pk=True, description="主键ID")
    
    class Meta:
        abstract = True
    
    async def to_dict(self, exclude_fields: list = None, include_relations: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        exclude_fields = exclude_fields or []
        
        # 获取基础字段
        result = {}
        for field_name, field_obj in self._meta.fields_map.items():
            if field_name in exclude_fields:
                continue
                
            value = getattr(self, field_name, None)
            
            # 处理特殊类型
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif hasattr(value, 'to_dict'):
                result[field_name] = await value.to_dict()
            else:
                result[field_name] = value
        
        # 包含关联关系
        if include_relations:
            for relation_name, relation_field in self._meta.fields_map.items():
                if hasattr(relation_field, 'related_model') and relation_name not in exclude_fields:
                    try:
                        relation_value = await getattr(self, relation_name)
                        if relation_value:
                            if hasattr(relation_value, '__iter__') and not isinstance(relation_value, str):
                                # 一对多或多对多关系
                                result[relation_name] = [
                                    await item.to_dict() if hasattr(item, 'to_dict') else str(item)
                                    for item in relation_value
                                ]
                            else:
                                # 一对一或多对一关系
                                result[relation_name] = (
                                    await relation_value.to_dict() 
                                    if hasattr(relation_value, 'to_dict') 
                                    else str(relation_value)
                                )
                    except Exception:
                        # 如果关联数据获取失败，跳过
                        pass
        
        return result
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        return self.__str__()


class SoftDeleteMixin:
    """软删除混入类"""
    
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")
    
    async def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.now()
        await self.save(update_fields=["is_deleted", "deleted_at"])
    
    async def restore(self):
        """恢复"""
        self.is_deleted = False
        self.deleted_at = None
        await self.save(update_fields=["is_deleted", "deleted_at"])


class StatusMixin:
    """状态混入类"""
    
    class StatusChoices:
        ACTIVE = "active"
        INACTIVE = "inactive"
        PENDING = "pending"
        SUSPENDED = "suspended"
        
        CHOICES = [
            (ACTIVE, "激活"),
            (INACTIVE, "未激活"),
            (PENDING, "待处理"),
            (SUSPENDED, "暂停"),
        ]
    
    status = fields.CharEnumField(
        StatusChoices,
        default=StatusChoices.ACTIVE,
        description="状态"
    )
    
    def is_active(self) -> bool:
        """是否激活状态"""
        return self.status == self.StatusChoices.ACTIVE
    
    def is_inactive(self) -> bool:
        """是否未激活状态"""
        return self.status == self.StatusChoices.INACTIVE
    
    def is_pending(self) -> bool:
        """是否待处理状态"""
        return self.status == self.StatusChoices.PENDING
    
    def is_suspended(self) -> bool:
        """是否暂停状态"""
        return self.status == self.StatusChoices.SUSPENDED


class OwnershipMixin:
    """所有权混入类"""
    
    owner_id = fields.IntField(description="所有者ID", index=True)
    
    async def get_owner(self):
        """获取所有者"""
        from .user import User
        return await User.get_or_none(id=self.owner_id)
    
    def is_owned_by(self, user_id: int) -> bool:
        """检查是否属于指定用户"""
        return self.owner_id == user_id


class VisibilityMixin:
    """可见性混入类"""
    
    class VisibilityChoices:
        PUBLIC = "public"
        PRIVATE = "private"
        SHARED = "shared"
        
        CHOICES = [
            (PUBLIC, "公开"),
            (PRIVATE, "私有"),
            (SHARED, "共享"),
        ]
    
    visibility = fields.CharEnumField(
        VisibilityChoices,
        default=VisibilityChoices.PRIVATE,
        description="可见性"
    )
    
    def is_public(self) -> bool:
        """是否公开"""
        return self.visibility == self.VisibilityChoices.PUBLIC
    
    def is_private(self) -> bool:
        """是否私有"""
        return self.visibility == self.VisibilityChoices.PRIVATE
    
    def is_shared(self) -> bool:
        """是否共享"""
        return self.visibility == self.VisibilityChoices.SHARED


class MetadataMixin:
    """元数据混入类"""
    
    metadata = fields.JSONField(default=dict, description="元数据")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据值"""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        self.metadata[key] = value
    
    def update_metadata(self, data: Dict[str, Any]):
        """批量更新元数据"""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        self.metadata.update(data)
    
    def remove_metadata(self, key: str):
        """删除元数据键"""
        if isinstance(self.metadata, dict) and key in self.metadata:
            del self.metadata[key]
