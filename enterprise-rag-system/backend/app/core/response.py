"""
统一响应格式模块
标准格式: {code, msg, data}
"""

from typing import Any, Optional, List, Dict, Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class StandardResponseModel(BaseModel):
    """标准响应模型"""
    code: int = Field(..., description="响应状态码")
    msg: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class PaginationData(BaseModel):
    """分页数据模型"""
    items: List[Any] = Field([], description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")


def success_response(
    data: Any = None,
    msg: str = "OK",
    code: int = 200
) -> JSONResponse:
    """
    成功响应
    
    Args:
        data: 响应数据
        msg: 响应消息
        code: 状态码
    
    Returns:
        JSONResponse: 标准格式响应
    """
    content = {
        "code": code,
        "msg": msg,
        "data": data
    }
    return JSONResponse(content=content, status_code=200)


def error_response(
    msg: str,
    code: int = 400,
    data: Any = None
) -> JSONResponse:
    """
    错误响应
    
    Args:
        msg: 错误消息
        code: 错误状态码
        data: 错误详情数据
    
    Returns:
        JSONResponse: 标准格式错误响应
    """
    content = {
        "code": code,
        "msg": msg,
        "data": data
    }
    return JSONResponse(content=content, status_code=200)  # HTTP状态码统一为200，业务状态码在code字段


def pagination_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    msg: str = "OK",
    code: int = 200
) -> JSONResponse:
    """
    分页响应
    
    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
        msg: 响应消息
        code: 状态码
    
    Returns:
        JSONResponse: 标准格式分页响应
    """
    pagination_data = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
    
    content = {
        "code": code,
        "msg": msg,
        "data": pagination_data
    }
    return JSONResponse(content=content, status_code=200)


# 常用响应快捷方法
class Response:
    """响应工具类"""
    
    @staticmethod
    def success(data: Any = None, msg: str = "OK") -> JSONResponse:
        """成功响应"""
        return success_response(data=data, msg=msg)
    
    @staticmethod
    def error(msg: str, code: int = 400, data: Any = None) -> JSONResponse:
        """错误响应"""
        return error_response(msg=msg, code=code, data=data)
    
    @staticmethod
    def pagination(
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        msg: str = "OK"
    ) -> JSONResponse:
        """分页响应"""
        return pagination_response(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            msg=msg
        )
    
    @staticmethod
    def created(data: Any = None, msg: str = "创建成功") -> JSONResponse:
        """创建成功响应"""
        return success_response(data=data, msg=msg, code=201)
    
    @staticmethod
    def updated(data: Any = None, msg: str = "更新成功") -> JSONResponse:
        """更新成功响应"""
        return success_response(data=data, msg=msg)
    
    @staticmethod
    def deleted(msg: str = "删除成功") -> JSONResponse:
        """删除成功响应"""
        return success_response(msg=msg)
    
    @staticmethod
    def not_found(msg: str = "资源不存在") -> JSONResponse:
        """资源不存在响应"""
        return error_response(msg=msg, code=404)
    
    @staticmethod
    def unauthorized(msg: str = "未授权访问") -> JSONResponse:
        """未授权响应"""
        return error_response(msg=msg, code=401)
    
    @staticmethod
    def forbidden(msg: str = "权限不足") -> JSONResponse:
        """权限不足响应"""
        return error_response(msg=msg, code=403)
    
    @staticmethod
    def bad_request(msg: str = "请求参数错误") -> JSONResponse:
        """请求参数错误响应"""
        return error_response(msg=msg, code=400)
    
    @staticmethod
    def internal_error(msg: str = "服务器内部错误") -> JSONResponse:
        """服务器内部错误响应"""
        return error_response(msg=msg, code=500)


# 导出常用方法
__all__ = [
    "StandardResponseModel",
    "PaginationData", 
    "success_response",
    "error_response",
    "pagination_response",
    "Response"
]
