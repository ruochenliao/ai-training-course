"""
企业级异常处理中间件
统一处理应用中的异常，提供标准化的错误响应
"""

import traceback
import uuid
import time
import os
from datetime import datetime
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from tortoise.exceptions import DoesNotExist, IntegrityError
from pydantic import ValidationError
from ..core.config import settings
from ..utils.error_codes import ErrorCode, ErrorCodeManager
from ..schemas.common import ErrorDetail, ResponseMetadata


class ExceptionMiddleware(BaseHTTPMiddleware):
    """企业级异常处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和异常"""
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        # 设置请求上下文
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.start_time = start_time

        try:
            response = await call_next(request)

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Execution-Time"] = str(int((time.time() - start_time) * 1000))

            return response

        except HTTPException as exc:
            # FastAPI HTTP异常
            return await self._handle_http_exception(exc, request_id, trace_id, start_time)

        except ValidationError as exc:
            # Pydantic验证异常
            return await self._handle_validation_error(exc, request_id, trace_id, start_time)

        except DoesNotExist as exc:
            # Tortoise ORM 对象不存在异常
            return await self._handle_not_found_error(exc, request_id, trace_id, start_time)

        except IntegrityError as exc:
            # 数据库完整性异常
            return await self._handle_integrity_error(exc, request_id, trace_id, start_time)

        except Exception as exc:
            # 其他未处理异常
            return await self._handle_internal_error(exc, request_id, trace_id, start_time, request)

    def _create_error_response(
        self,
        error_code: ErrorCode,
        request_id: str,
        trace_id: str,
        start_time: float,
        detail: str = None,
        errors: list = None
    ) -> dict:
        """创建标准错误响应"""
        execution_time = int((time.time() - start_time) * 1000)

        return {
            "code": error_code.code,
            "message": error_code.message,
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "trace_id": trace_id,
            "metadata": {
                "api_version": "v1.0.0",
                "server_time": int(time.time() * 1000),
                "execution_time": execution_time,
                "server_id": os.getenv("SERVER_ID", "server-001")
            },
            "error_type": ErrorCodeManager._get_error_type(error_code.code),
            "detail": detail,
            "errors": errors
        }

    async def _handle_http_exception(
        self,
        exc: HTTPException,
        request_id: str,
        trace_id: str,
        start_time: float
    ) -> JSONResponse:
        """处理HTTP异常"""
        # 根据状态码映射到错误码
        error_code_map = {
            400: ErrorCode.BAD_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            422: ErrorCode.UNPROCESSABLE_ENTITY,
            429: ErrorCode.TOO_MANY_REQUESTS,
            500: ErrorCode.INTERNAL_SERVER_ERROR
        }

        error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

        response_content = self._create_error_response(
            error_code=error_code,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            detail=exc.detail
        )

        # 如果有自定义消息，使用自定义消息
        if exc.detail:
            response_content["message"] = exc.detail

        response = JSONResponse(
            status_code=exc.status_code,
            content=response_content
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response

    async def _handle_validation_error(
        self,
        exc: ValidationError,
        request_id: str,
        trace_id: str,
        start_time: float
    ) -> JSONResponse:
        """处理验证错误"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "code": error["type"],
                "value": error.get("input")
            })

        response_content = self._create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            detail="请求参数验证失败",
            errors=errors
        )

        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response_content
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response

    async def _handle_not_found_error(
        self,
        exc: DoesNotExist,
        request_id: str,
        trace_id: str,
        start_time: float
    ) -> JSONResponse:
        """处理资源不存在错误"""
        response_content = self._create_error_response(
            error_code=ErrorCode.NOT_FOUND,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            detail="请求的资源不存在"
        )

        response = JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_content
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response

    async def _handle_integrity_error(
        self,
        exc: IntegrityError,
        request_id: str,
        trace_id: str,
        start_time: float
    ) -> JSONResponse:
        """处理数据库完整性错误"""
        message = "数据操作失败"
        error_code = ErrorCode.BAD_REQUEST

        # 根据错误信息提供更友好的提示
        error_str = str(exc).lower()
        if "unique" in error_str or "duplicate" in error_str:
            message = "数据已存在，请检查唯一性约束"
            error_code = ErrorCode.CONFLICT
        elif "foreign key" in error_str:
            message = "关联数据不存在或已被引用"
            error_code = ErrorCode.DEPENDENCY_EXISTS
        elif "not null" in error_str:
            message = "必填字段不能为空"
            error_code = ErrorCode.MISSING_PARAMETER

        response_content = self._create_error_response(
            error_code=error_code,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            detail=message
        )

        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response_content
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response

    async def _handle_internal_error(
        self,
        exc: Exception,
        request_id: str,
        trace_id: str,
        start_time: float,
        request: Request
    ) -> JSONResponse:
        """处理内部服务器错误"""
        # 记录详细错误信息
        error_details = {
            "request_id": request_id,
            "trace_id": trace_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "exception": str(exc),
            "traceback": traceback.format_exc(),
            "execution_time": int((time.time() - start_time) * 1000)
        }

        # 在开发环境下打印详细错误信息
        if settings.DEBUG:
            print(f"Internal Server Error: {error_details}")

        # 生产环境下不暴露详细错误信息
        detail = str(exc) if settings.DEBUG else "服务器内部错误，请联系管理员"

        response_content = self._create_error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            request_id=request_id,
            trace_id=trace_id,
            start_time=start_time,
            detail=detail
        )

        # 在开发环境下添加调试信息
        if settings.DEBUG:
            response_content["debug_info"] = {
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc().split('\n')
            }

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_content
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response
