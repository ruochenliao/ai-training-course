"""
Redis缓存管理器
"""

import json
import pickle
import time
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from loguru import logger

from app.core.config import settings


class CacheStrategy(str, Enum):
    """缓存策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    TTL = "ttl"  # 基于时间过期
    WRITE_THROUGH = "write_through"  # 写穿透
    WRITE_BACK = "write_back"  # 写回


class SerializationType(str, Enum):
    """序列化类型"""
    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600  # 默认1小时
    strategy: CacheStrategy = CacheStrategy.TTL
    serialization: SerializationType = SerializationType.JSON
    max_size: Optional[int] = None
    namespace: str = "default"


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_operations: int = 0
    hit_rate: float = 0.0
    memory_usage: int = 0


class RedisCacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
        
        # 缓存配置
        self.default_config = CacheConfig()
        self.namespace_configs: Dict[str, CacheConfig] = {}
        
        # 统计信息
        self.stats = CacheStats()
        
        # 序列化器
        self.serializers = {
            SerializationType.JSON: self._json_serializer,
            SerializationType.PICKLE: self._pickle_serializer,
            SerializationType.STRING: self._string_serializer,
        }
        
        # 反序列化器
        self.deserializers = {
            SerializationType.JSON: self._json_deserializer,
            SerializationType.PICKLE: self._pickle_deserializer,
            SerializationType.STRING: self._string_deserializer,
        }
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # 处理二进制数据
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            self.connected = True
            
            logger.info(f"Redis缓存连接成功: {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Redis缓存连接失败: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Redis缓存连接已断开")
    
    def _generate_key(self, key: str, namespace: str = "default") -> str:
        """生成缓存键"""
        return f"cache:{namespace}:{key}"
    
    def _json_serializer(self, data: Any) -> bytes:
        """JSON序列化"""
        return json.dumps(data, ensure_ascii=False).encode('utf-8')
    
    def _json_deserializer(self, data: bytes) -> Any:
        """JSON反序列化"""
        return json.loads(data.decode('utf-8'))
    
    def _pickle_serializer(self, data: Any) -> bytes:
        """Pickle序列化"""
        return pickle.dumps(data)
    
    def _pickle_deserializer(self, data: bytes) -> Any:
        """Pickle反序列化"""
        return pickle.loads(data)
    
    def _string_serializer(self, data: Any) -> bytes:
        """字符串序列化"""
        return str(data).encode('utf-8')
    
    def _string_deserializer(self, data: bytes) -> Any:
        """字符串反序列化"""
        return data.decode('utf-8')
    
    def get_config(self, namespace: str = "default") -> CacheConfig:
        """获取命名空间配置"""
        return self.namespace_configs.get(namespace, self.default_config)
    
    def set_config(self, namespace: str, config: CacheConfig):
        """设置命名空间配置"""
        self.namespace_configs[namespace] = config
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """获取缓存值"""
        if not self.connected:
            return None
        
        try:
            config = self.get_config(namespace)
            cache_key = self._generate_key(key, namespace)
            
            # 获取数据
            data = await self.redis_client.get(cache_key)
            
            if data is None:
                self.stats.misses += 1
                self.stats.total_operations += 1
                self._update_hit_rate()
                return None
            
            # 反序列化
            deserializer = self.deserializers[config.serialization]
            result = deserializer(data)
            
            self.stats.hits += 1
            self.stats.total_operations += 1
            self._update_hit_rate()
            
            logger.debug(f"缓存命中: {namespace}:{key}")
            return result
            
        except Exception as e:
            logger.error(f"获取缓存失败: {namespace}:{key} - {e}")
            self.stats.misses += 1
            self.stats.total_operations += 1
            self._update_hit_rate()
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """设置缓存值"""
        if not self.connected:
            return False
        
        try:
            config = self.get_config(namespace)
            cache_key = self._generate_key(key, namespace)
            
            # 序列化数据
            serializer = self.serializers[config.serialization]
            data = serializer(value)
            
            # 设置TTL
            expire_time = ttl or config.ttl
            
            # 存储数据
            await self.redis_client.setex(cache_key, expire_time, data)
            
            self.stats.sets += 1
            self.stats.total_operations += 1
            
            logger.debug(f"缓存设置: {namespace}:{key}, TTL: {expire_time}s")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {namespace}:{key} - {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """删除缓存"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_key(key, namespace)
            result = await self.redis_client.delete(cache_key)
            
            if result > 0:
                self.stats.deletes += 1
                self.stats.total_operations += 1
                logger.debug(f"缓存删除: {namespace}:{key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除缓存失败: {namespace}:{key} - {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """检查缓存是否存在"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_key(key, namespace)
            result = await self.redis_client.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {namespace}:{key} - {e}")
            return False
    
    async def expire(self, key: str, ttl: int, namespace: str = "default") -> bool:
        """设置缓存过期时间"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_key(key, namespace)
            result = await self.redis_client.expire(cache_key, ttl)
            return result
            
        except Exception as e:
            logger.error(f"设置缓存过期时间失败: {namespace}:{key} - {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """清空命名空间下的所有缓存"""
        if not self.connected:
            return 0
        
        try:
            pattern = f"cache:{namespace}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                self.stats.total_operations += deleted
                logger.info(f"清空命名空间缓存: {namespace}, 删除 {deleted} 个键")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"清空命名空间缓存失败: {namespace} - {e}")
            return 0
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        if not self.connected:
            return {}
        
        try:
            info = await self.redis_client.info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "memory_fragmentation_ratio": info.get("memory_fragmentation_ratio", 0),
            }
            
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {e}")
            return {}
    
    def _update_hit_rate(self):
        """更新命中率"""
        total = self.stats.hits + self.stats.misses
        if total > 0:
            self.stats.hit_rate = self.stats.hits / total
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_info = await self.get_memory_usage()
        
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "sets": self.stats.sets,
            "deletes": self.stats.deletes,
            "evictions": self.stats.evictions,
            "total_operations": self.stats.total_operations,
            "hit_rate": round(self.stats.hit_rate, 4),
            "connected": self.connected,
            "memory_usage": memory_info,
            "namespaces": list(self.namespace_configs.keys())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.connected:
                return {"status": "disconnected", "error": "Redis未连接"}
            
            start_time = time.time()
            await self.redis_client.ping()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": round(response_time, 3),
                "connected": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }


# 全局Redis缓存管理器实例
redis_cache_manager = RedisCacheManager()


async def get_redis_cache() -> RedisCacheManager:
    """获取Redis缓存管理器实例"""
    if not redis_cache_manager.connected:
        await redis_cache_manager.connect()
    return redis_cache_manager


# 缓存装饰器
def redis_cache(
    ttl: int = 3600,
    namespace: str = "default",
    key_func: Optional[Callable] = None
):
    """Redis缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            cache = await get_redis_cache()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
                cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            cached_result = await cache.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # 调用原函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            await cache.set(cache_key, result, ttl, namespace)
            
            return result
        
        return wrapper
    
    return decorator
