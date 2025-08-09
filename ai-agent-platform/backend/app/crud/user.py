"""
# Copyright (c) 2025 左岚. All rights reserved.

用户CRUD操作
"""
# # Standard library imports
from typing import Any, Dict, Optional, Union

# # Third-party imports
from sqlalchemy import or_
from sqlalchemy.orm import Session

# # Local application imports
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 邮箱地址
            
        Returns:
            用户对象或None
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象或None
        """
        return db.query(User).filter(User.username == username).first()

    def get_by_username_or_email(self, db: Session, *, identifier: str) -> Optional[User]:
        """
        根据用户名或邮箱获取用户
        
        Args:
            db: 数据库会话
            identifier: 用户名或邮箱
            
        Returns:
            用户对象或None
        """
        return db.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        创建用户
        
        Args:
            db: 数据库会话
            obj_in: 用户创建数据
            
        Returns:
            创建的用户对象
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            password_hash=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            avatar_url=obj_in.avatar_url,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        更新用户
        
        Args:
            db: 数据库会话
            db_obj: 要更新的用户对象
            obj_in: 更新数据
            
        Returns:
            更新后的用户对象
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # 如果包含密码，需要进行哈希处理
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password
            
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            认证成功的用户对象或None
        """
        user = self.get_by_username_or_email(db, identifier=username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        检查用户是否激活
        
        Args:
            user: 用户对象
            
        Returns:
            是否激活
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        检查用户是否为超级用户
        
        Args:
            user: 用户对象
            
        Returns:
            是否为超级用户
        """
        return user.is_superuser

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100):
        """
        获取激活的用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            激活用户列表
        """
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

    def search_users(self, db: Session, *, keyword: str, skip: int = 0, limit: int = 100):
        """
        搜索用户
        
        Args:
            db: 数据库会话
            keyword: 搜索关键词
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            匹配的用户列表
        """
        return db.query(User).filter(
            or_(
                User.username.contains(keyword),
                User.email.contains(keyword),
                User.full_name.contains(keyword)
            )
        ).offset(skip).limit(limit).all()


# 创建用户CRUD实例
user = CRUDUser(User)
