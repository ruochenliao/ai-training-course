"""
中间件模块
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import RateLimitException


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """请求处理时间中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求开始
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            response = await call_next(request)
            
            # 记录请求完成
            process_time = time.time() - start_time
            logger.info(
                f"请求完成: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )
            
            return response
            
        except Exception as e:
            # 记录请求异常
            process_time = time.time() - start_time
            logger.error(
                f"请求异常: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "exception": str(e),
                }
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # 简单的内存存储，生产环境应使用Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 跳过健康检查和文档路径
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        # 清理过期的请求记录
        self._cleanup_old_requests(current_time)
        
        # 检查当前分钟窗口的请求数
        key = f"{client_ip}:{minute_window}"
        current_requests = self.requests.get(key, 0)
        
        if current_requests >= self.calls_per_minute:
            logger.warning(
                f"限流触发: IP {client_ip} 在当前分钟内请求次数 {current_requests} 超过限制 {self.calls_per_minute}",
                extra={
                    "client_ip": client_ip,
                    "current_requests": current_requests,
                    "limit": self.calls_per_minute,
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"请求频率过高，每分钟最多允许 {self.calls_per_minute} 次请求",
                        "details": {
                            "limit": self.calls_per_minute,
                            "window": "1 minute",
                            "retry_after": 60 - (current_time % 60),
                        }
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": str(max(0, self.calls_per_minute - current_requests - 1)),
                    "X-RateLimit-Reset": str(int((minute_window + 1) * 60)),
                    "Retry-After": str(int(60 - (current_time % 60))),
                }
            )
        
        # 增加请求计数
        self.requests[key] = current_requests + 1
        
        response = await call_next(request)
        
        # 添加限流相关的响应头
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls_per_minute - self.requests[key]))
        response.headers["X-RateLimit-Reset"] = str(int((minute_window + 1) * 60))
        
        return response
    
    def _cleanup_old_requests(self, current_time: float):
        """清理过期的请求记录"""
        current_minute = int(current_time // 60)
        keys_to_remove = []
        
        for key in self.requests:
            try:
                minute = int(key.split(":")[1])
                if minute < current_minute - 1:  # 保留当前分钟和前一分钟的记录
                    keys_to_remove.append(key)
            except (IndexError, ValueError):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全相关的响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 根据路径设置缓存策略
        if request.url.path.startswith("/api/"):
            # API响应不缓存
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif request.url.path in ["/docs", "/redoc"]:
            # 文档页面短时间缓存
            response.headers["Cache-Control"] = "public, max-age=300"  # 5分钟
        elif request.url.path.startswith("/static/"):
            # 静态资源长时间缓存
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1年
        
        return response
