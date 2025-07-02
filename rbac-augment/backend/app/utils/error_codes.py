"""
企业级错误码定义
统一管理系统中的所有错误码和错误信息
"""

from enum import Enum
from typing import Dict, Any


class ErrorCode(Enum):
    """错误码枚举"""
    
    # 成功响应 (200-299)
    SUCCESS = (200, "操作成功")
    CREATED = (201, "创建成功")
    UPDATED = (202, "更新成功")
    DELETED = (204, "删除成功")
    
    # 客户端错误 (400-499)
    BAD_REQUEST = (400, "请求参数错误")
    VALIDATION_ERROR = (400001, "数据验证失败")
    MISSING_PARAMETER = (400002, "缺少必需参数")
    INVALID_PARAMETER = (400003, "参数格式错误")
    PARAMETER_OUT_OF_RANGE = (400004, "参数超出范围")
    
    # 认证错误 (401-401999)
    UNAUTHORIZED = (401, "未授权访问")
    TOKEN_EXPIRED = (401001, "令牌已过期")
    TOKEN_INVALID = (401002, "令牌无效")
    TOKEN_MISSING = (401003, "缺少认证令牌")
    LOGIN_REQUIRED = (401004, "需要登录")
    LOGIN_FAILED = (401005, "登录失败")
    PASSWORD_INCORRECT = (401006, "密码错误")
    ACCOUNT_LOCKED = (401007, "账户已锁定")
    ACCOUNT_DISABLED = (401008, "账户已禁用")
    
    # 权限错误 (403-403999)
    FORBIDDEN = (403, "权限不足")
    PERMISSION_DENIED = (403001, "权限被拒绝")
    ROLE_PERMISSION_DENIED = (403002, "角色权限不足")
    DATA_PERMISSION_DENIED = (403003, "数据权限不足")
    IP_NOT_ALLOWED = (403004, "IP地址不在白名单")
    TIME_WINDOW_DENIED = (403005, "不在允许的时间窗口")
    OPERATION_NOT_ALLOWED = (403006, "操作不被允许")
    
    # 资源错误 (404-404999)
    NOT_FOUND = (404, "资源未找到")
    USER_NOT_FOUND = (404001, "用户不存在")
    ROLE_NOT_FOUND = (404002, "角色不存在")
    PERMISSION_NOT_FOUND = (404003, "权限不存在")
    MENU_NOT_FOUND = (404004, "菜单不存在")
    DEPARTMENT_NOT_FOUND = (404005, "部门不存在")
    
    # 冲突错误 (409-409999)
    CONFLICT = (409, "资源冲突")
    USER_EXISTS = (409001, "用户已存在")
    ROLE_EXISTS = (409002, "角色已存在")
    PERMISSION_EXISTS = (409003, "权限已存在")
    MENU_EXISTS = (409004, "菜单已存在")
    DEPARTMENT_EXISTS = (409005, "部门已存在")
    EMAIL_EXISTS = (409006, "邮箱已存在")
    USERNAME_EXISTS = (409007, "用户名已存在")
    
    # 业务逻辑错误 (422-422999)
    UNPROCESSABLE_ENTITY = (422, "无法处理的实体")
    BUSINESS_LOGIC_ERROR = (422001, "业务逻辑错误")
    INVALID_OPERATION = (422002, "无效操作")
    DEPENDENCY_EXISTS = (422003, "存在依赖关系")
    CIRCULAR_DEPENDENCY = (422004, "循环依赖")
    INVALID_STATE = (422005, "状态无效")
    
    # 限流错误 (429-429999)
    TOO_MANY_REQUESTS = (429, "请求过于频繁")
    RATE_LIMIT_EXCEEDED = (429001, "超出速率限制")
    CONCURRENT_LIMIT_EXCEEDED = (429002, "超出并发限制")
    
    # 服务器错误 (500-599)
    INTERNAL_SERVER_ERROR = (500, "服务器内部错误")
    DATABASE_ERROR = (500001, "数据库错误")
    CACHE_ERROR = (500002, "缓存错误")
    EXTERNAL_SERVICE_ERROR = (500003, "外部服务错误")
    CONFIGURATION_ERROR = (500004, "配置错误")
    
    # 服务不可用 (503-503999)
    SERVICE_UNAVAILABLE = (503, "服务不可用")
    DATABASE_UNAVAILABLE = (503001, "数据库不可用")
    CACHE_UNAVAILABLE = (503002, "缓存服务不可用")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
    
    @property
    def is_success(self) -> bool:
        """判断是否为成功状态码"""
        return 200 <= self.code < 300
    
    @property
    def is_client_error(self) -> bool:
        """判断是否为客户端错误"""
        return 400 <= self.code < 500
    
    @property
    def is_server_error(self) -> bool:
        """判断是否为服务器错误"""
        return 500 <= self.code < 600


class ErrorCodeManager:
    """错误码管理器"""
    
    @staticmethod
    def get_error_info(error_code: ErrorCode) -> Dict[str, Any]:
        """获取错误信息"""
        return {
            "code": error_code.code,
            "message": error_code.message,
            "type": ErrorCodeManager._get_error_type(error_code.code)
        }
    
    @staticmethod
    def _get_error_type(code: int) -> str:
        """根据错误码获取错误类型"""
        if 200 <= code < 300:
            return "success"
        elif 400 <= code < 500:
            return "client_error"
        elif 500 <= code < 600:
            return "server_error"
        else:
            return "unknown"
    
    @staticmethod
    def create_error_response(
        error_code: ErrorCode,
        detail: str = None,
        errors: list = None
    ) -> Dict[str, Any]:
        """创建标准错误响应"""
        response = ErrorCodeManager.get_error_info(error_code)
        
        if detail:
            response["detail"] = detail
        
        if errors:
            response["errors"] = errors
            
        return response


# 常用错误码快捷访问
SUCCESS = ErrorCode.SUCCESS
BAD_REQUEST = ErrorCode.BAD_REQUEST
UNAUTHORIZED = ErrorCode.UNAUTHORIZED
FORBIDDEN = ErrorCode.FORBIDDEN
NOT_FOUND = ErrorCode.NOT_FOUND
INTERNAL_SERVER_ERROR = ErrorCode.INTERNAL_SERVER_ERROR
