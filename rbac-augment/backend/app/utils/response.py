"""
企业级响应工具类
提供标准化的API响应创建方法
"""

import uuid
import time
from typing import Any, Optional, List, Dict
from datetime import datetime
from fastapi import Request
from app.schemas.common import (
    BaseResponse, ErrorResponse, PaginationResponse, PaginationInfo,
    ResponseMetadata, ErrorDetail, ApiResponse
)
from app.utils.error_codes import ErrorCode, ErrorCodeManager


class ResponseBuilder:
    """响应构建器"""
    
    def __init__(self, request: Optional[Request] = None):
        self.request = request
        self.request_id = getattr(request.state, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
        self.trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
        self.start_time = getattr(request.state, 'start_time', time.time()) if request else time.time()
    
    def _create_metadata(self) -> ResponseMetadata:
        """创建响应元数据"""
        execution_time = int((time.time() - self.start_time) * 1000)
        return ResponseMetadata(
            execution_time=execution_time
        )
    
    def success(
        self,
        data: Any = None,
        message: str = "操作成功",
        code: int = 200
    ) -> BaseResponse:
        """创建成功响应"""
        return BaseResponse(
            code=code,
            message=message,
            data=data,
            request_id=self.request_id,
            trace_id=self.trace_id,
            metadata=self._create_metadata()
        )
    
    def error(
        self,
        error_code: ErrorCode,
        detail: str = None,
        errors: List[ErrorDetail] = None,
        data: Any = None
    ) -> ErrorResponse:
        """创建错误响应"""
        return ErrorResponse(
            code=error_code.code,
            message=error_code.message,
            data=data,
            request_id=self.request_id,
            trace_id=self.trace_id,
            metadata=self._create_metadata(),
            errors=errors,
            error_type=ErrorCodeManager._get_error_type(error_code.code),
            detail=detail
        )
    
    def paginated(
        self,
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "查询成功"
    ) -> BaseResponse:
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        start_index = (page - 1) * page_size + 1 if total > 0 else 0
        end_index = min(page * page_size, total)
        
        pagination_info = PaginationInfo(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            start_index=start_index,
            end_index=end_index
        )
        
        pagination_response = PaginationResponse(
            items=items,
            pagination=pagination_info,
            # 兼容旧版本字段
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        return self.success(
            data=pagination_response,
            message=message
        )


class ResponseHelper:
    """响应助手类 - 提供静态方法"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: int = 200,
        request: Optional[Request] = None
    ) -> BaseResponse:
        """创建成功响应"""
        builder = ResponseBuilder(request)
        return builder.success(data, message, code)
    
    @staticmethod
    def error(
        error_code: ErrorCode,
        detail: str = None,
        errors: List[ErrorDetail] = None,
        data: Any = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建错误响应"""
        builder = ResponseBuilder(request)
        return builder.error(error_code, detail, errors, data)
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "查询成功",
        request: Optional[Request] = None
    ) -> BaseResponse:
        """创建分页响应"""
        builder = ResponseBuilder(request)
        return builder.paginated(items, total, page, page_size, message)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功",
        request: Optional[Request] = None
    ) -> BaseResponse:
        """创建资源创建成功响应"""
        builder = ResponseBuilder(request)
        return builder.success(data, message, 201)
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = "更新成功",
        request: Optional[Request] = None
    ) -> BaseResponse:
        """创建资源更新成功响应"""
        builder = ResponseBuilder(request)
        return builder.success(data, message, 200)
    
    @staticmethod
    def deleted(
        message: str = "删除成功",
        request: Optional[Request] = None
    ) -> BaseResponse:
        """创建资源删除成功响应"""
        builder = ResponseBuilder(request)
        return builder.success(None, message, 204)
    
    @staticmethod
    def not_found(
        message: str = "资源未找到",
        detail: str = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建资源未找到响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.NOT_FOUND, detail or message)
    
    @staticmethod
    def forbidden(
        message: str = "权限不足",
        detail: str = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建权限不足响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.FORBIDDEN, detail or message)
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        detail: str = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建未授权响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.UNAUTHORIZED, detail or message)
    
    @staticmethod
    def validation_error(
        errors: List[ErrorDetail],
        message: str = "数据验证失败",
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建验证错误响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.VALIDATION_ERROR, message, errors)
    
    @staticmethod
    def conflict(
        message: str = "资源冲突",
        detail: str = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建资源冲突响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.CONFLICT, detail or message)
    
    @staticmethod
    def internal_error(
        message: str = "服务器内部错误",
        detail: str = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建内部错误响应"""
        builder = ResponseBuilder(request)
        return builder.error(ErrorCode.INTERNAL_SERVER_ERROR, detail or message)


# 便捷的全局响应函数
def success_response(*args, **kwargs) -> BaseResponse:
    """成功响应快捷方法"""
    return ResponseHelper.success(*args, **kwargs)


def error_response(*args, **kwargs) -> ErrorResponse:
    """错误响应快捷方法"""
    return ResponseHelper.error(*args, **kwargs)


def paginated_response(*args, **kwargs) -> BaseResponse:
    """分页响应快捷方法"""
    return ResponseHelper.paginated(*args, **kwargs)
