"""
多层缓存策略管理器
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from app.core.redis_cache import get_redis_cache, CacheConfig, SerializationType
from app.core.permission_cache import get_permission_cache


class CacheLevel(str, Enum):
    """缓存层级"""
    L1_MEMORY = "l1_memory"  # 内存缓存（最快）
    L2_REDIS = "l2_redis"    # Redis缓存（中等）
    L3_DATABASE = "l3_database"  # 数据库（最慢）


@dataclass
class CacheLevelConfig:
    """缓存层级配置"""
    enabled: bool = True
    ttl: int = 3600
    max_size: Optional[int] = None
    eviction_policy: str = "lru"  # lru, lfu, fifo


@dataclass
class MultiLevelCacheConfig:
    """多层缓存配置"""
    # 缓存策略
    write_through: bool = True  # 写穿透
    write_back: bool = False    # 写回
    read_through: bool = True   # 读穿透

    def __post_init__(self):
        """初始化后设置默认配置"""
        self.l1_config = CacheLevelConfig(ttl=300, max_size=1000)  # 5分钟，1000个键
        self.l2_config = CacheLevelConfig(ttl=3600)  # 1小时
        self.l3_config = CacheLevelConfig(ttl=86400)  # 24小时


class MultiLevelCacheManager:
    """多层缓存管理器"""
    
    def __init__(self, config: MultiLevelCacheConfig = None):
        self.config = config or MultiLevelCacheConfig()
        
        # L1缓存（内存）
        self.l1_cache: Dict[str, Dict[str, Any]] = {}
        self.l1_access_times: Dict[str, float] = {}
        self.l1_access_counts: Dict[str, int] = {}
        
        # 缓存统计
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l3_hits": 0,
            "l3_misses": 0,
            "total_operations": 0,
            "cache_promotions": 0,  # 缓存提升次数
            "cache_evictions": 0,   # 缓存驱逐次数
        }
    
    def _generate_l1_key(self, key: str, namespace: str) -> str:
        """生成L1缓存键"""
        return f"{namespace}:{key}"
    
    def _is_l1_expired(self, cache_data: Dict[str, Any]) -> bool:
        """检查L1缓存是否过期"""
        return time.time() > cache_data.get("expires_at", 0)
    
    def _evict_l1_cache(self):
        """L1缓存驱逐"""
        if not self.config.l1_config.max_size:
            return
        
        current_size = len(self.l1_cache)
        if current_size <= self.config.l1_config.max_size:
            return
        
        # 计算需要驱逐的数量
        evict_count = current_size - self.config.l1_config.max_size + 1
        
        # 根据驱逐策略选择要删除的键
        if self.config.l1_config.eviction_policy == "lru":
            # 最近最少使用
            sorted_keys = sorted(
                self.l1_access_times.items(),
                key=lambda x: x[1]
            )
        elif self.config.l1_config.eviction_policy == "lfu":
            # 最少使用频率
            sorted_keys = sorted(
                self.l1_access_counts.items(),
                key=lambda x: x[1]
            )
        else:  # fifo
            # 先进先出
            sorted_keys = list(self.l1_cache.items())
        
        # 删除最旧的键
        for i in range(min(evict_count, len(sorted_keys))):
            key_to_evict = sorted_keys[i][0]
            self.l1_cache.pop(key_to_evict, None)
            self.l1_access_times.pop(key_to_evict, None)
            self.l1_access_counts.pop(key_to_evict, None)
            self.stats["cache_evictions"] += 1
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """多层缓存获取"""
        self.stats["total_operations"] += 1
        l1_key = self._generate_l1_key(key, namespace)
        
        # L1缓存查找
        if self.config.l1_config.enabled and l1_key in self.l1_cache:
            cache_data = self.l1_cache[l1_key]
            if not self._is_l1_expired(cache_data):
                # 更新访问统计
                self.l1_access_times[l1_key] = time.time()
                self.l1_access_counts[l1_key] = self.l1_access_counts.get(l1_key, 0) + 1
                
                self.stats["l1_hits"] += 1
                logger.debug(f"L1缓存命中: {namespace}:{key}")
                return cache_data["value"]
            else:
                # L1缓存过期，删除
                self.l1_cache.pop(l1_key, None)
                self.l1_access_times.pop(l1_key, None)
                self.l1_access_counts.pop(l1_key, None)
        
        self.stats["l1_misses"] += 1
        
        # L2缓存查找（Redis）
        if self.config.l2_config.enabled:
            try:
                redis_cache = await get_redis_cache()
                l2_value = await redis_cache.get(key, namespace)
                
                if l2_value is not None:
                    self.stats["l2_hits"] += 1
                    logger.debug(f"L2缓存命中: {namespace}:{key}")
                    
                    # 提升到L1缓存
                    if self.config.l1_config.enabled:
                        await self._promote_to_l1(key, namespace, l2_value)
                    
                    return l2_value
                
            except Exception as e:
                logger.error(f"L2缓存查询失败: {namespace}:{key} - {e}")
        
        self.stats["l2_misses"] += 1
        
        # 如果启用了读穿透，这里可以调用数据源获取数据
        # 这里返回None，由调用方处理数据源查询
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default",
        levels: List[CacheLevel] = None
    ) -> bool:
        """多层缓存设置"""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        success = True
        
        # L1缓存设置
        if CacheLevel.L1_MEMORY in levels and self.config.l1_config.enabled:
            l1_ttl = ttl or self.config.l1_config.ttl
            l1_key = self._generate_l1_key(key, namespace)
            
            cache_data = {
                "value": value,
                "cached_at": time.time(),
                "expires_at": time.time() + l1_ttl,
                "ttl": l1_ttl
            }
            
            self.l1_cache[l1_key] = cache_data
            self.l1_access_times[l1_key] = time.time()
            self.l1_access_counts[l1_key] = 1
            
            # 检查是否需要驱逐
            self._evict_l1_cache()
            
            logger.debug(f"L1缓存设置: {namespace}:{key}")
        
        # L2缓存设置（Redis）
        if CacheLevel.L2_REDIS in levels and self.config.l2_config.enabled:
            try:
                redis_cache = await get_redis_cache()
                l2_ttl = ttl or self.config.l2_config.ttl
                
                l2_success = await redis_cache.set(key, value, l2_ttl, namespace)
                if not l2_success:
                    success = False
                    logger.warning(f"L2缓存设置失败: {namespace}:{key}")
                else:
                    logger.debug(f"L2缓存设置: {namespace}:{key}")
                
            except Exception as e:
                logger.error(f"L2缓存设置失败: {namespace}:{key} - {e}")
                success = False
        
        return success
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """多层缓存删除"""
        success = True
        l1_key = self._generate_l1_key(key, namespace)
        
        # L1缓存删除
        if l1_key in self.l1_cache:
            self.l1_cache.pop(l1_key, None)
            self.l1_access_times.pop(l1_key, None)
            self.l1_access_counts.pop(l1_key, None)
            logger.debug(f"L1缓存删除: {namespace}:{key}")
        
        # L2缓存删除（Redis）
        try:
            redis_cache = await get_redis_cache()
            l2_success = await redis_cache.delete(key, namespace)
            if not l2_success:
                success = False
            else:
                logger.debug(f"L2缓存删除: {namespace}:{key}")
                
        except Exception as e:
            logger.error(f"L2缓存删除失败: {namespace}:{key} - {e}")
            success = False
        
        return success
    
    async def _promote_to_l1(self, key: str, namespace: str, value: Any):
        """提升到L1缓存"""
        if not self.config.l1_config.enabled:
            return
        
        l1_key = self._generate_l1_key(key, namespace)
        cache_data = {
            "value": value,
            "cached_at": time.time(),
            "expires_at": time.time() + self.config.l1_config.ttl,
            "ttl": self.config.l1_config.ttl
        }
        
        self.l1_cache[l1_key] = cache_data
        self.l1_access_times[l1_key] = time.time()
        self.l1_access_counts[l1_key] = 1
        
        self.stats["cache_promotions"] += 1
        self._evict_l1_cache()
    
    async def clear_namespace(self, namespace: str) -> int:
        """清空命名空间缓存"""
        cleared_count = 0
        
        # 清空L1缓存
        l1_keys_to_remove = [
            key for key in self.l1_cache.keys()
            if key.startswith(f"{namespace}:")
        ]
        
        for key in l1_keys_to_remove:
            self.l1_cache.pop(key, None)
            self.l1_access_times.pop(key, None)
            self.l1_access_counts.pop(key, None)
            cleared_count += 1
        
        # 清空L2缓存
        try:
            redis_cache = await get_redis_cache()
            l2_cleared = await redis_cache.clear_namespace(namespace)
            cleared_count += l2_cleared
            
        except Exception as e:
            logger.error(f"清空L2缓存失败: {namespace} - {e}")
        
        logger.info(f"清空多层缓存命名空间: {namespace}, 清理 {cleared_count} 个键")
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"]
        total_misses = self.stats["l1_misses"] + self.stats["l2_misses"]
        total_requests = total_hits + total_misses
        
        return {
            "l1_stats": {
                "hits": self.stats["l1_hits"],
                "misses": self.stats["l1_misses"],
                "hit_rate": self.stats["l1_hits"] / max(self.stats["l1_hits"] + self.stats["l1_misses"], 1),
                "size": len(self.l1_cache),
                "max_size": self.config.l1_config.max_size
            },
            "l2_stats": {
                "hits": self.stats["l2_hits"],
                "misses": self.stats["l2_misses"],
                "hit_rate": self.stats["l2_hits"] / max(self.stats["l2_hits"] + self.stats["l2_misses"], 1)
            },
            "overall_stats": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "overall_hit_rate": total_hits / max(total_requests, 1),
                "total_operations": self.stats["total_operations"],
                "cache_promotions": self.stats["cache_promotions"],
                "cache_evictions": self.stats["cache_evictions"]
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "l1_cache": {
                "status": "healthy" if self.config.l1_config.enabled else "disabled",
                "size": len(self.l1_cache)
            },
            "l2_cache": {
                "status": "unknown",
                "connected": False
            }
        }
        
        # 检查L2缓存（Redis）
        if self.config.l2_config.enabled:
            try:
                redis_cache = await get_redis_cache()
                redis_health = await redis_cache.health_check()
                health_status["l2_cache"] = redis_health
                
            except Exception as e:
                health_status["l2_cache"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "connected": False
                }
        
        # 整体状态
        overall_healthy = (
            health_status["l1_cache"]["status"] in ["healthy", "disabled"] and
            health_status["l2_cache"]["status"] in ["healthy", "disabled"]
        )
        
        health_status["overall"] = {
            "status": "healthy" if overall_healthy else "unhealthy"
        }
        
        return health_status


# 全局多层缓存管理器实例
multi_level_cache_manager = MultiLevelCacheManager()


def get_multi_level_cache() -> MultiLevelCacheManager:
    """获取多层缓存管理器实例"""
    return multi_level_cache_manager


# 多层缓存装饰器
def multi_level_cache(
    ttl: int = 3600,
    namespace: str = "default",
    levels: List[CacheLevel] = None,
    key_func: Optional[Callable] = None
):
    """多层缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            cache = get_multi_level_cache()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
                cache_key = ":".join(key_parts)
            
            # 尝试从多层缓存获取
            cached_result = await cache.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # 调用原函数
            result = await func(*args, **kwargs)
            
            # 设置多层缓存
            await cache.set(cache_key, result, ttl, namespace, levels)
            
            return result
        
        return wrapper
    
    return decorator
