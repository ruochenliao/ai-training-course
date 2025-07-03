"""
用户模型
定义用户表结构和相关方法
"""

from tortoise import fields
from passlib.hash import bcrypt

from .base import BaseModel
from typing import List


class User(BaseModel):
    """用户模型"""
    
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=255, unique=True, description="电子邮箱")
    hashed_password = fields.CharField(max_length=128, description="哈希密码")
    full_name = fields.CharField(max_length=100, null=True, description="姓名")
    phone = fields.CharField(max_length=20, null=True, description="电话")
    avatar = fields.CharField(max_length=255, null=True, description="头像地址")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级用户")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")

    # 关联部门（外键）
    department = fields.ForeignKeyField(
        'models.Department',
        related_name='users',
        null=True,
        description="所属部门"
    )

    # 关联角色（多对多）
    roles = fields.ManyToManyField(
        'models.Role',
        related_name='users',
        through='user_role',
        description="用户角色"
    )
    
    class Meta:
        table = "users"
        table_description = "用户表"
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @classmethod
    def get_by_username(cls, username: str):
        """通过用户名获取用户"""
        return cls.filter(username=username, is_active=True, is_deleted=False).first()
    
    @classmethod
    def get_by_email(cls, email: str):
        """通过邮箱获取用户"""
        return cls.filter(email=email, is_active=True, is_deleted=False).first()
    
    def verify_password(self, password: str) -> bool:
        """验证用户密码"""
        return bcrypt.verify(password, self.hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码哈希"""
        return bcrypt.hash(password)
    
    async def to_dict(self, include_department: bool = True):
        """将用户转换为字典"""
        base_dict = super().to_dict()

        # 获取用户角色
        roles = await self.roles.all()
        role_list = [{"id": role.id, "name": role.name} for role in roles]

        # 获取部门信息
        department_info = None
        if include_department and self.department_id:
            try:
                await self.fetch_related("department")
                if self.department:
                    department_info = {
                        "id": self.department.id,
                        "name": self.department.name,
                        "code": self.department.code
                    }
            except:
                # 如果获取部门信息失败，设置为None
                department_info = None

        # 组合返回结果
        return {
            **base_dict,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "avatar": self.avatar,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "department_id": self.department_id,
            "department": department_info,
            "roles": role_list
        }
    
    async def get_permissions(self) -> List[str]:
        """获取用户所有权限代码"""
        permissions = set()
        
        # 获取用户所有角色的权限
        await self.fetch_related("roles__permissions")
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.code)
        
        return list(permissions)
    
    async def has_permission(self, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        if self.is_superuser:
            return True
            
        user_permissions = await self.get_permissions()
        return permission_code in user_permissions
    
    async def has_any_permission(self, permission_codes: List[str]) -> bool:
        """检查用户是否拥有任意一个指定权限"""
        if self.is_superuser:
            return True
            
        user_permissions = await self.get_permissions()
        return any(code in user_permissions for code in permission_codes)
    
    async def has_all_permissions(self, permission_codes: List[str]) -> bool:
        """检查用户是否拥有所有指定权限"""
        if self.is_superuser:
            return True
            
        user_permissions = await self.get_permissions()
        return all(code in user_permissions for code in permission_codes)

    async def get_department(self):
        """获取用户所属部门"""
        if not self.department_id:
            return None

        await self.fetch_related("department")
        return self.department

    async def get_department_path(self) -> str:
        """获取用户部门路径"""
        department = await self.get_department()
        if not department:
            return "无部门"

        return await department.get_path()

    async def is_department_manager(self) -> bool:
        """检查用户是否为部门负责人"""
        if not self.department_id:
            return False

        department = await self.get_department()
        return department and department.manager_id == self.id

    async def get_managed_departments(self):
        """获取用户管理的部门列表"""
        from app.models.department import Department
        return await Department.filter(manager_id=self.id, is_deleted=False)

    async def can_access_department_data(self, target_department_id: int) -> bool:
        """检查用户是否可以访问指定部门的数据"""
        if self.is_superuser:
            return True

        # 如果是同一个部门，可以访问
        if self.department_id == target_department_id:
            return True

        # 如果是部门负责人，可以访问本部门及子部门数据
        if await self.is_department_manager():
            department = await self.get_department()
            if department:
                descendants = await department.get_descendants()
                descendant_ids = [d.id for d in descendants]
                return target_department_id in descendant_ids

        return False
    
    async def get_role_codes(self) -> List[str]:
        """获取用户所有角色代码"""
        await self.fetch_related("roles")
        return [role.code for role in self.roles]
    
    async def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色"""
        role_codes = await self.get_role_codes()
        return role_code in role_codes
