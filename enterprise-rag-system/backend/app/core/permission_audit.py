"""
权限审计日志模块
"""

import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
import json

from loguru import logger
from fastapi import Request

from app.core.error_monitoring import get_error_monitor


class AuditAction(str, Enum):
    """审计动作类型"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    
    # 权限检查
    PERMISSION_CHECK = "permission_check"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHECK = "role_check"
    ROLE_DENIED = "role_denied"
    
    # 资源访问
    RESOURCE_ACCESS = "resource_access"
    RESOURCE_DENIED = "resource_denied"
    RESOURCE_CREATE = "resource_create"
    RESOURCE_UPDATE = "resource_update"
    RESOURCE_DELETE = "resource_delete"
    
    # 权限管理
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_UNASSIGN = "role_unassign"
    
    # 系统管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"


class AuditLevel(str, Enum):
    """审计级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """审计日志记录"""
    timestamp: float
    user_id: Optional[int]
    username: Optional[str]
    action: AuditAction
    level: AuditLevel
    resource_type: Optional[str]
    resource_id: Optional[str]
    permission_code: Optional[str]
    role_code: Optional[str]
    success: bool
    message: str
    details: Dict[str, Any]
    client_ip: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    session_id: Optional[str]


class PermissionAuditor:
    """权限审计器"""
    
    def __init__(self, max_logs: int = 10000):
        self.max_logs = max_logs
        self.audit_logs: List[AuditLog] = []
        
        # 统计信息
        self.stats = {
            "total_logs": 0,
            "success_count": 0,
            "failure_count": 0,
            "by_action": {},
            "by_level": {},
            "by_user": {},
        }
    
    def _extract_request_info(self, request: Optional[Request] = None) -> Dict[str, Any]:
        """提取请求信息"""
        if not request:
            return {
                "client_ip": None,
                "user_agent": None,
                "request_id": None,
            }
        
        return {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": getattr(request.state, "request_id", None),
        }
    
    def log_audit(
        self,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        permission_code: Optional[str] = None,
        role_code: Optional[str] = None,
        success: bool = True,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        session_id: Optional[str] = None,
    ):
        """记录审计日志"""
        current_time = time.time()
        request_info = self._extract_request_info(request)
        
        audit_log = AuditLog(
            timestamp=current_time,
            user_id=user_id,
            username=username,
            action=action,
            level=level,
            resource_type=resource_type,
            resource_id=resource_id,
            permission_code=permission_code,
            role_code=role_code,
            success=success,
            message=message,
            details=details or {},
            client_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"],
            request_id=request_info["request_id"],
            session_id=session_id,
        )
        
        # 添加到内存日志
        self.audit_logs.append(audit_log)
        
        # 限制内存中的日志数量
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs.pop(0)
        
        # 更新统计信息
        self._update_stats(audit_log)
        
        # 记录到结构化日志
        self._log_to_structured_logger(audit_log)
        
        # 记录到错误监控系统（如果是失败的操作）
        if not success and level in [AuditLevel.ERROR, AuditLevel.CRITICAL]:
            self._log_to_error_monitor(audit_log)
    
    def _update_stats(self, audit_log: AuditLog):
        """更新统计信息"""
        self.stats["total_logs"] += 1
        
        if audit_log.success:
            self.stats["success_count"] += 1
        else:
            self.stats["failure_count"] += 1
        
        # 按动作统计
        action_key = audit_log.action.value
        self.stats["by_action"][action_key] = self.stats["by_action"].get(action_key, 0) + 1
        
        # 按级别统计
        level_key = audit_log.level.value
        self.stats["by_level"][level_key] = self.stats["by_level"].get(level_key, 0) + 1
        
        # 按用户统计
        if audit_log.user_id:
            user_key = str(audit_log.user_id)
            self.stats["by_user"][user_key] = self.stats["by_user"].get(user_key, 0) + 1
    
    def _log_to_structured_logger(self, audit_log: AuditLog):
        """记录到结构化日志系统"""
        log_data = asdict(audit_log)
        
        # 选择日志级别
        if audit_log.level == AuditLevel.INFO:
            logger.info(f"权限审计: {audit_log.action.value}", extra=log_data)
        elif audit_log.level == AuditLevel.WARNING:
            logger.warning(f"权限审计: {audit_log.action.value}", extra=log_data)
        elif audit_log.level == AuditLevel.ERROR:
            logger.error(f"权限审计: {audit_log.action.value}", extra=log_data)
        elif audit_log.level == AuditLevel.CRITICAL:
            logger.critical(f"权限审计: {audit_log.action.value}", extra=log_data)
    
    def _log_to_error_monitor(self, audit_log: AuditLog):
        """记录到错误监控系统"""
        error_monitor = get_error_monitor()
        
        # 映射审计动作到错误码
        error_code_mapping = {
            AuditAction.LOGIN_FAILED: "AUTH_1001",
            AuditAction.PERMISSION_DENIED: "PERM_2001",
            AuditAction.ROLE_DENIED: "PERM_2004",
            AuditAction.RESOURCE_DENIED: "PERM_2002",
        }
        
        error_code = error_code_mapping.get(audit_log.action, "SYS_9001")
        
        error_monitor.record_error(
            error_code=error_code,
            path=f"/audit/{audit_log.action.value}",
            method="AUDIT",
            user_agent=audit_log.user_agent,
            client_ip=audit_log.client_ip,
            request_id=audit_log.request_id,
        )
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        level: Optional[AuditLevel] = None,
        success: Optional[bool] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取审计日志"""
        filtered_logs = self.audit_logs
        
        # 应用过滤条件
        if user_id is not None:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        if action is not None:
            filtered_logs = [log for log in filtered_logs if log.action == action]
        
        if level is not None:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if success is not None:
            filtered_logs = [log for log in filtered_logs if log.success == success]
        
        if start_time is not None:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        
        if end_time is not None:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        # 按时间倒序排序并限制数量
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_logs[:limit]
    
    def get_user_activity(self, user_id: int, hours: int = 24) -> List[AuditLog]:
        """获取用户活动日志"""
        start_time = time.time() - (hours * 3600)
        return self.get_audit_logs(
            user_id=user_id,
            start_time=start_time,
            limit=1000
        )
    
    def get_failed_attempts(self, hours: int = 24) -> List[AuditLog]:
        """获取失败的操作尝试"""
        start_time = time.time() - (hours * 3600)
        return self.get_audit_logs(
            success=False,
            start_time=start_time,
            limit=1000
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取审计统计信息"""
        return {
            "total_logs": self.stats["total_logs"],
            "success_count": self.stats["success_count"],
            "failure_count": self.stats["failure_count"],
            "success_rate": (
                self.stats["success_count"] / self.stats["total_logs"]
                if self.stats["total_logs"] > 0 else 0
            ),
            "by_action": self.stats["by_action"],
            "by_level": self.stats["by_level"],
            "by_user": self.stats["by_user"],
            "memory_usage": {
                "current_logs": len(self.audit_logs),
                "max_logs": self.max_logs,
            }
        }
    
    def clear_old_logs(self, hours: int = 168):  # 默认保留7天
        """清理旧的审计日志"""
        cutoff_time = time.time() - (hours * 3600)
        
        original_count = len(self.audit_logs)
        self.audit_logs = [
            log for log in self.audit_logs
            if log.timestamp >= cutoff_time
        ]
        
        cleared_count = original_count - len(self.audit_logs)
        logger.info(f"清理了 {cleared_count} 条过期审计日志")
        
        return cleared_count


# 全局审计器实例
permission_auditor = PermissionAuditor()


def get_permission_auditor() -> PermissionAuditor:
    """获取权限审计器实例"""
    return permission_auditor


# 便捷的审计日志记录函数
def audit_login(user_id: int, username: str, success: bool, request: Optional[Request] = None, details: Optional[Dict] = None):
    """记录登录审计"""
    auditor = get_permission_auditor()
    action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
    level = AuditLevel.INFO if success else AuditLevel.WARNING
    
    auditor.log_audit(
        action=action,
        level=level,
        user_id=user_id,
        username=username,
        success=success,
        message=f"用户 {username} {'登录成功' if success else '登录失败'}",
        details=details,
        request=request
    )


def audit_permission_check(
    user_id: int,
    username: str,
    permission_code: str,
    success: bool,
    request: Optional[Request] = None,
    details: Optional[Dict] = None
):
    """记录权限检查审计"""
    auditor = get_permission_auditor()
    action = AuditAction.PERMISSION_CHECK if success else AuditAction.PERMISSION_DENIED
    level = AuditLevel.INFO if success else AuditLevel.WARNING
    
    auditor.log_audit(
        action=action,
        level=level,
        user_id=user_id,
        username=username,
        permission_code=permission_code,
        success=success,
        message=f"用户 {username} 权限检查 {permission_code} {'通过' if success else '失败'}",
        details=details,
        request=request
    )


def audit_resource_access(
    user_id: int,
    username: str,
    resource_type: str,
    resource_id: str,
    action: str,
    success: bool,
    request: Optional[Request] = None,
    details: Optional[Dict] = None
):
    """记录资源访问审计"""
    auditor = get_permission_auditor()
    audit_action = AuditAction.RESOURCE_ACCESS if success else AuditAction.RESOURCE_DENIED
    level = AuditLevel.INFO if success else AuditLevel.WARNING
    
    auditor.log_audit(
        action=audit_action,
        level=level,
        user_id=user_id,
        username=username,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        message=f"用户 {username} {action} {resource_type}:{resource_id} {'成功' if success else '失败'}",
        details=details,
        request=request
    )
