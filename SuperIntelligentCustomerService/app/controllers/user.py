from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException

from .role import role_controller
from ..core.crud import CRUDBase
from ..models.admin import User
from ..schemas.login import CredentialsSchema
from ..schemas.users import UserCreate, UserUpdate
from ..utils.password import get_password_hash, verify_password


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create_user(self, obj_in: UserCreate) -> User:
        obj_in.password = get_password_hash(password=obj_in.password)
        obj = await self.create(obj_in)
        return obj

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        user = None

        # 判断输入是否为邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email = re.match(email_pattern, credentials.username)

        if is_email:
            # 如果是邮箱格式，直接通过邮箱查找
            user = await self.model.filter(email=credentials.username).first()
        else:
            # 如果不是邮箱格式，先尝试通过用户名查找
            user = await self.model.filter(username=credentials.username).first()

            # 如果通过用户名没找到，再尝试通过邮箱查找（兼容性）
            if not user:
                user = await self.model.filter(email=credentials.username).first()

        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名或邮箱")

        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_controller.get(id=role_id)
            await user.roles.add(role_obj)

    async def reset_password(self, user_id: int):
        user_obj = await self.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")
        user_obj.password = get_password_hash(password="123456")
        await user_obj.save()


user_controller = UserController()
