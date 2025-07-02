"""
数据权限控制工具
提供基于部门、角色的数据访问控制功能
"""

from typing import List, Optional, Dict, Any, Type
from enum import Enum
from tortoise.models import Model
from tortoise.queryset import QuerySet
from app.models.user import User
from app.utils.permissions import DataScope


class DataPermissionFilter:
    """数据权限过滤器"""
    
    def __init__(self, user: User, data_scope: DataScope = None):
        self.user = user
        self.data_scope = data_scope or DataScope.DEPARTMENT
        self.user_department_id = getattr(user, 'department_id', None)
    
    async def apply_filter(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """
        应用数据权限过滤
        
        Args:
            queryset: 查询集
            model: 模型类
            
        Returns:
            QuerySet: 过滤后的查询集
        """
        # 超级用户可以访问所有数据
        if self.user.is_superuser:
            return queryset
        
        # 根据数据权限范围进行过滤
        if self.data_scope == DataScope.ALL:
            return queryset
        elif self.data_scope == DataScope.SELF:
            return await self._filter_self_data(queryset, model)
        elif self.data_scope == DataScope.DEPARTMENT:
            return await self._filter_department_data(queryset, model)
        elif self.data_scope == DataScope.DEPARTMENT_AND_SUB:
            return await self._filter_department_and_sub_data(queryset, model)
        elif self.data_scope == DataScope.CUSTOM:
            return await self._filter_custom_data(queryset, model)
        
        return queryset
    
    async def _filter_self_data(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """过滤仅本人数据"""
        # 检查模型是否有用户关联字段
        if hasattr(model, 'user_id'):
            return queryset.filter(user_id=self.user.id)
        elif hasattr(model, 'created_by'):
            return queryset.filter(created_by=self.user.id)
        elif hasattr(model, 'owner_id'):
            return queryset.filter(owner_id=self.user.id)
        
        # 如果没有用户关联字段，返回空查询集
        return queryset.filter(id__in=[])
    
    async def _filter_department_data(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """过滤本部门数据"""
        if not self.user_department_id:
            return await self._filter_self_data(queryset, model)
        
        # 检查模型是否有部门关联字段
        if hasattr(model, 'department_id'):
            return queryset.filter(department_id=self.user_department_id)
        elif hasattr(model, 'user__department_id'):
            return queryset.filter(user__department_id=self.user_department_id)
        
        # 如果没有部门关联字段，回退到仅本人数据
        return await self._filter_self_data(queryset, model)
    
    async def _filter_department_and_sub_data(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """过滤本部门及子部门数据"""
        if not self.user_department_id:
            return await self._filter_self_data(queryset, model)
        
        # 获取部门及其子部门ID列表
        department_ids = await self._get_department_and_sub_ids(self.user_department_id)
        
        # 检查模型是否有部门关联字段
        if hasattr(model, 'department_id'):
            return queryset.filter(department_id__in=department_ids)
        elif hasattr(model, 'user__department_id'):
            return queryset.filter(user__department_id__in=department_ids)
        
        # 如果没有部门关联字段，回退到仅本人数据
        return await self._filter_self_data(queryset, model)
    
    async def _filter_custom_data(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """过滤自定义数据权限"""
        # 获取用户的自定义数据权限规则
        custom_rules = await self._get_custom_permission_rules()
        
        for rule in custom_rules:
            if rule.get('model') == model.__name__:
                filter_conditions = rule.get('conditions', {})
                queryset = queryset.filter(**filter_conditions)
        
        return queryset
    
    async def _get_department_and_sub_ids(self, department_id: int) -> List[int]:
        """获取部门及其子部门ID列表"""
        # 这里需要根据实际的部门模型实现
        # 暂时返回当前部门ID
        return [department_id]
    
    async def _get_custom_permission_rules(self) -> List[Dict[str, Any]]:
        """获取用户的自定义数据权限规则"""
        # 这里可以从数据库或配置中获取自定义规则
        # 暂时返回空列表
        return []


class DataPermissionDecorator:
    """数据权限装饰器"""
    
    @staticmethod
    def require_data_permission(
        data_scope: DataScope = DataScope.DEPARTMENT,
        model_field: str = None
    ):
        """
        数据权限验证装饰器
        
        Args:
            data_scope: 数据权限范围
            model_field: 模型字段名（用于从kwargs中获取模型）
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise ValueError("需要current_user参数")
                
                # 创建数据权限过滤器
                data_filter = DataPermissionFilter(current_user, data_scope)
                kwargs['data_filter'] = data_filter
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class DataPermissionMixin:
    """数据权限混入类"""
    
    def __init__(self, user: User, data_scope: DataScope = None):
        self.user = user
        self.data_scope = data_scope or DataScope.DEPARTMENT
        self.data_filter = DataPermissionFilter(user, self.data_scope)
    
    async def filter_queryset(self, queryset: QuerySet, model: Type[Model]) -> QuerySet:
        """过滤查询集"""
        return await self.data_filter.apply_filter(queryset, model)
    
    async def check_data_access(self, obj: Model) -> bool:
        """检查是否有权限访问指定数据"""
        # 超级用户可以访问所有数据
        if self.user.is_superuser:
            return True
        
        # 根据数据权限范围检查
        if self.data_scope == DataScope.ALL:
            return True
        elif self.data_scope == DataScope.SELF:
            return await self._check_self_access(obj)
        elif self.data_scope == DataScope.DEPARTMENT:
            return await self._check_department_access(obj)
        elif self.data_scope == DataScope.DEPARTMENT_AND_SUB:
            return await self._check_department_and_sub_access(obj)
        elif self.data_scope == DataScope.CUSTOM:
            return await self._check_custom_access(obj)
        
        return False
    
    async def _check_self_access(self, obj: Model) -> bool:
        """检查是否有权限访问自己的数据"""
        if hasattr(obj, 'user_id'):
            return obj.user_id == self.user.id
        elif hasattr(obj, 'created_by'):
            return obj.created_by == self.user.id
        elif hasattr(obj, 'owner_id'):
            return obj.owner_id == self.user.id
        
        return False
    
    async def _check_department_access(self, obj: Model) -> bool:
        """检查是否有权限访问部门数据"""
        user_department_id = getattr(self.user, 'department_id', None)
        if not user_department_id:
            return await self._check_self_access(obj)
        
        if hasattr(obj, 'department_id'):
            return obj.department_id == user_department_id
        elif hasattr(obj, 'user') and hasattr(obj.user, 'department_id'):
            return obj.user.department_id == user_department_id
        
        return await self._check_self_access(obj)
    
    async def _check_department_and_sub_access(self, obj: Model) -> bool:
        """检查是否有权限访问部门及子部门数据"""
        user_department_id = getattr(self.user, 'department_id', None)
        if not user_department_id:
            return await self._check_self_access(obj)
        
        # 获取部门及其子部门ID列表
        department_ids = await self.data_filter._get_department_and_sub_ids(user_department_id)
        
        if hasattr(obj, 'department_id'):
            return obj.department_id in department_ids
        elif hasattr(obj, 'user') and hasattr(obj.user, 'department_id'):
            return obj.user.department_id in department_ids
        
        return await self._check_self_access(obj)
    
    async def _check_custom_access(self, obj: Model) -> bool:
        """检查自定义数据权限"""
        # 实现自定义权限检查逻辑
        return True


# 便捷的装饰器函数
def require_data_permission(data_scope: DataScope = DataScope.DEPARTMENT):
    """数据权限装饰器快捷方法"""
    return DataPermissionDecorator.require_data_permission(data_scope)


# 便捷的权限检查函数
async def check_data_access(user: User, obj: Model, data_scope: DataScope = DataScope.DEPARTMENT) -> bool:
    """检查数据访问权限"""
    permission_mixin = DataPermissionMixin(user, data_scope)
    return await permission_mixin.check_data_access(obj)


async def filter_data_by_permission(
    user: User, 
    queryset: QuerySet, 
    model: Type[Model], 
    data_scope: DataScope = DataScope.DEPARTMENT
) -> QuerySet:
    """根据权限过滤数据"""
    data_filter = DataPermissionFilter(user, data_scope)
    return await data_filter.apply_filter(queryset, model)
