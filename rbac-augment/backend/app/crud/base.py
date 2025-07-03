"""
基础CRUD操作类
提供通用的数据库操作方法
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.expressions import Q
from ..schemas.common import PaginationParams


ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础CRUD操作类"""
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象
        
        Args:
            model: Tortoise ORM模型类
        """
        self.model = model
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        return await self.model.get_or_none(id=id)
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """获取多个对象"""
        query = self.model.filter(**filters)
        return await query.offset(skip).limit(limit).all()
    
    async def get_paginated(
        self,
        params: PaginationParams,
        **filters
    ) -> tuple[List[ModelType], int]:
        """分页获取对象"""
        query = self.model.filter(**filters)
        
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
        
        # 分页
        skip = (params.page - 1) * params.page_size
        items = await query.offset(skip).limit(params.page_size).all()
        
        return items, total
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建对象"""
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        return await self.model.create(**obj_data)
    
    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新对象"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db_obj.save()
        return db_obj
    
    async def delete(self, id: Any) -> bool:
        """删除对象"""
        obj = await self.get(id)
        if obj:
            await obj.delete()
            return True
        return False
    
    async def delete_multi(self, ids: List[Any]) -> int:
        """批量删除对象"""
        deleted_count = await self.model.filter(id__in=ids).delete()
        return deleted_count
    
    async def exists(self, **filters) -> bool:
        """检查对象是否存在"""
        return await self.model.filter(**filters).exists()
    
    async def count(self, **filters) -> int:
        """统计对象数量"""
        return await self.model.filter(**filters).count()
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """根据字段值获取对象"""
        return await self.model.get_or_none(**{field: value})
    
    async def get_multi_by_field(
        self,
        field: str,
        values: List[Any]
    ) -> List[ModelType]:
        """根据字段值列表获取多个对象"""
        return await self.model.filter(**{f"{field}__in": values}).all()
    
    def _build_search_query(self, search: str) -> Optional[Q]:
        """构建搜索查询条件（子类可重写）"""
        return None
    
    async def bulk_create(self, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """批量创建对象"""
        obj_data_list = []
        for obj_in in objs_in:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            obj_data_list.append(obj_data)
        
        return await self.model.bulk_create([
            self.model(**obj_data) for obj_data in obj_data_list
        ])
    
    async def bulk_update(
        self,
        objs: List[ModelType],
        fields: List[str]
    ) -> None:
        """批量更新对象"""
        await self.model.bulk_update(objs, fields)
    
    async def get_or_create(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> tuple[ModelType, bool]:
        """获取或创建对象"""
        obj = await self.model.get_or_none(**kwargs)
        if obj:
            return obj, False
        
        create_data = {**kwargs}
        if defaults:
            create_data.update(defaults)
        
        obj = await self.model.create(**create_data)
        return obj, True
