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

    # 部门信息
    department_id = fields.IntField(null=True, description="所属部门ID")
    
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
        from .rbac import UserRole
        user_roles = await UserRole.filter(user_id=self.id).prefetch_related("role")
        # 过滤未过期的角色
        active_roles = []
        for ur in user_roles:
            if not ur.is_expired() and ur.role.status == "active":
                active_roles.append(ur.role)
        return active_roles

    async def get_permissions(self) -> List["Permission"]:
        """获取用户权限（角色权限 + 直接权限）"""
        from .rbac import UserPermission

        # 1. 获取角色权限
        roles = await self.get_roles()
        role_permissions = []
        for role in roles:
            role_perms = await role.get_permissions()
            role_permissions.extend(role_perms)

        # 2. 获取直接权限
        user_permissions = await UserPermission.filter(user_id=self.id).prefetch_related("permission")
        direct_permissions = []
        denied_permissions = set()

        for up in user_permissions:
            if not up.is_expired() and up.permission.status == "active":
                if up.permission_type == "grant":
                    direct_permissions.append(up.permission)
                elif up.permission_type == "deny":
                    denied_permissions.add(up.permission.code)

        # 3. 合并权限并处理拒绝权限
        all_permissions = role_permissions + direct_permissions
        unique_permissions = {}
        for perm in all_permissions:
            if perm.code not in denied_permissions:
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

    async def get_department(self) -> Optional["Department"]:
        """获取用户部门"""
        if self.department_id:
            from .rbac import Department
            return await Department.get_or_none(id=self.department_id)
        return None

    async def get_data_scope_departments(self) -> List["Department"]:
        """获取用户数据权限范围内的部门"""
        from .rbac import UserRole, Department

        if self.is_superuser:
            # 超级用户可以访问所有部门
            return await Department.all()

        dept_ids = set()
        user_roles = await UserRole.filter(user_id=self.id).prefetch_related("role")

        for ur in user_roles:
            if not ur.is_expired() and ur.role.status == "active":
                role = ur.role

                if role.data_scope == "all":
                    # 全部数据权限
                    return await Department.all()
                elif role.data_scope == "dept":
                    # 本部门数据权限
                    if self.department_id:
                        dept_ids.add(self.department_id)
                elif role.data_scope == "dept_and_child":
                    # 本部门及子部门数据权限
                    if self.department_id:
                        dept = await self.get_department()
                        if dept:
                            dept_ids.add(dept.id)
                            children = await dept.get_all_children()
                            dept_ids.update([child.id for child in children])
                elif role.data_scope == "custom":
                    # 自定义数据权限
                    dept_ids.update(ur.dept_ids)

        if dept_ids:
            return await Department.filter(id__in=list(dept_ids))
        return []


# 注意：Role、Permission等RBAC模型已移动到rbac.py文件中
# 这里保留引用以保持向后兼容性

def __getattr__(name):
    """动态导入RBAC模型"""
    if name in ['Role', 'Permission', 'UserRole', 'RolePermission', 'Department']:
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


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
