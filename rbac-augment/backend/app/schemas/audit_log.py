"""
审计日志相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ASSIGN = "assign"
    REVOKE = "revoke"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"
    DOWNLOAD = "download"


class AuditLevel(str, Enum):
    """审计级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """审计状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class AuditLogBase(BaseModel):
    """审计日志基础模型"""
    action: AuditAction = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型", max_length=50)
    resource_id: Optional[str] = Field(None, description="资源ID", max_length=100)
    resource_name: Optional[str] = Field(None, description="资源名称", max_length=200)
    description: str = Field(..., description="操作描述")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    status: AuditStatus = Field(AuditStatus.SUCCESS, description="操作状态")
    level: AuditLevel = Field(AuditLevel.MEDIUM, description="审计级别")


class AuditLogCreate(AuditLogBase):
    """创建审计日志"""
    user_id: Optional[int] = Field(None, description="操作用户ID")
    username: Optional[str] = Field(None, description="操作用户名", max_length=50)
    user_ip: Optional[str] = Field(None, description="用户IP地址", max_length=45)
    user_agent: Optional[str] = Field(None, description="用户代理")
    request_method: Optional[str] = Field(None, description="请求方法", max_length=10)
    request_url: Optional[str] = Field(None, description="请求URL")
    request_params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    response_status: Optional[int] = Field(None, description="响应状态码")
    response_time: Optional[int] = Field(None, description="响应时间(毫秒)")
    old_values: Optional[Dict[str, Any]] = Field(None, description="变更前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="变更后的值")


class AuditLogResponse(AuditLogBase):
    """审计日志响应"""
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="操作用户ID")
    username: Optional[str] = Field(None, description="操作用户名")
    user_ip: Optional[str] = Field(None, description="用户IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    request_method: Optional[str] = Field(None, description="请求方法")
    request_url: Optional[str] = Field(None, description="请求URL")
    request_params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    response_status: Optional[int] = Field(None, description="响应状态码")
    response_time: Optional[int] = Field(None, description="响应时间(毫秒)")
    old_values: Optional[Dict[str, Any]] = Field(None, description="变更前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="变更后的值")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class AuditLogListItem(BaseModel):
    """审计日志列表项"""
    id: int = Field(..., description="日志ID")
    action: AuditAction = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_name: Optional[str] = Field(None, description="资源名称")
    description: str = Field(..., description="操作描述")
    status: AuditStatus = Field(..., description="操作状态")
    level: AuditLevel = Field(..., description="审计级别")
    username: Optional[str] = Field(None, description="操作用户名")
    user_ip: Optional[str] = Field(None, description="用户IP地址")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    items: List[AuditLogListItem] = Field(..., description="日志列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class AuditLogSearchParams(BaseModel):
    """审计日志搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词搜索")
    action: Optional[AuditAction] = Field(None, description="操作类型")
    resource_type: Optional[str] = Field(None, description="资源类型")
    level: Optional[AuditLevel] = Field(None, description="审计级别")
    status: Optional[AuditStatus] = Field(None, description="操作状态")
    user_id: Optional[int] = Field(None, description="操作用户ID")
    username: Optional[str] = Field(None, description="操作用户名")
    user_ip: Optional[str] = Field(None, description="用户IP地址")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class AuditLogStatistics(BaseModel):
    """审计日志统计"""
    total_logs: int = Field(..., description="总日志数")
    today_logs: int = Field(..., description="今日日志数")
    success_logs: int = Field(..., description="成功日志数")
    failed_logs: int = Field(..., description="失败日志数")
    logs_by_action: Dict[str, int] = Field(..., description="按操作类型统计")
    logs_by_level: Dict[str, int] = Field(..., description="按级别统计")
    logs_by_resource: Dict[str, int] = Field(..., description="按资源类型统计")
    top_users: List[Dict[str, Any]] = Field(..., description="活跃用户TOP10")
    recent_critical: List[AuditLogListItem] = Field(..., description="最近的关键操作")


class AuditLogExportRequest(BaseModel):
    """审计日志导出请求"""
    search_params: Optional[AuditLogSearchParams] = Field(None, description="搜索条件")
    export_format: str = Field("excel", description="导出格式", pattern="^(excel|csv|json)$")
    include_details: bool = Field(False, description="是否包含详细信息")


class AuditLogExportResponse(BaseModel):
    """审计日志导出响应"""
    file_url: str = Field(..., description="文件下载URL")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    export_count: int = Field(..., description="导出记录数")


class UserActivitySummary(BaseModel):
    """用户活动摘要"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    total_actions: int = Field(..., description="总操作数")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    last_action: Optional[datetime] = Field(None, description="最后操作时间")
    actions_by_type: Dict[str, int] = Field(..., description="按操作类型统计")
    risk_score: float = Field(..., description="风险评分")


class SystemActivitySummary(BaseModel):
    """系统活动摘要"""
    date: datetime = Field(..., description="日期")
    total_actions: int = Field(..., description="总操作数")
    unique_users: int = Field(..., description="活跃用户数")
    failed_actions: int = Field(..., description="失败操作数")
    critical_actions: int = Field(..., description="关键操作数")
    peak_hour: int = Field(..., description="高峰时段")


class AuditLogBatchDeleteRequest(BaseModel):
    """审计日志批量删除请求"""
    ids: List[int] = Field(..., description="日志ID列表")
    confirm: bool = Field(False, description="确认删除")


class AuditLogBatchDeleteResponse(BaseModel):
    """审计日志批量删除响应"""
    deleted_count: int = Field(..., description="删除数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class AuditLogCleanupRequest(BaseModel):
    """审计日志清理请求"""
    days_to_keep: int = Field(..., description="保留天数", ge=1, le=3650)
    level_filter: Optional[List[AuditLevel]] = Field(None, description="级别过滤")
    dry_run: bool = Field(True, description="试运行")


class AuditLogCleanupResponse(BaseModel):
    """审计日志清理响应"""
    total_logs: int = Field(..., description="总日志数")
    logs_to_delete: int = Field(..., description="待删除日志数")
    deleted_count: int = Field(0, description="已删除数量")
    freed_space: int = Field(0, description="释放空间(字节)")
    dry_run: bool = Field(..., description="是否为试运行")


class AuditLogArchiveRequest(BaseModel):
    """审计日志归档请求"""
    days_to_archive: int = Field(..., description="归档天数", ge=30, le=3650)
    archive_format: str = Field("json", description="归档格式", pattern="^(json|csv)$")
    compress: bool = Field(True, description="是否压缩")


class AuditLogArchiveResponse(BaseModel):
    """审计日志归档响应"""
    archive_file: str = Field(..., description="归档文件路径")
    archived_count: int = Field(..., description="归档记录数")
    file_size: int = Field(..., description="文件大小(字节)")
    start_date: datetime = Field(..., description="归档开始日期")
    end_date: datetime = Field(..., description="归档结束日期")
