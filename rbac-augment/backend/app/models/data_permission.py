"""
数据权限模型
处理数据级别的权限控制
"""

from tortoise.models import Model
from tortoise import fields
from typing import List, Dict, Any, Optional
from enum import Enum


class DataPermissionType(str, Enum):
    """数据权限类型"""
    ALL = "all"  # 全部数据
    SELF = "self"  # 仅本人数据
    DEPARTMENT = "department"  # 本部门数据
    DEPARTMENT_AND_SUB = "department_and_sub"  # 本部门及子部门数据
    CUSTOM = "custom"  # 自定义数据范围


class DataPermissionScope(str, Enum):
    """数据权限范围"""
    USER = "user"  # 用户数据
    DEPARTMENT = "department"  # 部门数据
    ROLE = "role"  # 角色数据
    CUSTOM = "custom"  # 自定义数据


class DataPermission(Model):
    """数据权限模型"""
    
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, description="权限名称")
    code = fields.CharField(max_length=100, unique=True, description="权限代码")
    description = fields.TextField(null=True, description="权限描述")
    
    # 权限配置
    permission_type = fields.CharEnumField(DataPermissionType, description="权限类型")
    scope = fields.CharEnumField(DataPermissionScope, description="权限范围")
    resource_type = fields.CharField(max_length=50, description="资源类型")
    
    # 自定义条件（JSON格式）
    custom_conditions = fields.JSONField(null=True, description="自定义条件")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否启用")
    sort_order = fields.IntField(default=0, description="排序")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 关联关系
    roles = fields.ManyToManyField(
        "models.Role",
        related_name="data_permissions",
        through="role_data_permission",
        description="关联角色"
    )
    
    users = fields.ManyToManyField(
        "models.User",
        related_name="data_permissions",
        through="user_data_permission",
        description="关联用户"
    )
    
    class Meta:
        table = "data_permissions"
        table_description = "数据权限表"
    
    def __str__(self):
        return f"DataPermission(name={self.name}, code={self.code})"
    
    async def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude_fields = exclude_fields or []
        
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "permission_type": self.permission_type,
            "scope": self.scope,
            "resource_type": self.resource_type,
            "custom_conditions": self.custom_conditions,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # 排除指定字段
        for field in exclude_fields:
            data.pop(field, None)
        
        return data
    
    async def get_applicable_users(self) -> List["User"]:
        """获取适用的用户列表"""
        from .user import User
        
        # 直接关联的用户
        direct_users = await self.users.all()
        
        # 通过角色关联的用户
        role_users = []
        roles = await self.roles.all()
        for role in roles:
            users = await role.users.all()
            role_users.extend(users)
        
        # 去重
        all_users = list({user.id: user for user in direct_users + role_users}.values())
        return all_users
    
    async def check_data_access(self, user: "User", resource_id: int = None, **kwargs) -> bool:
        """检查用户是否有数据访问权限"""
        if not self.is_active:
            return False
        
        # 检查用户是否在适用范围内
        applicable_users = await self.get_applicable_users()
        if user not in applicable_users:
            return False
        
        # 根据权限类型检查
        if self.permission_type == DataPermissionType.ALL:
            return True
        elif self.permission_type == DataPermissionType.SELF:
            return await self._check_self_permission(user, resource_id, **kwargs)
        elif self.permission_type == DataPermissionType.DEPARTMENT:
            return await self._check_department_permission(user, resource_id, **kwargs)
        elif self.permission_type == DataPermissionType.DEPARTMENT_AND_SUB:
            return await self._check_department_and_sub_permission(user, resource_id, **kwargs)
        elif self.permission_type == DataPermissionType.CUSTOM:
            return await self._check_custom_permission(user, resource_id, **kwargs)
        
        return False
    
    async def _check_self_permission(self, user: "User", resource_id: int = None, **kwargs) -> bool:
        """检查自己的数据权限"""
        if self.scope == DataPermissionScope.USER:
            return resource_id == user.id if resource_id else True
        # 其他范围的自己数据检查逻辑
        return True
    
    async def _check_department_permission(self, user: "User", resource_id: int = None, **kwargs) -> bool:
        """检查部门数据权限"""
        if not user.department_id:
            return False
        
        if self.scope == DataPermissionScope.USER:
            # 检查目标用户是否在同一部门
            from .user import User
            target_user = await User.get_or_none(id=resource_id)
            return target_user and target_user.department_id == user.department_id
        elif self.scope == DataPermissionScope.DEPARTMENT:
            # 检查目标部门是否是同一部门
            return resource_id == user.department_id
        
        return True
    
    async def _check_department_and_sub_permission(self, user: "User", resource_id: int = None, **kwargs) -> bool:
        """检查部门及子部门数据权限"""
        if not user.department_id:
            return False
        
        from .department import Department
        user_dept = await Department.get_or_none(id=user.department_id)
        if not user_dept:
            return False
        
        if self.scope == DataPermissionScope.USER:
            # 检查目标用户是否在本部门或子部门
            from .user import User
            target_user = await User.get_or_none(id=resource_id)
            if not target_user or not target_user.department_id:
                return False
            
            target_dept = await Department.get_or_none(id=target_user.department_id)
            if not target_dept:
                return False
            
            # 检查是否是子部门
            return await target_dept.is_descendant_of(user_dept)
        elif self.scope == DataPermissionScope.DEPARTMENT:
            # 检查目标部门是否是子部门
            target_dept = await Department.get_or_none(id=resource_id)
            if not target_dept:
                return False
            
            return await target_dept.is_descendant_of(user_dept)
        
        return True
    
    async def _check_custom_permission(self, user: "User", resource_id: int = None, **kwargs) -> bool:
        """检查自定义数据权限"""
        if not self.custom_conditions:
            return False
        
        # 这里可以实现复杂的自定义权限逻辑
        # 例如：基于用户属性、时间、地理位置等条件
        conditions = self.custom_conditions
        
        # 示例：检查用户级别
        if "user_level" in conditions:
            required_level = conditions["user_level"]
            user_level = getattr(user, "level", 0)
            if user_level < required_level:
                return False
        
        # 示例：检查时间范围
        if "time_range" in conditions:
            from datetime import datetime, time
            now = datetime.now().time()
            start_time = time.fromisoformat(conditions["time_range"]["start"])
            end_time = time.fromisoformat(conditions["time_range"]["end"])
            if not (start_time <= now <= end_time):
                return False
        
        return True


class UserDataPermission(Model):
    """用户数据权限关联表"""
    
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="user_data_permissions")
    data_permission = fields.ForeignKeyField("models.DataPermission", related_name="user_data_permissions")
    granted_at = fields.DatetimeField(auto_now_add=True, description="授权时间")
    granted_by = fields.ForeignKeyField("models.User", related_name="granted_data_permissions", null=True)
    
    class Meta:
        table = "user_data_permissions"
        unique_together = (("user", "data_permission"),)


class RoleDataPermission(Model):
    """角色数据权限关联表"""
    
    id = fields.IntField(pk=True)
    role = fields.ForeignKeyField("models.Role", related_name="role_data_permissions")
    data_permission = fields.ForeignKeyField("models.DataPermission", related_name="role_data_permissions")
    granted_at = fields.DatetimeField(auto_now_add=True, description="授权时间")
    granted_by = fields.ForeignKeyField("models.User", related_name="granted_role_data_permissions", null=True)
    
    class Meta:
        table = "role_data_permissions"
        unique_together = (("role", "data_permission"),)
