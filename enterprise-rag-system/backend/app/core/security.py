"""
安全相关模块
"""

from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core import settings
from app.models import User
from app.core.permission_cache import get_permission_cache
from app.core.error_codes import ErrorCode
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.permission_audit import audit_permission_check, audit_login

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
    """
    创建访问令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    """
    return pwd_context.hash(password)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    获取当前用户
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationException(error_code=ErrorCode.TOKEN_INVALID)
    except JWTError:
        raise AuthenticationException(error_code=ErrorCode.TOKEN_INVALID)

    user = await User.get_or_none(id=int(user_id))
    if user is None:
        raise AuthenticationException(error_code=ErrorCode.TOKEN_INVALID)

    # 检查用户状态
    if not user.is_active():
        raise AuthenticationException(error_code=ErrorCode.ACCOUNT_DISABLED)

    if user.is_locked():
        raise AuthenticationException(error_code=ErrorCode.ACCOUNT_LOCKED)

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户
    """
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="用户未激活"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前超级用户
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


def check_permission(permission_code: str):
    """
    权限检查装饰器
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        has_permission = await current_user.has_permission(permission_code)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission_code}"
            )
        
        return current_user
    
    return permission_checker


def check_role(role_code: str):
    """
    角色检查装饰器
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        has_role = await current_user.has_role(role_code)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少角色: {role_code}"
            )
        
        return current_user
    
    return role_checker


class PermissionChecker:
    """
    增强的权限检查器类，支持缓存
    """

    def __init__(self, permission_code: str, use_cache: bool = True):
        self.permission_code = permission_code
        self.use_cache = use_cache

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            # 记录超级用户权限检查
            audit_permission_check(
                user_id=current_user.id,
                username=current_user.username,
                permission_code=self.permission_code,
                success=True,
                details={"reason": "superuser"}
            )
            return current_user

        # 使用缓存检查权限
        has_permission = await self._check_permission_with_cache(current_user)

        # 记录权限检查审计
        audit_permission_check(
            user_id=current_user.id,
            username=current_user.username,
            permission_code=self.permission_code,
            success=has_permission,
            details={"cache_used": self.use_cache}
        )

        if not has_permission:
            raise AuthorizationException(
                error_code=ErrorCode.PERMISSION_DENIED,
                details={"required_permission": self.permission_code}
            )

        return current_user

    async def _check_permission_with_cache(self, user: User) -> bool:
        """使用缓存检查权限"""
        if not self.use_cache:
            return await user.has_permission(self.permission_code)

        cache = get_permission_cache()

        # 尝试从缓存获取
        cached_result = await cache.get_permission(user.id, self.permission_code)
        if cached_result is not None:
            return cached_result

        # 从数据库查询
        result = await user.has_permission(self.permission_code)

        # 设置缓存
        await cache.set_permission(user.id, self.permission_code, result, source="database")

        return result


class RoleChecker:
    """
    增强的角色检查器类，支持缓存
    """

    def __init__(self, role_code: str, use_cache: bool = True):
        self.role_code = role_code
        self.use_cache = use_cache

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        # 使用缓存检查角色
        has_role = await self._check_role_with_cache(current_user)

        if not has_role:
            raise AuthorizationException(
                error_code=ErrorCode.ROLE_NOT_ASSIGNED,
                details={"required_role": self.role_code}
            )

        return current_user

    async def _check_role_with_cache(self, user: User) -> bool:
        """使用缓存检查角色"""
        if not self.use_cache:
            return await user.has_role(self.role_code)

        cache = get_permission_cache()

        # 尝试从用户权限集合缓存获取
        cached_user_perms = await cache.get_user_permissions(user.id)
        if cached_user_perms is not None:
            return self.role_code in cached_user_perms.roles

        # 从数据库查询
        result = await user.has_role(self.role_code)

        # 这里可以选择性地更新缓存，或者在用户权限集合更新时一起更新

        return result


# 常用权限检查器实例
require_admin = RoleChecker("admin")
require_user_management = PermissionChecker("user:manage")
require_knowledge_base_read = PermissionChecker("knowledge_base:read")
require_knowledge_base_write = PermissionChecker("knowledge_base:write")
require_document_upload = PermissionChecker("document:upload")
require_chat_access = PermissionChecker("chat:access")


def generate_api_key() -> str:
    """
    生成API密钥
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str) -> bool:
    """
    验证API密钥
    """
    # 这里应该从数据库验证API密钥
    # 简单实现，实际应该更复杂
    return len(api_key) == 43  # token_urlsafe(32)的长度


async def get_user_by_api_key(api_key: str) -> Union[User, None]:
    """
    通过API密钥获取用户
    """
    # 这里应该从数据库查找API密钥对应的用户
    # 简单实现，实际需要API密钥管理表
    return None


def create_reset_token(user_id: int) -> str:
    """
    创建重置令牌
    """
    data = {
        "sub": str(user_id),
        "type": "reset",
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24小时有效
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_reset_token(token: str) -> Union[int, None]:
    """
    验证重置令牌
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if token_type != "reset" or user_id is None:
            return None
        
        return int(user_id)
    except JWTError:
        return None
