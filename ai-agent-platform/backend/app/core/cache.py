# Copyright (c) 2025 左岚. All rights reserved.
"""
Redis缓存管理器 - 高性能缓存层实现
"""

# # Standard library imports
import asyncio
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import logging
import pickle
import time
from typing import Any, Dict, List, Optional, Union

# # Third-party imports
try:
    import redis
    from redis.connection import ConnectionPool
    from redis.sentinel import Sentinel
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None
    Sentinel = None

# # Local application imports
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器 - 支持同步和异步操作"""
    
    def __init__(self):
        self._sync_client = None
        self._async_client = None
        self._connection_pool = None
        self._sentinel = None
        self._is_cluster = False
        self._redis_available = REDIS_AVAILABLE
        self._memory_cache = {}  # 内存缓存作为后备
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    def _create_connection_pool(self) -> ConnectionPool:
        """创建Redis连接池"""
        try:
            # 解析Redis URL
            # # Standard library imports
            import urllib.parse
            parsed = urllib.parse.urlparse(settings.REDIS_URL)
            
            pool = ConnectionPool(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                password=parsed.password,
                db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                max_connections=50,  # 最大连接数
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,  # 健康检查间隔
                decode_responses=True,
                encoding='utf-8'
            )
            logger.info("Redis连接池创建成功")
            return pool
        except Exception as e:
            logger.error(f"Redis连接池创建失败: {e}")
            raise
    
    @property
    def sync_client(self) -> redis.Redis:
        """获取同步Redis客户端"""
        if self._sync_client is None:
            if self._connection_pool is None:
                self._connection_pool = self._create_connection_pool()
            self._sync_client = redis.Redis(connection_pool=self._connection_pool)
        return self._sync_client
    
    async def async_client(self) -> aioredis.Redis:
        """获取异步Redis客户端"""
        if self._async_client is None:
            try:
                self._async_client = await aioredis.from_url(
                    settings.REDIS_URL,
                    max_connections=50,
                    retry_on_timeout=True,
                    decode_responses=True,
                    encoding='utf-8'
                )
                logger.info("异步Redis客户端创建成功")
            except Exception as e:
                logger.error(f"异步Redis客户端创建失败: {e}")
                raise
        return self._async_client
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        else:
            # 复杂对象使用pickle序列化
            return pickle.dumps(value).hex()
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化值"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            try:
                # 尝试pickle反序列化
                return pickle.loads(bytes.fromhex(value))
            except Exception:
                return value
    
    def _generate_key(self, key: str, prefix: str = "ai_platform") -> str:
        """生成缓存键"""
        return f"{prefix}:{key}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "ai_platform") -> bool:
        """设置缓存值"""
        try:
            cache_key = self._generate_key(key, prefix)

            if self._redis_available:
                serialized_value = self._serialize_value(value)

                if ttl:
                    result = self.sync_client.setex(cache_key, ttl, serialized_value)
                else:
                    result = self.sync_client.set(cache_key, serialized_value)

                if result:
                    self._stats['sets'] += 1
                    logger.debug(f"缓存设置成功: {cache_key}")
                return bool(result)
            else:
                # 使用内存缓存
                self._memory_cache[cache_key] = {
                    'value': value,
                    'expires': time.time() + ttl if ttl else None
                }
                self._stats['sets'] += 1
                return True

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存设置失败: {key}, 错误: {e}")
            # 降级到内存缓存
            try:
                cache_key = self._generate_key(key, prefix)
                self._memory_cache[cache_key] = {
                    'value': value,
                    'expires': time.time() + ttl if ttl else None
                }
                return True
            except:
                return False
    
    def get(self, key: str, default: Any = None, prefix: str = "ai_platform") -> Any:
        """获取缓存值"""
        try:
            cache_key = self._generate_key(key, prefix)
            value = self.sync_client.get(cache_key)
            
            if value is not None:
                self._stats['hits'] += 1
                logger.debug(f"缓存命中: {cache_key}")
                return self._deserialize_value(value)
            else:
                self._stats['misses'] += 1
                logger.debug(f"缓存未命中: {cache_key}")
                return default
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存获取失败: {key}, 错误: {e}")
            return default
    
    def delete(self, key: str, prefix: str = "ai_platform") -> bool:
        """删除缓存"""
        try:
            cache_key = self._generate_key(key, prefix)
            result = self.sync_client.delete(cache_key)
            if result:
                self._stats['deletes'] += 1
                logger.debug(f"缓存删除成功: {cache_key}")
            return bool(result)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存删除失败: {key}, 错误: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "ai_platform") -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = self._generate_key(key, prefix)
            return bool(self.sync_client.exists(cache_key))
        except Exception as e:
            logger.error(f"缓存存在检查失败: {key}, 错误: {e}")
            return False
    
    def expire(self, key: str, ttl: int, prefix: str = "ai_platform") -> bool:
        """设置缓存过期时间"""
        try:
            cache_key = self._generate_key(key, prefix)
            return bool(self.sync_client.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"缓存过期设置失败: {key}, 错误: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = self.sync_client.info()
            pool_stats = self._connection_pool.connection_kwargs if self._connection_pool else {}
            
            return {
                'cache_stats': self._stats.copy(),
                'redis_info': {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                },
                'connection_pool': {
                    'max_connections': pool_stats.get('max_connections', 0),
                    'created_connections': getattr(self._connection_pool, 'created_connections', 0) if self._connection_pool else 0,
                }
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {'error': str(e)}
    
    def clear_pattern(self, pattern: str, prefix: str = "ai_platform") -> int:
        """清除匹配模式的缓存"""
        try:
            cache_pattern = self._generate_key(pattern, prefix)
            keys = self.sync_client.keys(cache_pattern)
            if keys:
                deleted = self.sync_client.delete(*keys)
                self._stats['deletes'] += deleted
                logger.info(f"清除缓存模式 {cache_pattern}: {deleted} 个键")
                return deleted
            return 0
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"清除缓存模式失败: {pattern}, 错误: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试连接
            start_time = datetime.now()
            self.sync_client.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """关闭连接"""
        try:
            if self._sync_client:
                self._sync_client.close()
            if self._connection_pool:
                self._connection_pool.disconnect()
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")


def cache_result(ttl: int = 3600, prefix: str = "cache"):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, prefix=prefix)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl, prefix=prefix)
            return result
        return wrapper
    return decorator


# 全局缓存管理器实例
cache_manager = CacheManager()
