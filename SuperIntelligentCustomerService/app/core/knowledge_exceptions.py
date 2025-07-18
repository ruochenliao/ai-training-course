"""
知识库相关的异常定义
定义知识库系统中可能出现的各种异常类型
"""
from typing import Optional, Any, Dict


class KnowledgeBaseException(Exception):
    """知识库基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "KNOWLEDGE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class KnowledgeBaseNotFoundError(KnowledgeBaseException):
    """知识库不存在异常"""
    
    def __init__(self, kb_id: int):
        super().__init__(
            message=f"知识库不存在: {kb_id}",
            error_code="KB_NOT_FOUND",
            details={"knowledge_base_id": kb_id}
        )


class KnowledgeFileNotFoundError(KnowledgeBaseException):
    """知识文件不存在异常"""
    
    def __init__(self, file_id: int):
        super().__init__(
            message=f"知识文件不存在: {file_id}",
            error_code="FILE_NOT_FOUND",
            details={"file_id": file_id}
        )


class PermissionDeniedError(KnowledgeBaseException):
    """权限拒绝异常"""
    
    def __init__(self, resource: str, action: str, user_id: int):
        super().__init__(
            message=f"用户 {user_id} 无权限对 {resource} 执行 {action} 操作",
            error_code="PERMISSION_DENIED",
            details={
                "resource": resource,
                "action": action,
                "user_id": user_id
            }
        )


class FileProcessingError(KnowledgeBaseException):
    """文件处理异常"""
    
    def __init__(self, file_id: int, reason: str):
        super().__init__(
            message=f"文件处理失败: {reason}",
            error_code="FILE_PROCESSING_ERROR",
            details={
                "file_id": file_id,
                "reason": reason
            }
        )


class FileUploadError(KnowledgeBaseException):
    """文件上传异常"""
    
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"文件上传失败: {filename} - {reason}",
            error_code="FILE_UPLOAD_ERROR",
            details={
                "filename": filename,
                "reason": reason
            }
        )


class UnsupportedFileTypeError(KnowledgeBaseException):
    """不支持的文件类型异常"""
    
    def __init__(self, file_type: str, supported_types: list):
        super().__init__(
            message=f"不支持的文件类型: {file_type}，支持的类型: {', '.join(supported_types)}",
            error_code="UNSUPPORTED_FILE_TYPE",
            details={
                "file_type": file_type,
                "supported_types": supported_types
            }
        )


class FileSizeExceededError(KnowledgeBaseException):
    """文件大小超限异常"""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"文件大小超过限制: {file_size} > {max_size} 字节",
            error_code="FILE_SIZE_EXCEEDED",
            details={
                "file_size": file_size,
                "max_size": max_size
            }
        )


class VectorSearchError(KnowledgeBaseException):
    """向量搜索异常"""
    
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"向量搜索失败: {reason}",
            error_code="VECTOR_SEARCH_ERROR",
            details={
                "query": query,
                "reason": reason
            }
        )


class BatchOperationError(KnowledgeBaseException):
    """批量操作异常"""
    
    def __init__(self, operation: str, failed_count: int, total_count: int, errors: list):
        super().__init__(
            message=f"批量{operation}操作部分失败: {failed_count}/{total_count}",
            error_code="BATCH_OPERATION_ERROR",
            details={
                "operation": operation,
                "failed_count": failed_count,
                "total_count": total_count,
                "errors": errors
            }
        )


class ConfigurationError(KnowledgeBaseException):
    """配置错误异常"""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"配置错误: {config_key} - {reason}",
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "reason": reason
            }
        )


class StorageError(KnowledgeBaseException):
    """存储异常"""
    
    def __init__(self, operation: str, path: str, reason: str):
        super().__init__(
            message=f"存储操作失败: {operation} {path} - {reason}",
            error_code="STORAGE_ERROR",
            details={
                "operation": operation,
                "path": path,
                "reason": reason
            }
        )


class DatabaseError(KnowledgeBaseException):
    """数据库异常"""
    
    def __init__(self, operation: str, table: str, reason: str):
        super().__init__(
            message=f"数据库操作失败: {operation} {table} - {reason}",
            error_code="DATABASE_ERROR",
            details={
                "operation": operation,
                "table": table,
                "reason": reason
            }
        )


class ValidationError(KnowledgeBaseException):
    """数据验证异常"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"数据验证失败: {field}={value} - {reason}",
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value),
                "reason": reason
            }
        )


class ResourceLimitError(KnowledgeBaseException):
    """资源限制异常"""
    
    def __init__(self, resource: str, current: int, limit: int):
        super().__init__(
            message=f"资源使用超过限制: {resource} {current}/{limit}",
            error_code="RESOURCE_LIMIT_ERROR",
            details={
                "resource": resource,
                "current": current,
                "limit": limit
            }
        )


class ServiceUnavailableError(KnowledgeBaseException):
    """服务不可用异常"""
    
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"服务不可用: {service} - {reason}",
            error_code="SERVICE_UNAVAILABLE",
            details={
                "service": service,
                "reason": reason
            }
        )


# 异常映射表，用于将异常转换为HTTP状态码
EXCEPTION_STATUS_MAP = {
    KnowledgeBaseNotFoundError: 404,
    KnowledgeFileNotFoundError: 404,
    PermissionDeniedError: 403,
    FileUploadError: 400,
    UnsupportedFileTypeError: 400,
    FileSizeExceededError: 400,
    ValidationError: 400,
    ResourceLimitError: 429,
    ConfigurationError: 500,
    StorageError: 500,
    DatabaseError: 500,
    FileProcessingError: 500,
    VectorSearchError: 500,
    BatchOperationError: 500,
    ServiceUnavailableError: 503,
    KnowledgeBaseException: 500,
}


def get_http_status_code(exception: Exception) -> int:
    """
    根据异常类型获取对应的HTTP状态码
    
    Args:
        exception: 异常实例
        
    Returns:
        HTTP状态码
    """
    for exc_type, status_code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exception, exc_type):
            return status_code
    return 500  # 默认返回500


def format_exception_response(exception: Exception) -> Dict[str, Any]:
    """
    格式化异常响应
    
    Args:
        exception: 异常实例
        
    Returns:
        格式化的异常响应
    """
    if isinstance(exception, KnowledgeBaseException):
        return {
            "success": False,
            "error": exception.to_dict(),
            "msg": exception.message
        }
    else:
        return {
            "success": False,
            "error": {
                "error_code": "UNKNOWN_ERROR",
                "message": str(exception),
                "details": {}
            },
            "msg": str(exception)
        }
