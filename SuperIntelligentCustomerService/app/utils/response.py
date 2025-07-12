"""
统一响应格式工具
"""
from typing import Any, Optional

from pydantic import BaseModel


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int
    msg: str
    data: Optional[Any] = None


def Success(data: Any = None, msg: str = "操作成功") -> ResponseModel:
    """成功响应"""
    return ResponseModel(code=200, msg=msg, data=data)


def Fail(msg: str = "操作失败", code: int = 400, data: Any = None) -> ResponseModel:
    """失败响应"""
    return ResponseModel(code=code, msg=msg, data=data)


def Error(msg: str = "服务器错误", code: int = 500, data: Any = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(code=code, msg=msg, data=data)



