"""
RBAC统一异常处理
"""

from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import HTTPException
from loguru import logger

from .exceptions import BaseException as CoreBaseException


class RBACException(CoreBaseException):
    """RBAC基础异常"""
    
    def __init__(
        self,
        message: str,
        code: int = 400,
        details: Optional[str] = None,
        **kwargs
    ):
        self.message = message
        self.code = code
        self.details = details
        self.timestamp = datetime.now()
        super().__init__(message, **kwargs)


class DepartmentException(RBACException):
    """部门相关异常"""
    pass


class RoleException(RBACException):
    """角色相关异常"""
    pass


class PermissionException(RBACException):
    """权限相关异常"""
    pass


class UserRoleException(RBACException):
    """用户角色相关异常"""
    pass


def handle_rbac_exception(func):
    """RBAC异常处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"参数错误: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            raise HTTPException(status_code=403, detail=str(e))
        except FileNotFoundError as e:
            logger.error(f"资源不存在: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except RBACException as e:
            logger.error(f"RBAC异常: {e}")
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise HTTPException(status_code=500, detail="内部服务器错误")
    
    return wrapper


def create_error_response(
    code: int,
    message: str,
    details: Optional[str] = None
) -> Dict[str, Any]:
    """创建标准错误响应"""
    return {
        "code": code,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }


def create_success_response(
    data: Any = None,
    message: str = "操作成功"
) -> Dict[str, Any]:
    """创建标准成功响应"""
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
