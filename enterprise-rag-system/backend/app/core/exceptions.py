"""
异常处理模块
"""

import time
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from tortoise.exceptions import DoesNotExist, IntegrityError

from .error_codes import ErrorCode, ErrorMessages, create_error_response


class BusinessException(Exception):
    """业务异常基类"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = None,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh",
    ):
        self.error_code = error_code
        self.message = message or ErrorMessages.get_message(error_code, language)
        self.status_code = status_code or self._get_default_status_code(error_code)
        self.details = details or {}
        self.language = language
        super().__init__(self.message)

    def _get_default_status_code(self, error_code: ErrorCode) -> int:
        """根据错误码获取默认HTTP状态码"""
        if error_code.value.startswith("AUTH_"):
            return status.HTTP_401_UNAUTHORIZED
        elif error_code.value.startswith("PERM_"):
            return status.HTTP_403_FORBIDDEN
        elif error_code.value.startswith("RES_3001"):  # NOT_FOUND
            return status.HTTP_404_NOT_FOUND
        elif error_code.value.startswith("RES_3002"):  # ALREADY_EXISTS
            return status.HTTP_409_CONFLICT
        elif error_code.value.startswith("VAL_"):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        elif error_code.value.startswith("SYS_9003"):  # RATE_LIMIT
            return status.HTTP_429_TOO_MANY_REQUESTS
        elif error_code.value.startswith("EXT_") or error_code.value.startswith("DB_"):
            return status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return create_error_response(
            self.error_code,
            self.message,
            self.details,
            self.language
        )


class AuthenticationException(BusinessException):
    """认证异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class AuthorizationException(BusinessException):
    """授权异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.PERMISSION_DENIED,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class NotFoundException(BusinessException):
    """资源未找到异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class ValidationException(BusinessException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class DatabaseException(BusinessException):
    """数据库异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.DATABASE_CONNECTION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class ExternalServiceException(BusinessException):
    """外部服务异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class AIServiceException(BusinessException):
    """AI服务异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.LLM_SERVICE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class VectorDatabaseException(BusinessException):
    """向量数据库异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.VECTOR_DATABASE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class GraphDatabaseException(BusinessException):
    """图数据库异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.GRAPH_DATABASE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class DocumentProcessingException(BusinessException):
    """文档处理异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.PROCESSING_FAILED,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class RateLimitException(BusinessException):
    """限流异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class AgentException(BusinessException):
    """Agent异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.AGENT_COLLABORATION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class WorkflowException(BusinessException):
    """工作流异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.WORKFLOW_ERROR,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class SearchException(BusinessException):
    """搜索异常"""

    def __init__(
        self,
        message: str = None,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None,
        language: str = "zh"
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            language=language,
        )


class QAException(BusinessException):
    """问答异常"""

    def __init__(self, message: str = "问答处理失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="QA_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class AnalyticsException(BusinessException):
    """分析异常"""

    def __init__(self, message: str = "分析处理失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ANALYTICS_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class CacheException(BusinessException):
    """缓存异常"""

    def __init__(self, message: str = "缓存操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class TenantException(BusinessException):
    """租户异常"""

    def __init__(self, message: str = "租户操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="TENANT_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class NotificationException(BusinessException):
    """通知异常"""

    def __init__(self, message: str = "通知发送失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOTIFICATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class BackupException(BusinessException):
    """备份异常"""

    def __init__(self, message: str = "备份操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="BACKUP_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ConfigException(BusinessException):
    """配置异常"""

    def __init__(self, message: str = "配置操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class I18nException(BusinessException):
    """国际化异常"""

    def __init__(self, message: str = "国际化操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="I18N_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class PluginException(BusinessException):
    """插件异常"""

    def __init__(self, message: str = "插件操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="PLUGIN_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class SecurityException(BusinessException):
    """安全异常"""

    def __init__(self, message: str = "安全检查失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="SECURITY_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )





async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """业务异常处理器"""

    request_id = getattr(request.state, "request_id", None)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 记录错误到监控系统
    from .error_monitoring import get_error_monitor
    error_monitor = get_error_monitor()
    error_monitor.record_error(
        error_code=exc.error_code.value,
        path=request.url.path,
        method=request.method,
        user_agent=user_agent,
        client_ip=client_ip,
        request_id=request_id,
    )

    # 结构化日志记录
    logger.error(
        f"业务异常: {exc.error_code.value} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code.value,
            "error_category": exc.error_code.value.split("_")[0],
            "status_code": exc.status_code,
            "details": exc.details,
            "user_agent": user_agent,
            "client_ip": client_ip,
            "language": exc.language,
        }
    )

    # 获取响应内容
    response_content = exc.to_dict()
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """数据验证异常处理器"""

    request_id = getattr(request.state, "request_id", None)

    # 处理验证错误详情
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    # 结构化日志记录
    logger.error(
        f"数据验证异常: {len(validation_errors)} 个字段验证失败",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "validation_errors": validation_errors,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
    )

    response_content = create_error_response(
        ErrorCode.VALIDATION_ERROR,
        details={"validation_errors": validation_errors}
    )
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    
    logger.error(
        f"HTTP异常: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            },
            "request_id": getattr(request.state, "request_id", None),
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""

    request_id = getattr(request.state, "request_id", None)

    # 结构化日志记录
    logger.exception(
        f"未处理异常: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
    )

    response_content = create_error_response(
        ErrorCode.INTERNAL_SERVER_ERROR,
        details={"exception_type": type(exc).__name__}
    )
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""

    request_id = getattr(request.state, "request_id", None)

    # 根据HTTP状态码映射错误码
    error_code_mapping = {
        401: ErrorCode.TOKEN_INVALID,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.RESOURCE_ALREADY_EXISTS,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = error_code_mapping.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    logger.error(
        f"HTTP异常: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": error_code.value,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
    )

    response_content = create_error_response(
        error_code,
        message=str(exc.detail),
        details={"http_status": exc.status_code}
    )
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def tortoise_does_not_exist_handler(request: Request, exc: DoesNotExist) -> JSONResponse:
    """Tortoise DoesNotExist异常处理器"""

    request_id = getattr(request.state, "request_id", None)

    logger.error(
        f"资源不存在: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": ErrorCode.RESOURCE_NOT_FOUND.value,
            "exception": str(exc),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
    )

    response_content = create_error_response(
        ErrorCode.RESOURCE_NOT_FOUND,
        details={"model": str(exc)}
    )
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response_content
    )


async def tortoise_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Tortoise IntegrityError异常处理器"""

    request_id = getattr(request.state, "request_id", None)

    logger.error(
        f"数据完整性错误: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": ErrorCode.DATABASE_CONSTRAINT_ERROR.value,
            "exception": str(exc),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
    )

    # 判断是否为重复键错误
    error_message = str(exc).lower()
    if "duplicate" in error_message or "unique" in error_message:
        error_code = ErrorCode.DUPLICATE_VALUE
        status_code = status.HTTP_409_CONFLICT
    else:
        error_code = ErrorCode.DATABASE_CONSTRAINT_ERROR
        status_code = status.HTTP_400_BAD_REQUEST

    response_content = create_error_response(
        error_code,
        details={"constraint_error": str(exc)}
    )
    response_content["request_id"] = request_id
    response_content["timestamp"] = time.time()

    return JSONResponse(
        status_code=status_code,
        content=response_content
    )
