"""
系统相关数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from tortoise import fields

from .base import BaseModel, TimestampMixin, StatusMixin, MetadataMixin


class ConfigType(str, Enum):
    """配置类型枚举"""
    SYSTEM = "system"
    AI_MODEL = "ai_model"
    DATABASE = "database"
    SECURITY = "security"
    FEATURE = "feature"
    UI = "ui"


class SystemConfig(BaseModel, TimestampMixin, StatusMixin, MetadataMixin):
    """系统配置模型"""

    # 配置信息
    key = fields.CharField(max_length=100, unique=True, description="配置键", index=True)
    # 临时使用 TextField 来避免 JSON 解析问题，后续可以通过迁移改为 JSONField
    value = fields.TextField(description="配置值")
    config_type = fields.CharEnumField(ConfigType, description="配置类型", index=True)

    # 描述信息
    name = fields.CharField(max_length=100, description="配置名称")
    description = fields.TextField(null=True, description="配置描述")

    # 验证规则 - 临时使用 TextField
    validation_rules = fields.TextField(default="{}", description="验证规则JSON")
    default_value = fields.TextField(null=True, description="默认值JSON")

    # 权限控制
    is_public = fields.BooleanField(default=False, description="是否公开")
    is_readonly = fields.BooleanField(default=False, description="是否只读")

    # 版本控制
    version = fields.IntField(default=1, description="版本号")
    
    class Meta:
        table = "system_configs"
        indexes = [
            ["key"],
            ["config_type"],
            ["is_public"],
            ["status"],
        ]
    
    def get_value(self, default: Any = None) -> Any:
        """获取配置值"""
        if self.value is None:
            return default

        # 尝试解析 JSON，如果失败则返回原始字符串
        try:
            import json
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value

    def set_value(self, value: Any):
        """设置配置值"""
        import json
        if isinstance(value, str):
            self.value = value
        else:
            self.value = json.dumps(value, ensure_ascii=False)
        self.version += 1
    
    def validate_value(self, value: Any) -> bool:
        """验证配置值"""
        # 解析验证规则
        try:
            import json
            if isinstance(self.validation_rules, str):
                rules = json.loads(self.validation_rules) if self.validation_rules else {}
            else:
                rules = self.validation_rules or {}
        except (json.JSONDecodeError, TypeError):
            return True

        if not rules:
            return True

        # 检查类型
        if "type" in rules:
            expected_type = rules["type"]
            if expected_type == "string" and not isinstance(value, str):
                return False
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False
            elif expected_type == "array" and not isinstance(value, list):
                return False
            elif expected_type == "object" and not isinstance(value, dict):
                return False

        # 检查范围
        if "min" in rules and value < rules["min"]:
            return False
        if "max" in rules and value > rules["max"]:
            return False

        # 检查枚举值
        if "enum" in rules and value not in rules["enum"]:
            return False

        return True


class ActionType(str, Enum):
    """操作类型枚举"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SEARCH = "search"
    CHAT = "chat"


class ResultType(str, Enum):
    """结果类型枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"


class AuditLog(BaseModel, TimestampMixin, MetadataMixin):
    """审计日志模型"""
    
    # 操作信息
    action_type = fields.CharEnumField(ActionType, description="操作类型", index=True)
    resource_type = fields.CharField(max_length=50, description="资源类型", index=True)
    resource_id = fields.CharField(max_length=100, null=True, description="资源ID")
    
    # 用户信息
    user_id = fields.IntField(null=True, description="用户ID", index=True)
    username = fields.CharField(max_length=50, null=True, description="用户名")
    
    # 请求信息
    ip_address = fields.CharField(max_length=45, description="IP地址", index=True)
    user_agent = fields.TextField(null=True, description="用户代理")
    request_id = fields.CharField(max_length=100, null=True, description="请求ID")
    
    # 操作详情
    action_description = fields.TextField(description="操作描述")
    request_data = fields.JSONField(default=dict, description="请求数据")
    response_data = fields.JSONField(default=dict, description="响应数据")
    
    # 结果信息
    result_type = fields.CharEnumField(ResultType, description="结果类型", index=True)
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 性能信息
    processing_time = fields.FloatField(null=True, description="处理时间(秒)")
    
    class Meta:
        table = "audit_logs"
        indexes = [
            ["user_id", "action_type"],
            ["resource_type", "resource_id"],
            ["ip_address"],
            ["result_type"],
            ["created_at"],
        ]
    
    @classmethod
    async def log_action(
        cls,
        action_type: str,
        resource_type: str,
        description: str,
        user_id: int = None,
        username: str = None,
        resource_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None,
        request_data: Dict = None,
        response_data: Dict = None,
        result_type: str = ResultType.SUCCESS,
        error_message: str = None,
        processing_time: float = None,
        metadata: Dict = None,
    ) -> "AuditLog":
        """记录操作日志"""
        return await cls.create(
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            action_description=description,
            request_data=request_data or {},
            response_data=response_data or {},
            result_type=result_type,
            error_message=error_message,
            processing_time=processing_time,
            metadata=metadata or {},
        )


class MetricType(str, Enum):
    """指标类型枚举"""
    PERFORMANCE = "performance"
    USAGE = "usage"
    ERROR = "error"
    BUSINESS = "business"


class SystemMetrics(BaseModel, TimestampMixin):
    """系统指标模型"""
    
    # 指标信息
    metric_name = fields.CharField(max_length=100, description="指标名称", index=True)
    metric_type = fields.CharEnumField(MetricType, description="指标类型", index=True)
    metric_value = fields.FloatField(description="指标值")
    metric_unit = fields.CharField(max_length=20, null=True, description="指标单位")
    
    # 维度信息
    dimensions = fields.JSONField(default=dict, description="维度信息")
    
    # 时间信息
    timestamp = fields.DatetimeField(description="时间戳", index=True)
    
    class Meta:
        table = "system_metrics"
        indexes = [
            ["metric_name", "timestamp"],
            ["metric_type", "timestamp"],
            ["timestamp"],
        ]
    
    @classmethod
    async def record_metric(
        cls,
        name: str,
        value: float,
        metric_type: str = MetricType.PERFORMANCE.value,
        unit: str = None,
        dimensions: Dict = None,
        timestamp: datetime = None,
    ) -> "SystemMetrics":
        """记录指标"""
        return await cls.create(
            metric_name=name,
            metric_type=metric_type,
            metric_value=value,
            metric_unit=unit,
            dimensions=dimensions or {},
            timestamp=timestamp or datetime.now(),
        )


class NotificationType(str, Enum):
    """通知类型枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationLevel(str, Enum):
    """通知级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SystemNotification(BaseModel, TimestampMixin, StatusMixin):
    """系统通知模型"""
    
    # 通知内容
    title = fields.CharField(max_length=200, description="通知标题")
    content = fields.TextField(description="通知内容")
    notification_type = fields.CharEnumField(NotificationType, description="通知类型", index=True)
    level = fields.CharEnumField(NotificationLevel, description="通知级别", index=True)
    
    # 目标用户
    target_user_id = fields.IntField(null=True, description="目标用户ID", index=True)
    target_role = fields.CharField(max_length=50, null=True, description="目标角色")
    is_global = fields.BooleanField(default=False, description="是否全局通知")
    
    # 状态信息
    is_read = fields.BooleanField(default=False, description="是否已读")
    read_at = fields.DatetimeField(null=True, description="阅读时间")
    
    # 过期信息
    expires_at = fields.DatetimeField(null=True, description="过期时间")
    
    # 操作信息
    action_url = fields.CharField(max_length=500, null=True, description="操作链接")
    action_text = fields.CharField(max_length=50, null=True, description="操作文本")
    
    class Meta:
        table = "system_notifications"
        indexes = [
            ["target_user_id", "is_read"],
            ["notification_type", "level"],
            ["is_global", "status"],
            ["expires_at"],
            ["created_at"],
        ]
    
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    async def mark_as_read(self, user_id: int = None):
        """标记为已读"""
        if not self.is_read and (not self.target_user_id or self.target_user_id == user_id):
            self.is_read = True
            self.read_at = datetime.now()
            await self.save(update_fields=["is_read", "read_at"])
