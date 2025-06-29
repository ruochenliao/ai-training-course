"""
核心模块 - 包含配置、数据库、安全等核心功能
"""

from .config import Settings, settings
from .database import init_db, close_db, create_initial_data
from .exceptions import (
    BusinessException, RateLimitException, DocumentProcessingException,
    ExternalServiceException, AIServiceException, VectorDatabaseException,
    GraphDatabaseException, AuthenticationException, AuthorizationException,
    NotFoundException, ValidationException, DatabaseException, AgentException,
    WorkflowException, SearchException,
    business_exception_handler, general_exception_handler, validation_exception_handler,
    http_exception_handler, tortoise_does_not_exist_handler, tortoise_integrity_error_handler
)
from .middleware import LoggingMiddleware, ProcessTimeMiddleware, RateLimitMiddleware
from .security import create_access_token, get_current_user, get_current_superuser, PermissionChecker, verify_password, get_password_hash
from .error_codes import ErrorCode, ErrorMessages, create_error_response
from .error_monitoring import ErrorMonitor, get_error_monitor
from .permission_cache import PermissionCache, get_permission_cache
from .permission_audit import PermissionAuditor, get_permission_auditor, audit_login, audit_permission_check, audit_resource_access
from .resource_permissions import (
    ResourcePermissionChecker, require_resource_access, BatchResourcePermissionChecker,
    require_knowledge_base_access, require_document_access, require_conversation_access,
    get_knowledge_base_filter, get_document_filter
)

__all__ = [
    "Settings",
    "settings",
    "init_db",
    "close_db",
    "create_initial_data",
    "BusinessException",
    "RateLimitException",
    "DocumentProcessingException",
    "ExternalServiceException",
    "AIServiceException",
    "VectorDatabaseException",
    "GraphDatabaseException",
    "AuthenticationException",
    "AuthorizationException",
    "NotFoundException",
    "ValidationException",
    "DatabaseException",
    "AgentException",
    "WorkflowException",
    "SearchException",
    "business_exception_handler",
    "general_exception_handler",
    "validation_exception_handler",
    "http_exception_handler",
    "tortoise_does_not_exist_handler",
    "tortoise_integrity_error_handler",
    "LoggingMiddleware",
    "ProcessTimeMiddleware",
    "RateLimitMiddleware",
    "create_access_token",
    "get_current_user",
    "get_current_superuser",
    "PermissionChecker",
    "verify_password",
    "get_password_hash",
    "ErrorCode",
    "ErrorMessages",
    "create_error_response",
    "ErrorMonitor",
    "get_error_monitor",
    "PermissionCache",
    "get_permission_cache",
    "PermissionAuditor",
    "get_permission_auditor",
    "audit_login",
    "audit_permission_check",
    "audit_resource_access",
    "ResourcePermissionChecker",
    "require_resource_access",
    "BatchResourcePermissionChecker",
    "require_knowledge_base_access",
    "require_document_access",
    "require_conversation_access",
    "get_knowledge_base_filter",
    "get_document_filter",
]
