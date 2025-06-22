"""
用户相关数据模型
"""

from datetime import datetime
from typing import List, Optional

from passlib.context import CryptContext
from tortoise import fields

from .base import BaseModel, TimestampMixin, StatusMixin, SoftDeleteMixin, MetadataMixin

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel, TimestampMixin, StatusMixin, SoftDeleteMixin, MetadataMixin):
    """用户模型"""
    
    # 基本信息
    username = fields.CharField(max_length=50, unique=True, description="用户名", index=True)
    email = fields.CharField(max_length=100, unique=True, description="邮箱", index=True)
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    
    # 认证信息
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    is_email_verified = fields.BooleanField(default=False, description="邮箱是否已验证")
    is_phone_verified = fields.BooleanField(default=False, description="手机号是否已验证")
    
    # 个人信息
    full_name = fields.CharField(max_length=100, null=True, description="全名")
    avatar_url = fields.CharField(max_length=500, null=True, description="头像URL")
    bio = fields.TextField(null=True, description="个人简介")
    
    # 权限信息
    is_superuser = fields.BooleanField(default=False, description="是否为超级用户")
    is_staff = fields.BooleanField(default=False, description="是否为员工")
    
    # 登录信息
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")
    last_login_ip = fields.CharField(max_length=45, null=True, description="最后登录IP")
    login_count = fields.IntField(default=0, description="登录次数")
    
    # 安全信息
    failed_login_attempts = fields.IntField(default=0, description="失败登录尝试次数")
    locked_until = fields.DatetimeField(null=True, description="锁定到期时间")
    password_changed_at = fields.DatetimeField(null=True, description="密码修改时间")
    
    # 偏好设置
    language = fields.CharField(max_length=10, default="zh-CN", description="语言偏好")
    timezone = fields.CharField(max_length=50, default="Asia/Shanghai", description="时区")
    theme = fields.CharField(max_length=20, default="light", description="主题偏好")
    
    class Meta:
        table = "users"
        indexes = [
            ["username", "email"],
            ["status", "is_deleted"],
            ["created_at"],
        ]
    
    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.now()
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(password, self.password_hash)
    
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until:
            return datetime.now() < self.locked_until
        return False
    
    def lock_account(self, duration_minutes: int = 30):
        """锁定账户"""
        from datetime import timedelta
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self):
        """解锁账户"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_login(self, ip_address: str = None):
        """记录登录"""
        self.last_login_at = datetime.now()
        self.last_login_ip = ip_address
        self.login_count += 1
        self.failed_login_attempts = 0
    
    def record_failed_login(self):
        """记录失败登录"""
        self.failed_login_attempts += 1
        
        # 如果失败次数过多，锁定账户
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    async def get_roles(self) -> List["Role"]:
        """获取用户角色"""
        user_roles = await UserRole.filter(user_id=self.id).prefetch_related("role")
        return [ur.role for ur in user_roles]
    
    async def get_permissions(self) -> List["Permission"]:
        """获取用户权限"""
        roles = await self.get_roles()
        permissions = []
        for role in roles:
            role_permissions = await role.get_permissions()
            permissions.extend(role_permissions)
        
        # 去重
        unique_permissions = {}
        for perm in permissions:
            unique_permissions[perm.code] = perm
        
        return list(unique_permissions.values())
    
    async def has_permission(self, permission_code: str) -> bool:
        """检查是否有指定权限"""
        if self.is_superuser:
            return True
        
        permissions = await self.get_permissions()
        return any(perm.code == permission_code for perm in permissions)
    
    async def has_role(self, role_code: str) -> bool:
        """检查是否有指定角色"""
        roles = await self.get_roles()
        return any(role.code == role_code for role in roles)


class Role(BaseModel, TimestampMixin, StatusMixin, MetadataMixin):
    """角色模型"""
    
    name = fields.CharField(max_length=50, description="角色名称")
    code = fields.CharField(max_length=50, unique=True, description="角色代码", index=True)
    description = fields.TextField(null=True, description="角色描述")
    
    # 层级关系
    parent_id = fields.IntField(null=True, description="父角色ID")
    level = fields.IntField(default=0, description="角色层级")
    sort_order = fields.IntField(default=0, description="排序")
    
    class Meta:
        table = "roles"
        indexes = [
            ["code"],
            ["parent_id", "level"],
            ["status"],
        ]
    
    async def get_permissions(self) -> List["Permission"]:
        """获取角色权限"""
        role_permissions = await RolePermission.filter(role_id=self.id).prefetch_related("permission")
        return [rp.permission for rp in role_permissions]
    
    async def add_permission(self, permission: "Permission"):
        """添加权限"""
        await RolePermission.get_or_create(role_id=self.id, permission_id=permission.id)
    
    async def remove_permission(self, permission: "Permission"):
        """移除权限"""
        await RolePermission.filter(role_id=self.id, permission_id=permission.id).delete()
    
    async def get_children(self) -> List["Role"]:
        """获取子角色"""
        return await Role.filter(parent_id=self.id)
    
    async def get_parent(self) -> Optional["Role"]:
        """获取父角色"""
        if self.parent_id:
            return await Role.get_or_none(id=self.parent_id)
        return None


class Permission(BaseModel, TimestampMixin, StatusMixin, MetadataMixin):
    """权限模型"""
    
    name = fields.CharField(max_length=50, description="权限名称")
    code = fields.CharField(max_length=100, unique=True, description="权限代码", index=True)
    description = fields.TextField(null=True, description="权限描述")
    
    # 权限分组
    group = fields.CharField(max_length=50, description="权限分组", index=True)
    
    # 资源和操作
    resource = fields.CharField(max_length=50, description="资源")
    action = fields.CharField(max_length=50, description="操作")
    
    class Meta:
        table = "permissions"
        indexes = [
            ["code"],
            ["group"],
            ["resource", "action"],
            ["status"],
        ]


class UserRole(BaseModel, TimestampMixin):
    """用户角色关联模型"""
    
    user = fields.ForeignKeyField("models.User", related_name="user_roles", on_delete=fields.CASCADE)
    role = fields.ForeignKeyField("models.Role", related_name="role_users", on_delete=fields.CASCADE)
    
    # 授权信息
    granted_by = fields.IntField(description="授权人ID")
    granted_at = fields.DatetimeField(auto_now_add=True, description="授权时间")
    expires_at = fields.DatetimeField(null=True, description="过期时间")
    
    class Meta:
        table = "user_roles"
        unique_together = [["user", "role"]]
        indexes = [
            ["user_id", "role_id"],
            ["expires_at"],
        ]
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


class RolePermission(BaseModel, TimestampMixin):
    """角色权限关联模型"""
    
    role = fields.ForeignKeyField("models.Role", related_name="role_permissions", on_delete=fields.CASCADE)
    permission = fields.ForeignKeyField("models.Permission", related_name="permission_roles", on_delete=fields.CASCADE)
    
    class Meta:
        table = "role_permissions"
        unique_together = [["role", "permission"]]
        indexes = [
            ["role_id", "permission_id"],
        ]


class UserSession(BaseModel, TimestampMixin):
    """用户会话模型"""
    
    user = fields.ForeignKeyField("models.User", related_name="sessions", on_delete=fields.CASCADE)
    session_id = fields.CharField(max_length=255, unique=True, description="会话ID", index=True)
    
    # 会话信息
    ip_address = fields.CharField(max_length=45, description="IP地址")
    user_agent = fields.TextField(description="用户代理")
    device_info = fields.JSONField(default=dict, description="设备信息")
    
    # 状态信息
    is_active = fields.BooleanField(default=True, description="是否活跃")
    last_activity_at = fields.DatetimeField(auto_now=True, description="最后活动时间")
    expires_at = fields.DatetimeField(description="过期时间")
    
    class Meta:
        table = "user_sessions"
        indexes = [
            ["user_id", "is_active"],
            ["session_id"],
            ["expires_at"],
        ]
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at
    
    async def refresh(self, extend_minutes: int = 60):
        """刷新会话"""
        from datetime import timedelta
        self.last_activity_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=extend_minutes)
        await self.save(update_fields=["last_activity_at", "expires_at"])


class UserEvent(BaseModel, TimestampMixin):
    """用户事件模型"""

    user = fields.ForeignKeyField("models.User", related_name="events", on_delete=fields.CASCADE)
    session_id = fields.CharField(max_length=255, description="会话ID", index=True)

    # 事件信息
    event_type = fields.CharField(max_length=50, description="事件类型", index=True)
    properties = fields.JSONField(default=dict, description="事件属性")

    # 请求信息
    ip_address = fields.CharField(max_length=45, description="IP地址")
    user_agent = fields.TextField(description="用户代理")

    class Meta:
        table = "user_events"
        indexes = [
            ["user_id", "event_type"],
            ["session_id"],
            ["event_type", "created_at"],
            ["created_at"],
        ]
