"""
错误码标准化模块
"""

from enum import Enum
from typing import Dict, Any


class ErrorCode(str, Enum):
    """标准化错误码"""
    
    # 认证相关错误 (AUTH_1xxx)
    INVALID_CREDENTIALS = "AUTH_1001"
    TOKEN_EXPIRED = "AUTH_1002"
    TOKEN_INVALID = "AUTH_1003"
    ACCOUNT_LOCKED = "AUTH_1004"
    ACCOUNT_DISABLED = "AUTH_1005"
    PASSWORD_EXPIRED = "AUTH_1006"
    LOGIN_ATTEMPTS_EXCEEDED = "AUTH_1007"
    
    # 权限相关错误 (PERM_2xxx)
    PERMISSION_DENIED = "PERM_2001"
    RESOURCE_NOT_OWNED = "PERM_2002"
    INSUFFICIENT_PRIVILEGES = "PERM_2003"
    ROLE_NOT_ASSIGNED = "PERM_2004"
    DEPARTMENT_ACCESS_DENIED = "PERM_2005"
    
    # 资源相关错误 (RES_3xxx)
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"
    RESOURCE_LOCKED = "RES_3004"
    RESOURCE_DELETED = "RES_3005"
    RESOURCE_EXPIRED = "RES_3006"
    
    # 业务逻辑错误 (BIZ_4xxx)
    INVALID_FILE_FORMAT = "BIZ_4001"
    FILE_TOO_LARGE = "BIZ_4002"
    PROCESSING_FAILED = "BIZ_4003"
    INVALID_OPERATION = "BIZ_4004"
    BUSINESS_RULE_VIOLATION = "BIZ_4005"
    WORKFLOW_ERROR = "BIZ_4006"
    
    # 数据验证错误 (VAL_5xxx)
    VALIDATION_ERROR = "VAL_5001"
    REQUIRED_FIELD_MISSING = "VAL_5002"
    INVALID_FORMAT = "VAL_5003"
    VALUE_OUT_OF_RANGE = "VAL_5004"
    DUPLICATE_VALUE = "VAL_5005"
    INVALID_REFERENCE = "VAL_5006"
    
    # 外部服务错误 (EXT_6xxx)
    EXTERNAL_SERVICE_UNAVAILABLE = "EXT_6001"
    EXTERNAL_API_ERROR = "EXT_6002"
    TIMEOUT_ERROR = "EXT_6003"
    NETWORK_ERROR = "EXT_6004"
    SERVICE_DEGRADED = "EXT_6005"
    
    # AI服务错误 (AI_7xxx)
    LLM_SERVICE_ERROR = "AI_7001"
    EMBEDDING_SERVICE_ERROR = "AI_7002"
    RERANKER_SERVICE_ERROR = "AI_7003"
    AGENT_COLLABORATION_ERROR = "AI_7004"
    MODEL_LOADING_ERROR = "AI_7005"
    INFERENCE_ERROR = "AI_7006"
    
    # 数据库错误 (DB_8xxx)
    DATABASE_CONNECTION_ERROR = "DB_8001"
    DATABASE_QUERY_ERROR = "DB_8002"
    DATABASE_CONSTRAINT_ERROR = "DB_8003"
    DATABASE_TIMEOUT = "DB_8004"
    VECTOR_DATABASE_ERROR = "DB_8005"
    GRAPH_DATABASE_ERROR = "DB_8006"
    
    # 系统错误 (SYS_9xxx)
    INTERNAL_SERVER_ERROR = "SYS_9001"
    SERVICE_UNAVAILABLE = "SYS_9002"
    RATE_LIMIT_EXCEEDED = "SYS_9003"
    MAINTENANCE_MODE = "SYS_9004"
    CONFIGURATION_ERROR = "SYS_9005"
    MEMORY_ERROR = "SYS_9006"


class ErrorMessages:
    """错误消息映射"""
    
    # 中文错误消息
    MESSAGES_ZH = {
        # 认证相关
        ErrorCode.INVALID_CREDENTIALS: "用户名或密码错误",
        ErrorCode.TOKEN_EXPIRED: "登录已过期，请重新登录",
        ErrorCode.TOKEN_INVALID: "无效的访问令牌",
        ErrorCode.ACCOUNT_LOCKED: "账户已被锁定",
        ErrorCode.ACCOUNT_DISABLED: "账户已被禁用",
        ErrorCode.PASSWORD_EXPIRED: "密码已过期，请修改密码",
        ErrorCode.LOGIN_ATTEMPTS_EXCEEDED: "登录尝试次数过多，请稍后再试",
        
        # 权限相关
        ErrorCode.PERMISSION_DENIED: "权限不足，无法执行此操作",
        ErrorCode.RESOURCE_NOT_OWNED: "您没有访问此资源的权限",
        ErrorCode.INSUFFICIENT_PRIVILEGES: "权限级别不足",
        ErrorCode.ROLE_NOT_ASSIGNED: "未分配相应角色",
        ErrorCode.DEPARTMENT_ACCESS_DENIED: "部门访问权限不足",
        
        # 资源相关
        ErrorCode.RESOURCE_NOT_FOUND: "请求的资源不存在",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "资源已存在",
        ErrorCode.RESOURCE_CONFLICT: "资源冲突",
        ErrorCode.RESOURCE_LOCKED: "资源已被锁定",
        ErrorCode.RESOURCE_DELETED: "资源已被删除",
        ErrorCode.RESOURCE_EXPIRED: "资源已过期",
        
        # 业务逻辑
        ErrorCode.INVALID_FILE_FORMAT: "不支持的文件格式",
        ErrorCode.FILE_TOO_LARGE: "文件大小超出限制",
        ErrorCode.PROCESSING_FAILED: "处理失败",
        ErrorCode.INVALID_OPERATION: "无效的操作",
        ErrorCode.BUSINESS_RULE_VIOLATION: "违反业务规则",
        ErrorCode.WORKFLOW_ERROR: "工作流程错误",
        
        # 数据验证
        ErrorCode.VALIDATION_ERROR: "数据验证失败",
        ErrorCode.REQUIRED_FIELD_MISSING: "必填字段缺失",
        ErrorCode.INVALID_FORMAT: "格式不正确",
        ErrorCode.VALUE_OUT_OF_RANGE: "值超出允许范围",
        ErrorCode.DUPLICATE_VALUE: "值重复",
        ErrorCode.INVALID_REFERENCE: "无效的引用",
        
        # 外部服务
        ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: "外部服务不可用",
        ErrorCode.EXTERNAL_API_ERROR: "外部API调用失败",
        ErrorCode.TIMEOUT_ERROR: "请求超时",
        ErrorCode.NETWORK_ERROR: "网络连接错误",
        ErrorCode.SERVICE_DEGRADED: "服务降级",
        
        # AI服务
        ErrorCode.LLM_SERVICE_ERROR: "大语言模型服务错误",
        ErrorCode.EMBEDDING_SERVICE_ERROR: "嵌入模型服务错误",
        ErrorCode.RERANKER_SERVICE_ERROR: "重排序服务错误",
        ErrorCode.AGENT_COLLABORATION_ERROR: "智能体协作错误",
        ErrorCode.MODEL_LOADING_ERROR: "模型加载失败",
        ErrorCode.INFERENCE_ERROR: "推理过程错误",
        
        # 数据库
        ErrorCode.DATABASE_CONNECTION_ERROR: "数据库连接失败",
        ErrorCode.DATABASE_QUERY_ERROR: "数据库查询错误",
        ErrorCode.DATABASE_CONSTRAINT_ERROR: "数据库约束错误",
        ErrorCode.DATABASE_TIMEOUT: "数据库操作超时",
        ErrorCode.VECTOR_DATABASE_ERROR: "向量数据库错误",
        ErrorCode.GRAPH_DATABASE_ERROR: "图数据库错误",
        
        # 系统
        ErrorCode.INTERNAL_SERVER_ERROR: "服务器内部错误",
        ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
        ErrorCode.RATE_LIMIT_EXCEEDED: "请求频率过高",
        ErrorCode.MAINTENANCE_MODE: "系统维护中",
        ErrorCode.CONFIGURATION_ERROR: "配置错误",
        ErrorCode.MEMORY_ERROR: "内存不足",
    }
    
    # 英文错误消息
    MESSAGES_EN = {
        # 认证相关
        ErrorCode.INVALID_CREDENTIALS: "Invalid username or password",
        ErrorCode.TOKEN_EXPIRED: "Token has expired, please login again",
        ErrorCode.TOKEN_INVALID: "Invalid access token",
        ErrorCode.ACCOUNT_LOCKED: "Account has been locked",
        ErrorCode.ACCOUNT_DISABLED: "Account has been disabled",
        ErrorCode.PASSWORD_EXPIRED: "Password has expired, please change password",
        ErrorCode.LOGIN_ATTEMPTS_EXCEEDED: "Too many login attempts, please try again later",
        
        # 权限相关
        ErrorCode.PERMISSION_DENIED: "Permission denied",
        ErrorCode.RESOURCE_NOT_OWNED: "You don't have permission to access this resource",
        ErrorCode.INSUFFICIENT_PRIVILEGES: "Insufficient privileges",
        ErrorCode.ROLE_NOT_ASSIGNED: "Required role not assigned",
        ErrorCode.DEPARTMENT_ACCESS_DENIED: "Department access denied",
        
        # 资源相关
        ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource already exists",
        ErrorCode.RESOURCE_CONFLICT: "Resource conflict",
        ErrorCode.RESOURCE_LOCKED: "Resource is locked",
        ErrorCode.RESOURCE_DELETED: "Resource has been deleted",
        ErrorCode.RESOURCE_EXPIRED: "Resource has expired",
        
        # 业务逻辑
        ErrorCode.INVALID_FILE_FORMAT: "Unsupported file format",
        ErrorCode.FILE_TOO_LARGE: "File size exceeds limit",
        ErrorCode.PROCESSING_FAILED: "Processing failed",
        ErrorCode.INVALID_OPERATION: "Invalid operation",
        ErrorCode.BUSINESS_RULE_VIOLATION: "Business rule violation",
        ErrorCode.WORKFLOW_ERROR: "Workflow error",
        
        # 数据验证
        ErrorCode.VALIDATION_ERROR: "Validation failed",
        ErrorCode.REQUIRED_FIELD_MISSING: "Required field missing",
        ErrorCode.INVALID_FORMAT: "Invalid format",
        ErrorCode.VALUE_OUT_OF_RANGE: "Value out of range",
        ErrorCode.DUPLICATE_VALUE: "Duplicate value",
        ErrorCode.INVALID_REFERENCE: "Invalid reference",
        
        # 外部服务
        ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: "External service unavailable",
        ErrorCode.EXTERNAL_API_ERROR: "External API error",
        ErrorCode.TIMEOUT_ERROR: "Request timeout",
        ErrorCode.NETWORK_ERROR: "Network error",
        ErrorCode.SERVICE_DEGRADED: "Service degraded",
        
        # AI服务
        ErrorCode.LLM_SERVICE_ERROR: "LLM service error",
        ErrorCode.EMBEDDING_SERVICE_ERROR: "Embedding service error",
        ErrorCode.RERANKER_SERVICE_ERROR: "Reranker service error",
        ErrorCode.AGENT_COLLABORATION_ERROR: "Agent collaboration error",
        ErrorCode.MODEL_LOADING_ERROR: "Model loading failed",
        ErrorCode.INFERENCE_ERROR: "Inference error",
        
        # 数据库
        ErrorCode.DATABASE_CONNECTION_ERROR: "Database connection failed",
        ErrorCode.DATABASE_QUERY_ERROR: "Database query error",
        ErrorCode.DATABASE_CONSTRAINT_ERROR: "Database constraint error",
        ErrorCode.DATABASE_TIMEOUT: "Database operation timeout",
        ErrorCode.VECTOR_DATABASE_ERROR: "Vector database error",
        ErrorCode.GRAPH_DATABASE_ERROR: "Graph database error",
        
        # 系统
        ErrorCode.INTERNAL_SERVER_ERROR: "Internal server error",
        ErrorCode.SERVICE_UNAVAILABLE: "Service unavailable",
        ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
        ErrorCode.MAINTENANCE_MODE: "System under maintenance",
        ErrorCode.CONFIGURATION_ERROR: "Configuration error",
        ErrorCode.MEMORY_ERROR: "Out of memory",
    }
    
    @classmethod
    def get_message(cls, error_code: ErrorCode, language: str = "zh") -> str:
        """获取错误消息"""
        messages = cls.MESSAGES_ZH if language == "zh" else cls.MESSAGES_EN
        return messages.get(error_code, "Unknown error")


def create_error_response(
    error_code: ErrorCode,
    message: str = None,
    details: Dict[str, Any] = None,
    language: str = "zh"
) -> Dict[str, Any]:
    """创建标准化错误响应"""
    if message is None:
        message = ErrorMessages.get_message(error_code, language)
    
    return {
        "success": False,
        "error": {
            "code": error_code.value,
            "message": message,
            "details": details or {},
        }
    }
