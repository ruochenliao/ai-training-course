"""
用户CRUD操作
处理用户相关的数据库操作
"""

from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.common import PaginationParams
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""
    
    def _build_search_query(self, search: str) -> Optional[Q]:
        """构建用户搜索查询条件"""
        return Q(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(full_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.model.get_or_none(username=username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.model.get_or_none(email=email)
    
    async def create_with_roles(self, obj_in: UserCreate) -> User:
        """创建用户并分配角色"""
        # 提取角色ID
        role_ids = obj_in.role_ids
        obj_data = obj_in.dict(exclude={"role_ids", "password"})
        
        # 加密密码
        obj_data["hashed_password"] = get_password_hash(obj_in.password)
        
        # 创建用户
        user = await self.model.create(**obj_data)
        
        # 分配角色
        if role_ids:
            roles = await Role.filter(id__in=role_ids).all()
            await user.roles.add(*roles)
        
        return user
    
    async def update_with_roles(
        self,
        user: User,
        obj_in: UserUpdate
    ) -> User:
        """更新用户并分配角色"""
        # 提取角色ID
        role_ids = obj_in.role_ids
        obj_data = obj_in.dict(exclude={"role_ids"}, exclude_unset=True)
        
        # 更新用户基本信息
        for field, value in obj_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await user.save()
        
        # 更新角色
        if role_ids is not None:
            await user.roles.clear()
            if role_ids:
                roles = await Role.filter(id__in=role_ids).all()
                await user.roles.add(*roles)
        
        return user
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.get_by_username(username)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user
    
    async def update_password(self, user: User, new_password: str) -> User:
        """更新用户密码"""
        user.hashed_password = get_password_hash(new_password)
        await user.save()
        return user
    
    async def update_last_login(self, user: User) -> User:
        """更新最后登录时间"""
        from datetime import datetime
        user.last_login = datetime.now()
        await user.save()
        return user
    
    async def get_with_roles(self, user_id: int) -> Optional[User]:
        """获取用户及其角色信息"""
        return await self.model.get_or_none(id=user_id).prefetch_related("roles")
    
    async def get_user_permissions(self, user: User) -> List[str]:
        """获取用户所有权限"""
        return await user.get_permissions()
    
    async def get_user_roles(self, user: User) -> List[str]:
        """获取用户所有角色代码"""
        return await user.get_role_codes()
    
    async def assign_roles(self, user: User, role_ids: List[int]) -> User:
        """为用户分配角色"""
        await user.roles.clear()
        if role_ids:
            roles = await Role.filter(id__in=role_ids).all()
            await user.roles.add(*roles)
        return user
    
    async def remove_roles(self, user: User, role_ids: List[int]) -> User:
        """移除用户角色"""
        if role_ids:
            roles = await Role.filter(id__in=role_ids).all()
            await user.roles.remove(*roles)
        return user
    
    async def get_active_users(self) -> List[User]:
        """获取所有激活的用户"""
        return await self.model.filter(is_active=True).all()
    
    async def get_superusers(self) -> List[User]:
        """获取所有超级用户"""
        return await self.model.filter(is_superuser=True).all()
    
    async def deactivate_user(self, user: User) -> User:
        """停用用户"""
        user.is_active = False
        await user.save()
        return user
    
    async def activate_user(self, user: User) -> User:
        """激活用户"""
        user.is_active = True
        await user.save()
        return user
    
    async def check_username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """检查用户名是否已存在"""
        query = self.model.filter(username=username)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def check_email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """检查邮箱是否已存在"""
        query = self.model.filter(email=email)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        return await query.exists()
    
    async def get_users_by_role(self, role_id: int) -> List[User]:
        """根据角色ID获取用户列表"""
        return await self.model.filter(roles__id=role_id).all()
    
    async def get_paginated_with_roles(
        self,
        params: PaginationParams,
        **filters
    ) -> tuple[List[Dict[str, Any]], int]:
        """分页获取用户及角色信息"""
        query = self.model.filter(**filters).prefetch_related("roles")
        
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
        users = await query.offset(skip).limit(params.page_size).all()
        
        # 构建返回数据
        result = []
        for user in users:
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "avatar": user.avatar,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "role_names": [role.name for role in user.roles]
            }
            result.append(user_data)
        
        return result, total


# 创建用户CRUD实例
crud_user = CRUDUser(User)
