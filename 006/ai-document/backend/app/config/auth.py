"""
认证配置
"""
from typing import Dict, Any, List
from datetime import timedelta
from .base import settings


class AuthConfig:
    """认证配置类"""
    
    @staticmethod
    def get_jwt_config() -> Dict[str, Any]:
        """获取JWT配置"""
        return {
            "secret_key": settings.secret_key,
            "algorithm": settings.algorithm,
            "access_token_expire_minutes": settings.access_token_expire_minutes,
            "refresh_token_expire_days": settings.refresh_token_expire_days,
        }
    
    @staticmethod
    def get_password_config() -> Dict[str, Any]:
        """获取密码配置"""
        return {
            "schemes": ["bcrypt"],
            "deprecated": "auto",
            "bcrypt__rounds": 12,
        }
    
    @staticmethod
    def get_access_token_expire_delta() -> timedelta:
        """获取访问令牌过期时间"""
        return timedelta(minutes=settings.access_token_expire_minutes)
    
    @staticmethod
    def get_refresh_token_expire_delta() -> timedelta:
        """获取刷新令牌过期时间"""
        return timedelta(days=settings.refresh_token_expire_days)
    
    @staticmethod
    def get_cookie_config() -> Dict[str, Any]:
        """获取Cookie配置"""
        return {
            "key": "access_token",
            "httponly": True,
            "secure": settings.is_production,
            "samesite": "lax",
            "max_age": settings.access_token_expire_minutes * 60,
        }
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """获取CORS配置"""
        return {
            "allow_origins": settings.cors_origins,
            "allow_credentials": settings.cors_allow_credentials,
            "allow_methods": settings.cors_allow_methods,
            "allow_headers": settings.cors_allow_headers,
        }
    
    @staticmethod
    def get_rate_limit_config() -> Dict[str, Any]:
        """获取限流配置"""
        return {
            "enabled": settings.rate_limit_enabled,
            "requests": settings.rate_limit_requests,
            "window": settings.rate_limit_window,
        }
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """获取安全头配置"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        }
    
    @staticmethod
    def get_oauth_config() -> Dict[str, Any]:
        """获取OAuth配置（预留）"""
        return {
            "google": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "/auth/google/callback",
            },
            "github": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "/auth/github/callback",
            },
        }
    
    @staticmethod
    def get_session_config() -> Dict[str, Any]:
        """获取会话配置"""
        return {
            "secret_key": settings.secret_key,
            "session_cookie": "session_id",
            "max_age": 86400,  # 24小时
            "httponly": True,
            "secure": settings.is_production,
        }
