"""
权限缓存模块
"""

import json
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict

from loguru import logger


@dataclass
class CachedPermission:
    """缓存的权限信息"""
    user_id: int
    permission_code: str
    has_permission: bool
    cached_at: float
    expires_at: float
    source: str  # 'role', 'direct', 'department'


@dataclass
class CachedUserPermissions:
    """缓存的用户权限集合"""
    user_id: int
    permissions: Set[str]
    roles: Set[str]
    department_ids: List[int]
    cached_at: float
    expires_at: float


class PermissionCache:
    """权限缓存管理器"""
    
    def __init__(self, default_ttl: int = 300):  # 默认5分钟TTL
        self.default_ttl = default_ttl
        
        # 权限缓存
        self.permission_cache: Dict[str, CachedPermission] = {}
        
        # 用户权限集合缓存
        self.user_permissions_cache: Dict[int, CachedUserPermissions] = {}
        
        # 角色权限缓存
        self.role_permissions_cache: Dict[str, Set[str]] = {}
        
        # 部门权限缓存
        self.department_cache: Dict[int, List[int]] = {}  # 部门ID -> 子部门ID列表
        
        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cache_size": 0,
        }
    
    def _generate_cache_key(self, user_id: int, permission_code: str) -> str:
        """生成缓存键"""
        return f"perm:{user_id}:{permission_code}"
    
    def _is_expired(self, expires_at: float) -> bool:
        """检查是否过期"""
        return time.time() > expires_at
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 清理权限缓存
        expired_keys = [
            key for key, perm in self.permission_cache.items()
            if self._is_expired(perm.expires_at)
        ]
        for key in expired_keys:
            del self.permission_cache[key]
            self.stats["evictions"] += 1
        
        # 清理用户权限集合缓存
        expired_users = [
            user_id for user_id, user_perms in self.user_permissions_cache.items()
            if self._is_expired(user_perms.expires_at)
        ]
        for user_id in expired_users:
            del self.user_permissions_cache[user_id]
            self.stats["evictions"] += 1
        
        # 更新缓存大小统计
        self.stats["cache_size"] = len(self.permission_cache) + len(self.user_permissions_cache)
    
    async def get_permission(self, user_id: int, permission_code: str) -> Optional[bool]:
        """获取缓存的权限"""
        self._cleanup_expired()
        
        cache_key = self._generate_cache_key(user_id, permission_code)
        
        if cache_key in self.permission_cache:
            cached_perm = self.permission_cache[cache_key]
            if not self._is_expired(cached_perm.expires_at):
                self.stats["hits"] += 1
                logger.debug(f"权限缓存命中: {user_id}:{permission_code}")
                return cached_perm.has_permission
        
        self.stats["misses"] += 1
        return None
    
    async def set_permission(
        self,
        user_id: int,
        permission_code: str,
        has_permission: bool,
        source: str = "unknown",
        ttl: Optional[int] = None
    ):
        """设置权限缓存"""
        if ttl is None:
            ttl = self.default_ttl
        
        current_time = time.time()
        cache_key = self._generate_cache_key(user_id, permission_code)
        
        cached_perm = CachedPermission(
            user_id=user_id,
            permission_code=permission_code,
            has_permission=has_permission,
            cached_at=current_time,
            expires_at=current_time + ttl,
            source=source
        )
        
        self.permission_cache[cache_key] = cached_perm
        logger.debug(f"权限缓存设置: {user_id}:{permission_code}={has_permission}")
    
    async def get_user_permissions(self, user_id: int) -> Optional[CachedUserPermissions]:
        """获取用户权限集合缓存"""
        self._cleanup_expired()
        
        if user_id in self.user_permissions_cache:
            cached_perms = self.user_permissions_cache[user_id]
            if not self._is_expired(cached_perms.expires_at):
                self.stats["hits"] += 1
                logger.debug(f"用户权限集合缓存命中: {user_id}")
                return cached_perms
        
        self.stats["misses"] += 1
        return None
    
    async def set_user_permissions(
        self,
        user_id: int,
        permissions: Set[str],
        roles: Set[str],
        department_ids: List[int],
        ttl: Optional[int] = None
    ):
        """设置用户权限集合缓存"""
        if ttl is None:
            ttl = self.default_ttl
        
        current_time = time.time()
        
        cached_perms = CachedUserPermissions(
            user_id=user_id,
            permissions=permissions,
            roles=roles,
            department_ids=department_ids,
            cached_at=current_time,
            expires_at=current_time + ttl
        )
        
        self.user_permissions_cache[user_id] = cached_perms
        logger.debug(f"用户权限集合缓存设置: {user_id}")
    
    async def get_role_permissions(self, role_code: str) -> Optional[Set[str]]:
        """获取角色权限缓存"""
        return self.role_permissions_cache.get(role_code)
    
    async def set_role_permissions(self, role_code: str, permissions: Set[str]):
        """设置角色权限缓存"""
        self.role_permissions_cache[role_code] = permissions
        logger.debug(f"角色权限缓存设置: {role_code}")
    
    async def get_department_hierarchy(self, department_id: int) -> Optional[List[int]]:
        """获取部门层级缓存"""
        return self.department_cache.get(department_id)
    
    async def set_department_hierarchy(self, department_id: int, child_dept_ids: List[int]):
        """设置部门层级缓存"""
        self.department_cache[department_id] = child_dept_ids
        logger.debug(f"部门层级缓存设置: {department_id}")
    
    async def invalidate_user(self, user_id: int):
        """使用户相关缓存失效"""
        # 清理用户权限集合缓存
        if user_id in self.user_permissions_cache:
            del self.user_permissions_cache[user_id]
            logger.debug(f"用户权限集合缓存失效: {user_id}")
        
        # 清理用户相关的权限缓存
        keys_to_remove = [
            key for key in self.permission_cache.keys()
            if key.startswith(f"perm:{user_id}:")
        ]
        for key in keys_to_remove:
            del self.permission_cache[key]
        
        logger.debug(f"用户权限缓存失效: {user_id}")
    
    async def invalidate_role(self, role_code: str):
        """使角色相关缓存失效"""
        # 清理角色权限缓存
        if role_code in self.role_permissions_cache:
            del self.role_permissions_cache[role_code]
            logger.debug(f"角色权限缓存失效: {role_code}")
        
        # 清理所有用户权限集合缓存（因为角色变更影响所有用户）
        self.user_permissions_cache.clear()
        logger.debug("所有用户权限集合缓存失效（角色变更）")
    
    async def invalidate_department(self, department_id: int):
        """使部门相关缓存失效"""
        # 清理部门层级缓存
        if department_id in self.department_cache:
            del self.department_cache[department_id]
            logger.debug(f"部门层级缓存失效: {department_id}")
        
        # 清理相关用户的权限缓存
        # 这里需要根据实际业务逻辑来确定哪些用户受影响
        # 为简化，清理所有用户权限集合缓存
        self.user_permissions_cache.clear()
        logger.debug("所有用户权限集合缓存失效（部门变更）")
    
    async def clear_all(self):
        """清空所有缓存"""
        self.permission_cache.clear()
        self.user_permissions_cache.clear()
        self.role_permissions_cache.clear()
        self.department_cache.clear()
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cache_size": 0,
        }
        
        logger.info("所有权限缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        self._cleanup_expired()
        
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": round(hit_rate, 4),
            "cache_sizes": {
                "permissions": len(self.permission_cache),
                "user_permissions": len(self.user_permissions_cache),
                "role_permissions": len(self.role_permissions_cache),
                "departments": len(self.department_cache),
            },
            "total_cache_size": (
                len(self.permission_cache) + 
                len(self.user_permissions_cache) + 
                len(self.role_permissions_cache) + 
                len(self.department_cache)
            )
        }


# 全局权限缓存实例
permission_cache = PermissionCache()


def get_permission_cache() -> PermissionCache:
    """获取权限缓存实例"""
    return permission_cache


# 缓存装饰器
def cache_permission(ttl: int = 300):
    """权限缓存装饰器"""
    def decorator(func):
        async def wrapper(user_id: int, permission_code: str, *args, **kwargs):
            cache = get_permission_cache()
            
            # 尝试从缓存获取
            cached_result = await cache.get_permission(user_id, permission_code)
            if cached_result is not None:
                return cached_result
            
            # 调用原函数
            result = await func(user_id, permission_code, *args, **kwargs)
            
            # 设置缓存
            await cache.set_permission(user_id, permission_code, result, ttl=ttl)
            
            return result
        
        return wrapper
    
    return decorator
