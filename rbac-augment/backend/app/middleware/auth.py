"""
认证中间件
处理JWT Token认证和用户信息注入
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.security import verify_token
from ..crud.user import crud_user


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    # 不需要认证的路径
    EXCLUDE_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求认证"""
        start_time = time.time()
        
        # 检查是否需要认证
        if self._should_skip_auth(request):
            response = await call_next(request)
        else:
            # 尝试获取用户信息
            user = await self._get_user_from_token(request)
            request.state.current_user = user
            response = await call_next(request)
        
        # 添加响应时间头
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # 添加请求ID头
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-ID"] = request.state.request_id
        
        return response
    
    def _should_skip_auth(self, request: Request) -> bool:
        """检查是否应该跳过认证"""
        path = request.url.path
        
        # 检查排除路径
        if path in self.EXCLUDE_PATHS:
            return True
        
        # 检查静态文件路径
        if path.startswith("/static/") or path.startswith("/assets/"):
            return True
        
        # 检查健康检查路径
        if path.startswith("/health"):
            return True
        
        return False
    
    async def _get_user_from_token(self, request: Request):
        """从Token获取用户信息"""
        try:
            # 获取Authorization头
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None
            
            # 检查Bearer格式
            if not authorization.startswith("Bearer "):
                return None
            
            # 提取Token
            token = authorization.split(" ")[1]
            
            # 验证Token
            user_id = verify_token(token, "access")
            if not user_id:
                return None
            
            # 获取用户信息
            user = await crud_user.get(int(user_id))
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception:
            return None
