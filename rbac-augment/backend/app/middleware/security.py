"""
企业级安全中间件
提供IP白名单、限流、安全头等安全功能
"""

import time
import ipaddress
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings
from ..utils.error_codes import ErrorCode


class RateLimiter:
    """限流器"""
    
    def __init__(self):
        # 存储每个IP的请求记录 {ip: deque(timestamps)}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        # 存储每个IP的锁定状态 {ip: unlock_time}
        self.locked_ips: Dict[str, float] = {}
    
    def is_allowed(self, ip: str, limit: int = None, window: int = 60) -> bool:
        """
        检查IP是否允许请求
        
        Args:
            ip: 客户端IP
            limit: 限制次数（默认使用配置）
            window: 时间窗口（秒）
        
        Returns:
            bool: 是否允许请求
        """
        if not settings.ENABLE_RATE_LIMITING:
            return True
        
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        current_time = time.time()
        
        # 检查IP是否被锁定
        if ip in self.locked_ips:
            if current_time < self.locked_ips[ip]:
                return False
            else:
                # 解锁IP
                del self.locked_ips[ip]
        
        # 清理过期的请求记录
        requests = self.requests[ip]
        while requests and requests[0] < current_time - window:
            requests.popleft()
        
        # 检查是否超过限制
        if len(requests) >= limit:
            # 锁定IP 5分钟
            self.locked_ips[ip] = current_time + 300
            return False
        
        # 记录当前请求
        requests.append(current_time)
        return True
    
    def get_remaining_requests(self, ip: str, limit: int = None, window: int = 60) -> int:
        """获取剩余请求次数"""
        if not settings.ENABLE_RATE_LIMITING:
            return limit or settings.RATE_LIMIT_PER_MINUTE
        
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        current_time = time.time()
        
        # 清理过期的请求记录
        requests = self.requests[ip]
        while requests and requests[0] < current_time - window:
            requests.popleft()
        
        return max(0, limit - len(requests))
    
    def get_reset_time(self, ip: str, window: int = 60) -> Optional[datetime]:
        """获取限制重置时间"""
        requests = self.requests[ip]
        if not requests:
            return None
        
        oldest_request = requests[0]
        reset_time = oldest_request + window
        return datetime.fromtimestamp(reset_time)


class IPWhitelistChecker:
    """IP白名单检查器"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 检查Cloudflare头
        cf_connecting_ip = request.headers.get("CF-Connecting-IP")
        if cf_connecting_ip:
            return cf_connecting_ip
        
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def is_ip_allowed(ip: str, whitelist: List[str] = None) -> bool:
        """检查IP是否在白名单中"""
        if not settings.ENABLE_IP_WHITELIST:
            return True
        
        whitelist = whitelist or settings.IP_WHITELIST
        if not whitelist:
            return True
        
        try:
            client_ip = ipaddress.ip_address(ip)
            
            for allowed_ip in whitelist:
                try:
                    if "/" in allowed_ip:
                        # CIDR网段
                        network = ipaddress.ip_network(allowed_ip, strict=False)
                        if client_ip in network:
                            return True
                    else:
                        # 单个IP
                        if client_ip == ipaddress.ip_address(allowed_ip):
                            return True
                except ValueError:
                    # 忽略无效的IP格式
                    continue
            
            return False
        except ValueError:
            # 无效的客户端IP
            return False


class SecurityHeadersManager:
    """安全头管理器"""
    
    @staticmethod
    def add_security_headers(response: Response) -> Response:
        """添加安全响应头"""
        # 防止XSS攻击
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (仅在HTTPS下)
        if settings.DEBUG is False:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 内容安全策略 - 根据环境调整
        if settings.DEBUG:
            # 开发环境：允许Swagger UI CDN资源
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https: https://cdn.jsdelivr.net; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        else:
            # 生产环境：严格的CSP策略
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )

        response.headers["Content-Security-Policy"] = csp_policy

        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )

        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """企业级安全中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.ip_checker = IPWhitelistChecker()
        self.headers_manager = SecurityHeadersManager()
        
        # 不需要安全检查的路径
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求安全检查"""
        # 获取客户端IP
        client_ip = self.ip_checker.get_client_ip(request)
        request.state.client_ip = client_ip

        # 跳过不需要检查的路径和OPTIONS请求（CORS预检）
        if request.url.path in self.excluded_paths or request.method == "OPTIONS":
            response = await call_next(request)
            return self.headers_manager.add_security_headers(response)
        
        try:
            # IP白名单检查
            if not self.ip_checker.is_ip_allowed(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "code": ErrorCode.IP_NOT_ALLOWED.code,
                        "message": ErrorCode.IP_NOT_ALLOWED.message,
                        "detail": f"IP地址 {client_ip} 不在允许的白名单中",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # 限流检查
            if not self.rate_limiter.is_allowed(client_ip):
                remaining = self.rate_limiter.get_remaining_requests(client_ip)
                reset_time = self.rate_limiter.get_reset_time(client_ip)
                
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "code": ErrorCode.RATE_LIMIT_EXCEEDED.code,
                        "message": ErrorCode.RATE_LIMIT_EXCEEDED.message,
                        "detail": "请求过于频繁，请稍后再试",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # 添加限流相关头
                response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                if reset_time:
                    response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
                
                return response
            
            # 处理请求
            response = await call_next(request)
            
            # 添加限流信息到响应头
            remaining = self.rate_limiter.get_remaining_requests(client_ip)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            
            reset_time = self.rate_limiter.get_reset_time(client_ip)
            if reset_time:
                response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
            
            # 添加安全头
            return self.headers_manager.add_security_headers(response)
            
        except Exception as exc:
            # 安全检查异常，记录日志并返回错误
            print(f"Security middleware error: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": ErrorCode.INTERNAL_SERVER_ERROR.code,
                    "message": "安全检查失败",
                    "timestamp": datetime.now().isoformat()
                }
            )
