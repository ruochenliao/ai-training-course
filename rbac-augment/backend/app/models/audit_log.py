"""
审计日志模型
记录系统中的重要操作和变更
"""

from tortoise.models import Model
from tortoise import fields
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"  # 创建
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 删除
    LOGIN = "login"    # 登录
    LOGOUT = "logout"  # 登出
    ASSIGN = "assign"  # 分配
    REVOKE = "revoke"  # 撤销
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入
    VIEW = "view"      # 查看
    DOWNLOAD = "download"  # 下载


class AuditLevel(str, Enum):
    """审计级别"""
    LOW = "low"        # 低级别
    MEDIUM = "medium"  # 中级别
    HIGH = "high"      # 高级别
    CRITICAL = "critical"  # 关键级别


class AuditStatus(str, Enum):
    """审计状态"""
    SUCCESS = "success"  # 成功
    FAILED = "failed"    # 失败
    PENDING = "pending"  # 待处理


class AuditLog(Model):
    """审计日志模型"""
    
    id = fields.IntField(pk=True, description="主键ID")
    
    # 操作信息
    action = fields.CharEnumField(AuditAction, description="操作类型")
    resource_type = fields.CharField(max_length=50, description="资源类型")
    resource_id = fields.CharField(max_length=100, null=True, description="资源ID")
    resource_name = fields.CharField(max_length=200, null=True, description="资源名称")
    
    # 操作描述
    description = fields.TextField(description="操作描述")
    details = fields.JSONField(null=True, description="详细信息")
    
    # 操作结果
    status = fields.CharEnumField(AuditStatus, default=AuditStatus.SUCCESS, description="操作状态")
    level = fields.CharEnumField(AuditLevel, default=AuditLevel.MEDIUM, description="审计级别")
    
    # 用户信息
    username = fields.CharField(max_length=50, null=True, description="操作用户名")
    user_ip = fields.CharField(max_length=45, null=True, description="用户IP地址")
    user_agent = fields.TextField(null=True, description="用户代理")

    # 请求信息
    request_method = fields.CharField(max_length=10, null=True, description="请求方法")
    request_url = fields.TextField(null=True, description="请求URL")
    request_params = fields.JSONField(null=True, description="请求参数")

    # 响应信息
    response_status = fields.IntField(null=True, description="响应状态码")
    response_time = fields.IntField(null=True, description="响应时间(毫秒)")

    # 变更信息
    old_values = fields.JSONField(null=True, description="变更前的值")
    new_values = fields.JSONField(null=True, description="变更后的值")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    # 关联关系
    user = fields.ForeignKeyField(
        "models.User",
        related_name="audit_logs",
        null=True,
        description="操作用户"
    )
    
    class Meta:
        table = "audit_logs"
        table_description = "审计日志表"
    
    def __str__(self):
        return f"AuditLog(action={self.action}, resource={self.resource_type}, user={self.username})"
    
    async def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude_fields = exclude_fields or []
        
        data = {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "description": self.description,
            "details": self.details,
            "status": self.status,
            "level": self.level,
            "user_id": self.user_id,
            "username": self.username,
            "user_ip": self.user_ip,
            "user_agent": self.user_agent,
            "request_method": self.request_method,
            "request_url": self.request_url,
            "request_params": self.request_params,
            "response_status": self.response_status,
            "response_time": self.response_time,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "created_at": self.created_at
        }
        
        # 排除指定字段
        for field in exclude_fields:
            data.pop(field, None)
        
        return data
    
    @classmethod
    async def log_action(
        cls,
        action: AuditAction,
        resource_type: str,
        description: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.MEDIUM,
        status: AuditStatus = AuditStatus.SUCCESS,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_url: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        response_time: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> "AuditLog":
        """记录审计日志"""
        
        log_data = {
            "action": action,
            "resource_type": resource_type,
            "description": description,
            "level": level,
            "status": status
        }
        
        # 添加可选字段
        optional_fields = {
            "user_id": user_id,
            "username": username,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "details": details,
            "user_ip": user_ip,
            "user_agent": user_agent,
            "request_method": request_method,
            "request_url": request_url,
            "request_params": request_params,
            "response_status": response_status,
            "response_time": response_time,
            "old_values": old_values,
            "new_values": new_values
        }
        
        for key, value in optional_fields.items():
            if value is not None:
                log_data[key] = value
        
        return await cls.create(**log_data)
    
    @classmethod
    async def log_user_action(
        cls,
        user: "User",
        action: AuditAction,
        resource_type: str,
        description: str,
        **kwargs
    ) -> "AuditLog":
        """记录用户操作日志"""
        return await cls.log_action(
            action=action,
            resource_type=resource_type,
            description=description,
            user_id=user.id,
            username=user.username,
            **kwargs
        )
    
    @classmethod
    async def log_login(
        cls,
        user: "User",
        user_ip: str,
        user_agent: str,
        success: bool = True
    ) -> "AuditLog":
        """记录登录日志"""
        return await cls.log_action(
            action=AuditAction.LOGIN,
            resource_type="auth",
            description=f"用户 {user.username} {'成功' if success else '失败'}登录",
            user_id=user.id,
            username=user.username,
            user_ip=user_ip,
            user_agent=user_agent,
            level=AuditLevel.MEDIUM if success else AuditLevel.HIGH,
            status=AuditStatus.SUCCESS if success else AuditStatus.FAILED
        )
    
    @classmethod
    async def log_logout(
        cls,
        user: "User",
        user_ip: str,
        user_agent: str
    ) -> "AuditLog":
        """记录登出日志"""
        return await cls.log_action(
            action=AuditAction.LOGOUT,
            resource_type="auth",
            description=f"用户 {user.username} 登出",
            user_id=user.id,
            username=user.username,
            user_ip=user_ip,
            user_agent=user_agent,
            level=AuditLevel.LOW
        )
    
    @classmethod
    async def log_data_change(
        cls,
        user: "User",
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "AuditLog":
        """记录数据变更日志"""
        
        if action == AuditAction.CREATE:
            description = f"创建{resource_type}: {resource_name}"
            level = AuditLevel.MEDIUM
        elif action == AuditAction.UPDATE:
            description = f"更新{resource_type}: {resource_name}"
            level = AuditLevel.MEDIUM
        elif action == AuditAction.DELETE:
            description = f"删除{resource_type}: {resource_name}"
            level = AuditLevel.HIGH
        else:
            description = f"{action.value}{resource_type}: {resource_name}"
            level = AuditLevel.MEDIUM
        
        return await cls.log_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            user_id=user.id,
            username=user.username,
            old_values=old_values,
            new_values=new_values,
            level=level,
            **kwargs
        )
    
    @classmethod
    async def log_permission_change(
        cls,
        user: "User",
        action: AuditAction,
        target_type: str,
        target_name: str,
        permission_names: List[str],
        **kwargs
    ) -> "AuditLog":
        """记录权限变更日志"""
        
        action_text = "分配" if action == AuditAction.ASSIGN else "撤销"
        description = f"{action_text}{target_type}权限: {target_name}, 权限: {', '.join(permission_names)}"
        
        return await cls.log_action(
            action=action,
            resource_type="permission",
            description=description,
            user_id=user.id,
            username=user.username,
            level=AuditLevel.HIGH,
            details={
                "target_type": target_type,
                "target_name": target_name,
                "permissions": permission_names
            },
            **kwargs
        )
