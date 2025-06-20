"""
缓存管理器
提供Redis缓存的统一管理和优化策略
"""

import asyncio
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheException(Exception):
    """缓存异常"""
    pass


class CacheManager:
    """
    缓存管理器
    
    主要功能：
    - Redis连接管理
    - 多级缓存策略
    - 缓存预热和失效
    - 性能监控和统计
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,
        max_connections: int = 20
    ):
        """
        初始化缓存管理器
        
        Args:
            redis_url: Redis连接URL
            default_ttl: 默认过期时间（秒）
            max_connections: 最大连接数
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.redis_client: Optional[Redis] = None
        self._connected = False
        
        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        
        # 缓存键前缀
        self.key_prefixes = {
            "chat": "chat:",
            "knowledge": "kb:",
            "model": "model:",
            "user": "user:",
            "session": "session:",
            "search": "search:",
            "embedding": "emb:",
            "graph": "graph:"
        }
        
        logger.info(f"缓存管理器初始化: {redis_url}")
    
    async def connect(self):
        """连接到Redis"""
        try:
            if self._connected and self.redis_client:
                return
            
            self.redis_client = redis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=False,  # 保持二进制数据
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            
            self._connected = True
            logger.info("✅ Redis连接成功")
            
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {str(e)}")
            raise CacheException(f"Redis连接失败: {str(e)}")
    
    async def disconnect(self):
        """断开连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis连接已断开")
    
    def _generate_key(self, category: str, key: str) -> str:
        """生成缓存键"""
        prefix = self.key_prefixes.get(category, "default:")
        return f"{prefix}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """序列化值"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return json.dumps(value).encode('utf-8')
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"序列化失败: {str(e)}")
            raise CacheException(f"序列化失败: {str(e)}")
    
    def _deserialize_value(self, data: bytes) -> Any:
        """反序列化值"""
        try:
            # 尝试JSON反序列化
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 使用pickle反序列化
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"反序列化失败: {str(e)}")
            raise CacheException(f"反序列化失败: {str(e)}")
    
    async def _ensure_connected(self):
        """确保连接已建立"""
        if not self._connected:
            await self.connect()
    
    async def get(
        self,
        category: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取缓存值
        
        Args:
            category: 缓存分类
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        try:
            await self._ensure_connected()
            
            cache_key = self._generate_key(category, key)
            data = await self.redis_client.get(cache_key)
            
            if data is not None:
                self.stats["hits"] += 1
                value = self._deserialize_value(data)
                logger.debug(f"缓存命中: {cache_key}")
                return value
            else:
                self.stats["misses"] += 1
                logger.debug(f"缓存未命中: {cache_key}")
                return default
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"获取缓存失败: {str(e)}")
            return default
    
    async def set(
        self,
        category: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            category: 缓存分类
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            设置是否成功
        """
        try:
            await self._ensure_connected()
            
            cache_key = self._generate_key(category, key)
            serialized_value = self._serialize_value(value)
            
            ttl = ttl or self.default_ttl
            
            result = await self.redis_client.setex(
                cache_key,
                ttl,
                serialized_value
            )
            
            if result:
                self.stats["sets"] += 1
                logger.debug(f"缓存设置成功: {cache_key}, TTL: {ttl}")
                return True
            else:
                logger.warning(f"缓存设置失败: {cache_key}")
                return False
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"设置缓存失败: {str(e)}")
            return False
    
    async def delete(self, category: str, key: str) -> bool:
        """
        删除缓存
        
        Args:
            category: 缓存分类
            key: 缓存键
            
        Returns:
            删除是否成功
        """
        try:
            await self._ensure_connected()
            
            cache_key = self._generate_key(category, key)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                self.stats["deletes"] += 1
                logger.debug(f"缓存删除成功: {cache_key}")
                return True
            else:
                logger.debug(f"缓存键不存在: {cache_key}")
                return False
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"删除缓存失败: {str(e)}")
            return False
    
    async def exists(self, category: str, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            category: 缓存分类
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            await self._ensure_connected()
            
            cache_key = self._generate_key(category, key)
            result = await self.redis_client.exists(cache_key)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {str(e)}")
            return False
    
    async def expire(self, category: str, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            category: 缓存分类
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            设置是否成功
        """
        try:
            await self._ensure_connected()
            
            cache_key = self._generate_key(category, key)
            result = await self.redis_client.expire(cache_key, ttl)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"设置缓存过期时间失败: {str(e)}")
            return False
    
    async def clear_category(self, category: str) -> int:
        """
        清空指定分类的所有缓存
        
        Args:
            category: 缓存分类
            
        Returns:
            删除的键数量
        """
        try:
            await self._ensure_connected()
            
            prefix = self.key_prefixes.get(category, "default:")
            pattern = f"{prefix}*"
            
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"清空缓存分类 {category}: 删除 {deleted} 个键")
                return deleted
            else:
                logger.info(f"缓存分类 {category} 无数据")
                return 0
                
        except Exception as e:
            logger.error(f"清空缓存分类失败: {str(e)}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            await self._ensure_connected()
            
            # Redis信息
            redis_info = await self.redis_client.info()
            
            # 计算命中率
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_stats": {
                    **self.stats,
                    "hit_rate": round(hit_rate, 2),
                    "total_requests": total_requests
                },
                "redis_info": {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    "total_commands_processed": redis_info.get("total_commands_processed", 0)
                },
                "connection_info": {
                    "connected": self._connected,
                    "redis_url": self.redis_url,
                    "max_connections": self.max_connections
                }
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {
                "cache_stats": self.stats,
                "redis_info": {},
                "connection_info": {
                    "connected": self._connected,
                    "error": str(e)
                }
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            await self._ensure_connected()
            
            start_time = datetime.now()
            
            # 测试基本操作
            test_key = "health_check"
            test_value = {"timestamp": datetime.now().isoformat()}
            
            # 设置测试值
            await self.set("test", test_key, test_value, ttl=60)
            
            # 获取测试值
            retrieved_value = await self.get("test", test_key)
            
            # 删除测试值
            await self.delete("test", test_key)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            success = retrieved_value is not None and retrieved_value.get("timestamp") == test_value["timestamp"]
            
            return {
                "status": "healthy" if success else "unhealthy",
                "response_time": response_time,
                "test_passed": success,
                "connected": self._connected,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"缓存健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": self._connected,
                "timestamp": datetime.now().isoformat()
            }


# 全局缓存管理器实例
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    global cache_manager
    
    if cache_manager is None:
        import os
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))
        max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        
        cache_manager = CacheManager(
            redis_url=redis_url,
            default_ttl=default_ttl,
            max_connections=max_connections
        )
    
    return cache_manager


async def initialize_cache_manager():
    """初始化缓存管理器"""
    manager = get_cache_manager()
    await manager.connect()
    return manager
