"""
企业级权限验证装饰器
提供多层权限验证、数据权限控制、安全增强等功能
"""

from functools import wraps
from typing import List, Callable, Any, Optional, Union, Dict
from enum import Enum
import time
import ipaddress
from datetime import datetime, time as dt_time
from fastapi import HTTPException, status, Request
from ..models.user import User
from ..core.config import settings
from .error_codes import ErrorCode


class PermissionLogic(Enum):
    """权限逻辑枚举"""
    AND = "AND"  # 需要所有权限
    OR = "OR"    # 需要任意权限


class DataScope(Enum):
    """数据权限范围枚举"""
    ALL = "all"              # 全部数据
    DEPARTMENT = "department"  # 本部门数据
    DEPARTMENT_AND_SUB = "department_and_sub"  # 本部门及子部门数据
    SELF = "self"            # 仅本人数据
    CUSTOM = "custom"        # 自定义数据权限


class PermissionValidator:
    """权限验证器"""

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    @staticmethod
    def _check_ip_whitelist(request: Request) -> bool:
        """检查IP白名单"""
        if not settings.ENABLE_IP_WHITELIST or not settings.IP_WHITELIST:
            return True

        client_ip = PermissionValidator._get_client_ip(request)

        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for allowed_ip in settings.IP_WHITELIST:
                try:
                    if "/" in allowed_ip:
                        # CIDR网段
                        if client_ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                            return True
                    else:
                        # 单个IP
                        if client_ip_obj == ipaddress.ip_address(allowed_ip):
                            return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False

    @staticmethod
    def _check_time_window(time_windows: List[Dict[str, str]]) -> bool:
        """检查时间窗口权限"""
        if not time_windows:
            return True

        current_time = datetime.now().time()
        current_weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday

        for window in time_windows:
            # 检查星期
            if "weekdays" in window:
                allowed_weekdays = window["weekdays"]
                if current_weekday not in allowed_weekdays:
                    continue

            # 检查时间范围
            start_time = dt_time.fromisoformat(window.get("start_time", "00:00:00"))
            end_time = dt_time.fromisoformat(window.get("end_time", "23:59:59"))

            if start_time <= current_time <= end_time:
                return True

        return False


def require_permissions(
    permissions: List[str],
    logic: PermissionLogic = PermissionLogic.AND,
    check_ip: bool = False,
    time_windows: List[Dict[str, str]] = None,
    data_scope: DataScope = None
):
    """
    企业级权限验证装饰器

    Args:
        permissions: 必需的权限列表
        logic: 权限逻辑（AND/OR）
        check_ip: 是否检查IP白名单
        time_windows: 时间窗口限制
        data_scope: 数据权限范围
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象和用户
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')

            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=ErrorCode.UNAUTHORIZED.code,
                    detail=ErrorCode.UNAUTHORIZED.message
                )

            # IP白名单检查
            if check_ip and request:
                if not PermissionValidator._check_ip_whitelist(request):
                    raise HTTPException(
                        status_code=ErrorCode.IP_NOT_ALLOWED.code,
                        detail=ErrorCode.IP_NOT_ALLOWED.message
                    )

            # 时间窗口检查
            if time_windows:
                if not PermissionValidator._check_time_window(time_windows):
                    raise HTTPException(
                        status_code=ErrorCode.TIME_WINDOW_DENIED.code,
                        detail=ErrorCode.TIME_WINDOW_DENIED.message
                    )

            # 超级用户拥有所有权限
            if current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            user_permissions = await current_user.get_permissions()

            if logic == PermissionLogic.AND:
                # 需要所有权限
                missing_permissions = [p for p in permissions if p not in user_permissions]
                if missing_permissions:
                    raise HTTPException(
                        status_code=ErrorCode.PERMISSION_DENIED.code,
                        detail=f"权限不足，缺少权限: {', '.join(missing_permissions)}"
                    )
            else:
                # 需要任意权限
                has_permission = any(p in user_permissions for p in permissions)
                if not has_permission:
                    raise HTTPException(
                        status_code=ErrorCode.PERMISSION_DENIED.code,
                        detail=f"权限不足，需要以下任意一个权限: {', '.join(permissions)}"
                    )

            # 设置数据权限范围
            if data_scope:
                kwargs['data_scope'] = data_scope
                kwargs['user_department_id'] = getattr(current_user, 'department_id', None)

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(
    permissions: List[str],
    check_ip: bool = False,
    time_windows: List[Dict[str, str]] = None
):
    """
    任意权限验证装饰器（需要任意一个权限）

    Args:
        permissions: 权限列表（拥有任意一个即可）
        check_ip: 是否检查IP白名单
        time_windows: 时间窗口限制
    """
    return require_permissions(
        permissions=permissions,
        logic=PermissionLogic.OR,
        check_ip=check_ip,
        time_windows=time_windows
    )


def require_roles(
    roles: List[str],
    logic: PermissionLogic = PermissionLogic.OR,
    check_ip: bool = False,
    time_windows: List[Dict[str, str]] = None
):
    """
    角色验证装饰器

    Args:
        roles: 必需的角色列表
        logic: 角色逻辑（AND/OR）
        check_ip: 是否检查IP白名单
        time_windows: 时间窗口限制
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象和用户
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')

            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=ErrorCode.UNAUTHORIZED.code,
                    detail=ErrorCode.UNAUTHORIZED.message
                )

            # IP白名单检查
            if check_ip and request:
                if not PermissionValidator._check_ip_whitelist(request):
                    raise HTTPException(
                        status_code=ErrorCode.IP_NOT_ALLOWED.code,
                        detail=ErrorCode.IP_NOT_ALLOWED.message
                    )

            # 时间窗口检查
            if time_windows:
                if not PermissionValidator._check_time_window(time_windows):
                    raise HTTPException(
                        status_code=ErrorCode.TIME_WINDOW_DENIED.code,
                        detail=ErrorCode.TIME_WINDOW_DENIED.message
                    )

            # 超级用户拥有所有角色
            if current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户角色
            user_roles = await current_user.get_role_codes()

            if logic == PermissionLogic.AND:
                # 需要所有角色
                missing_roles = [r for r in roles if r not in user_roles]
                if missing_roles:
                    raise HTTPException(
                        status_code=ErrorCode.ROLE_PERMISSION_DENIED.code,
                        detail=f"角色权限不足，缺少角色: {', '.join(missing_roles)}"
                    )
            else:
                # 需要任意角色
                has_role = any(r in user_roles for r in roles)
                if not has_role:
                    raise HTTPException(
                        status_code=ErrorCode.ROLE_PERMISSION_DENIED.code,
                        detail=f"角色权限不足，需要以下任意一个角色: {', '.join(roles)}"
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_superuser(
    check_ip: bool = False,
    time_windows: List[Dict[str, str]] = None
):
    """
    超级用户验证装饰器

    Args:
        check_ip: 是否检查IP白名单
        time_windows: 时间窗口限制
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象和用户
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')

            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=ErrorCode.UNAUTHORIZED.code,
                    detail=ErrorCode.UNAUTHORIZED.message
                )

            # IP白名单检查
            if check_ip and request:
                if not PermissionValidator._check_ip_whitelist(request):
                    raise HTTPException(
                        status_code=ErrorCode.IP_NOT_ALLOWED.code,
                        detail=ErrorCode.IP_NOT_ALLOWED.message
                    )

            # 时间窗口检查
            if time_windows:
                if not PermissionValidator._check_time_window(time_windows):
                    raise HTTPException(
                        status_code=ErrorCode.TIME_WINDOW_DENIED.code,
                        detail=ErrorCode.TIME_WINDOW_DENIED.message
                    )

            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=ErrorCode.FORBIDDEN.code,
                    detail="需要超级用户权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(roles: List[str]):
    """
    角色验证装饰器
    
    Args:
        roles: 必需的角色列表
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user or not isinstance(current_user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户"
                )
            
            # 超级用户拥有所有角色
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # 检查用户角色
            user_roles = await current_user.get_role_codes()
            has_role = any(role in user_roles for role in roles)
            
            if not has_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任意一个角色: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_superuser(func: Callable) -> Callable:
    """
    超级用户验证装饰器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从kwargs中获取current_user
        current_user = kwargs.get('current_user')
        if not current_user or not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证的用户"
            )
        
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，需要超级用户权限"
            )
        
        return await func(*args, **kwargs)
    return wrapper


async def check_user_permission(user: User, permission: str) -> bool:
    """
    检查用户是否拥有指定权限
    
    Args:
        user: 用户对象
        permission: 权限代码
        
    Returns:
        bool: 是否拥有权限
    """
    if user.is_superuser:
        return True
    
    return await user.has_permission(permission)


async def check_user_permissions(user: User, permissions: List[str]) -> bool:
    """
    检查用户是否拥有所有指定权限
    
    Args:
        user: 用户对象
        permissions: 权限代码列表
        
    Returns:
        bool: 是否拥有所有权限
    """
    if user.is_superuser:
        return True
    
    return await user.has_all_permissions(permissions)


async def check_user_any_permission(user: User, permissions: List[str]) -> bool:
    """
    检查用户是否拥有任意一个指定权限
    
    Args:
        user: 用户对象
        permissions: 权限代码列表
        
    Returns:
        bool: 是否拥有任意一个权限
    """
    if user.is_superuser:
        return True
    
    return await user.has_any_permission(permissions)


async def check_user_role(user: User, role: str) -> bool:
    """
    检查用户是否拥有指定角色
    
    Args:
        user: 用户对象
        role: 角色代码
        
    Returns:
        bool: 是否拥有角色
    """
    if user.is_superuser:
        return True
    
    return await user.has_role(role)


async def get_user_accessible_resources(
    user: User,
    resource_permissions: dict[str, List[str]]
) -> List[str]:
    """
    获取用户可访问的资源列表
    
    Args:
        user: 用户对象
        resource_permissions: 资源权限映射 {resource: [permissions]}
        
    Returns:
        List[str]: 可访问的资源列表
    """
    if user.is_superuser:
        return list(resource_permissions.keys())
    
    user_permissions = await user.get_permissions()
    accessible_resources = []
    
    for resource, permissions in resource_permissions.items():
        # 检查是否拥有该资源的任意一个权限
        if any(permission in user_permissions for permission in permissions):
            accessible_resources.append(resource)
    
    return accessible_resources


class PermissionCache:
    """权限缓存管理器"""

    def __init__(self):
        self._cache = {}
        self._cache_expire = {}

    def get(self, key: str):
        """获取缓存"""
        if key in self._cache:
            if time.time() < self._cache_expire.get(key, 0):
                return self._cache[key]
            else:
                # 缓存过期，清理
                self._cache.pop(key, None)
                self._cache_expire.pop(key, None)
        return None

    def set(self, key: str, value, expire_seconds: int = None):
        """设置缓存"""
        expire_seconds = expire_seconds or settings.PERMISSION_CACHE_EXPIRE
        self._cache[key] = value
        self._cache_expire[key] = time.time() + expire_seconds

    def clear(self, pattern: str = None):
        """清理缓存"""
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_expire.pop(key, None)
        else:
            self._cache.clear()
            self._cache_expire.clear()


# 全局权限缓存实例
permission_cache = PermissionCache()


class EnhancedPermissionChecker:
    """增强的权限检查器类"""

    def __init__(self, user: User, use_cache: bool = True):
        self.user = user
        self.use_cache = use_cache
        self._permissions_cache = None
        self._roles_cache = None

    def _get_cache_key(self, suffix: str) -> str:
        """生成缓存键"""
        return f"user:{self.user.id}:{suffix}"

    async def _get_permissions(self) -> List[str]:
        """获取用户权限（带缓存）"""
        if not self.use_cache:
            return await self.user.get_permissions()

        cache_key = self._get_cache_key("permissions")
        cached_permissions = permission_cache.get(cache_key)

        if cached_permissions is not None:
            return cached_permissions

        permissions = await self.user.get_permissions()
        permission_cache.set(cache_key, permissions)
        return permissions

    async def _get_roles(self) -> List[str]:
        """获取用户角色（带缓存）"""
        if not self.use_cache:
            return await self.user.get_role_codes()

        cache_key = self._get_cache_key("roles")
        cached_roles = permission_cache.get(cache_key)

        if cached_roles is not None:
            return cached_roles

        roles = await self.user.get_role_codes()
        permission_cache.set(cache_key, roles)
        return roles

    async def has_permission(self, permission: str) -> bool:
        """检查是否拥有权限"""
        if self.user.is_superuser:
            return True

        permissions = await self._get_permissions()
        return permission in permissions

    async def has_any_permission(self, permissions: List[str]) -> bool:
        """检查是否拥有任意权限"""
        if self.user.is_superuser:
            return True

        user_permissions = await self._get_permissions()
        return any(permission in user_permissions for permission in permissions)

    async def has_all_permissions(self, permissions: List[str]) -> bool:
        """检查是否拥有所有权限"""
        if self.user.is_superuser:
            return True

        user_permissions = await self._get_permissions()
        return all(permission in user_permissions for permission in permissions)

    async def has_role(self, role: str) -> bool:
        """检查是否拥有角色"""
        if self.user.is_superuser:
            return True

        roles = await self._get_roles()
        return role in roles

    async def has_any_role(self, roles: List[str]) -> bool:
        """检查是否拥有任意角色"""
        if self.user.is_superuser:
            return True

        user_roles = await self._get_roles()
        return any(role in user_roles for role in roles)

    async def has_all_roles(self, roles: List[str]) -> bool:
        """检查是否拥有所有角色"""
        if self.user.is_superuser:
            return True

        user_roles = await self._get_roles()
        return all(role in user_roles for role in roles)

    def clear_cache(self):
        """清理用户权限缓存"""
        if self.use_cache:
            permission_cache.clear(f"user:{self.user.id}")


# 兼容性别名
PermissionChecker = EnhancedPermissionChecker


# 便捷的权限检查函数
async def check_user_permission(user: User, permission: str, use_cache: bool = True) -> bool:
    """检查用户是否拥有指定权限"""
    checker = EnhancedPermissionChecker(user, use_cache)
    return await checker.has_permission(permission)


async def check_user_permissions(user: User, permissions: List[str], logic: PermissionLogic = PermissionLogic.AND, use_cache: bool = True) -> bool:
    """检查用户是否拥有指定权限"""
    checker = EnhancedPermissionChecker(user, use_cache)

    if logic == PermissionLogic.AND:
        return await checker.has_all_permissions(permissions)
    else:
        return await checker.has_any_permission(permissions)


async def check_user_any_permission(user: User, permissions: List[str], use_cache: bool = True) -> bool:
    """检查用户是否拥有任意一个指定权限"""
    checker = EnhancedPermissionChecker(user, use_cache)
    return await checker.has_any_permission(permissions)


async def check_user_role(user: User, role: str, use_cache: bool = True) -> bool:
    """检查用户是否拥有指定角色"""
    checker = EnhancedPermissionChecker(user, use_cache)
    return await checker.has_role(role)


async def check_user_roles(user: User, roles: List[str], logic: PermissionLogic = PermissionLogic.OR, use_cache: bool = True) -> bool:
    """检查用户是否拥有指定角色"""
    checker = EnhancedPermissionChecker(user, use_cache)

    if logic == PermissionLogic.AND:
        return await checker.has_all_roles(roles)
    else:
        return await checker.has_any_role(roles)


async def get_user_accessible_resources(
    user: User,
    resource_permissions: Dict[str, List[str]],
    use_cache: bool = True
) -> List[str]:
    """获取用户可访问的资源列表"""
    if user.is_superuser:
        return list(resource_permissions.keys())

    checker = EnhancedPermissionChecker(user, use_cache)
    user_permissions = await checker._get_permissions()
    accessible_resources = []

    for resource, permissions in resource_permissions.items():
        # 检查是否拥有该资源的任意一个权限
        if any(permission in user_permissions for permission in permissions):
            accessible_resources.append(resource)

    return accessible_resources


def clear_user_permission_cache(user_id: int):
    """清理指定用户的权限缓存"""
    permission_cache.clear(f"user:{user_id}")


def clear_all_permission_cache():
    """清理所有权限缓存"""
    permission_cache.clear()


# 装饰器快捷方法
def permission_required(*permissions, logic: PermissionLogic = PermissionLogic.AND, **kwargs):
    """权限验证装饰器快捷方法"""
    return require_permissions(list(permissions), logic=logic, **kwargs)


def any_permission_required(*permissions, **kwargs):
    """任意权限验证装饰器快捷方法"""
    return require_any_permission(list(permissions), **kwargs)


def role_required(*roles, logic: PermissionLogic = PermissionLogic.OR, **kwargs):
    """角色验证装饰器快捷方法"""
    return require_roles(list(roles), logic=logic, **kwargs)


def superuser_required(**kwargs):
    """超级用户验证装饰器快捷方法"""
    return require_superuser(**kwargs)


# 时间窗口配置示例
BUSINESS_HOURS = [
    {
        "weekdays": [0, 1, 2, 3, 4],  # 周一到周五
        "start_time": "09:00:00",
        "end_time": "18:00:00"
    }
]

WEEKEND_HOURS = [
    {
        "weekdays": [5, 6],  # 周六周日
        "start_time": "10:00:00",
        "end_time": "16:00:00"
    }
]

ALL_DAY = [
    {
        "start_time": "00:00:00",
        "end_time": "23:59:59"
    }
]
