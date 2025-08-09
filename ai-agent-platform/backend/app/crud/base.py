"""
# Copyright (c) 2025 左岚. All rights reserved.

通用CRUD基类
"""
# # Standard library imports
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

# # Third-party imports
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

# # Local application imports
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用CRUD基类
    提供基本的增删改查操作
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象
        
        Args:
            model: SQLAlchemy模型类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        根据ID获取单个对象
        
        Args:
            db: 数据库会话
            id: 对象ID
            
        Returns:
            模型对象或None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个对象
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            模型对象列表
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新对象
        
        Args:
            db: 数据库会话
            obj_in: 创建对象的数据
            
        Returns:
            创建的模型对象
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新对象
        
        Args:
            db: 数据库会话
            db_obj: 要更新的数据库对象
            obj_in: 更新数据
            
        Returns:
            更新后的模型对象
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        删除对象
        
        Args:
            db: 数据库会话
            id: 要删除的对象ID
            
        Returns:
            被删除的模型对象
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def count(self, db: Session) -> int:
        """
        获取对象总数
        
        Args:
            db: 数据库会话
            
        Returns:
            对象总数
        """
        return db.query(self.model).count()

    def exists(self, db: Session, id: Any) -> bool:
        """
        检查对象是否存在
        
        Args:
            db: 数据库会话
            id: 对象ID
            
        Returns:
            是否存在
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
