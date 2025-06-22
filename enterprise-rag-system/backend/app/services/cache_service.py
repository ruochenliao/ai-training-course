"""
智能缓存优化服务
"""

import asyncio
import json
import pickle
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

import redis.asyncio as redis
from app.core.config import settings
from loguru import logger

from app.core.exceptions import CacheException


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    TTL = "ttl"  # 时间过期
    WRITE_THROUGH = "write_through"  # 写穿透
    WRITE_BACK = "write_back"  # 写回
    REFRESH_AHEAD = "refresh_ahead"  # 预刷新


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"  # 内存缓存
    L2_REDIS = "l2_redis"    # Redis缓存
    L3_DISK = "l3_disk"      # 磁盘缓存


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600  # 默认1小时过期
    max_size: int = 1000  # 最大缓存条目数
    strategy: CacheStrategy = CacheStrategy.LRU
    levels: List[CacheLevel] = None
    compress: bool = False
    serialize_method: str = "json"  # json, pickle
    
    def __post_init__(self):
        if self.levels is None:
            self.levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class CacheService:
    """智能缓存服务类"""
    
    def __init__(self):
        """初始化缓存服务"""
        self.redis_client = None
        self.memory_cache = {}  # L1内存缓存
        self.cache_stats = {}  # 各缓存区域的统计
        self.access_patterns = {}  # 访问模式分析
        
        # 默认配置
        self.default_config = CacheConfig()
        
        # 缓存区域配置
        self.cache_regions = {
            "search_results": CacheConfig(
                ttl=1800,  # 30分钟
                max_size=5000,
                strategy=CacheStrategy.LRU,
                levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
            ),
            "embeddings": CacheConfig(
                ttl=86400,  # 24小时
                max_size=10000,
                strategy=CacheStrategy.LFU,
                levels=[CacheLevel.L2_REDIS],
                compress=True
            ),
            "user_sessions": CacheConfig(
                ttl=3600,  # 1小时
                max_size=1000,
                strategy=CacheStrategy.TTL,
                levels=[CacheLevel.L1_MEMORY]
            ),
            "api_responses": CacheConfig(
                ttl=300,  # 5分钟
                max_size=2000,
                strategy=CacheStrategy.LRU,
                levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
            ),
            "analytics": CacheConfig(
                ttl=7200,  # 2小时
                max_size=500,
                strategy=CacheStrategy.REFRESH_AHEAD,
                levels=[CacheLevel.L2_REDIS]
            )
        }
        
        logger.info("智能缓存服务初始化完成")
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {e}")
            raise CacheException(f"Redis连接初始化失败: {e}")
    
    async def get(
        self,
        key: str,
        region: str = "default",
        default: Any = None
    ) -> Any:
        """获取缓存值"""
        try:
            cache_key = self._build_cache_key(key, region)
            config = self._get_region_config(region)
            
            # 记录访问模式
            await self._record_access_pattern(cache_key)
            
            # 按缓存级别查找
            for level in config.levels:
                value = await self._get_from_level(cache_key, level, config)
                if value is not None:
                    # 缓存命中
                    await self._record_hit(region)
                    
                    # 如果是从L2获取的，回写到L1
                    if level == CacheLevel.L2_REDIS and CacheLevel.L1_MEMORY in config.levels:
                        await self._set_to_level(cache_key, value, CacheLevel.L1_MEMORY, config)
                    
                    return value
            
            # 缓存未命中
            await self._record_miss(region)
            return default
            
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        region: str = "default",
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            cache_key = self._build_cache_key(key, region)
            config = self._get_region_config(region)
            
            if ttl is not None:
                config.ttl = ttl
            
            # 写入所有配置的缓存级别
            success = True
            for level in config.levels:
                level_success = await self._set_to_level(cache_key, value, level, config)
                success = success and level_success
            
            if success:
                await self._record_set(region)
            
            return success
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    async def delete(
        self,
        key: str,
        region: str = "default"
    ) -> bool:
        """删除缓存值"""
        try:
            cache_key = self._build_cache_key(key, region)
            config = self._get_region_config(region)
            
            success = True
            for level in config.levels:
                level_success = await self._delete_from_level(cache_key, level)
                success = success and level_success
            
            if success:
                await self._record_delete(region)
            
            return success
            
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    async def exists(
        self,
        key: str,
        region: str = "default"
    ) -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = self._build_cache_key(key, region)
            config = self._get_region_config(region)
            
            for level in config.levels:
                if await self._exists_in_level(cache_key, level):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {e}")
            return False
    
    async def clear_region(self, region: str) -> bool:
        """清空缓存区域"""
        try:
            pattern = f"cache:{region}:*"
            
            # 清空内存缓存
            keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self.memory_cache[key]
            
            # 清空Redis缓存
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info(f"清空缓存区域: {region}")
            return True
            
        except Exception as e:
            logger.error(f"清空缓存区域失败: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        region: str = "default",
        ttl: Optional[int] = None
    ) -> Any:
        """获取缓存值，如果不存在则通过工厂函数生成并缓存"""
        try:
            # 先尝试获取缓存
            value = await self.get(key, region)
            if value is not None:
                return value
            
            # 缓存不存在，通过工厂函数生成
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            # 缓存生成的值
            if value is not None:
                await self.set(key, value, region, ttl)
            
            return value
            
        except Exception as e:
            logger.error(f"获取或设置缓存失败: {e}")
            return None
    
    async def batch_get(
        self,
        keys: List[str],
        region: str = "default"
    ) -> Dict[str, Any]:
        """批量获取缓存值"""
        try:
            results = {}
            
            # 并发获取所有键
            tasks = [self.get(key, region) for key in keys]
            values = await asyncio.gather(*tasks, return_exceptions=True)
            
            for key, value in zip(keys, values):
                if not isinstance(value, Exception) and value is not None:
                    results[key] = value
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取缓存失败: {e}")
            return {}
    
    async def batch_set(
        self,
        items: Dict[str, Any],
        region: str = "default",
        ttl: Optional[int] = None
    ) -> bool:
        """批量设置缓存值"""
        try:
            # 并发设置所有键值对
            tasks = [self.set(key, value, region, ttl) for key, value in items.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查是否所有操作都成功
            return all(result is True for result in results if not isinstance(result, Exception))
            
        except Exception as e:
            logger.error(f"批量设置缓存失败: {e}")
            return False
    
    async def get_stats(self, region: Optional[str] = None) -> Dict[str, CacheStats]:
        """获取缓存统计信息"""
        try:
            if region:
                return {region: self.cache_stats.get(region, CacheStats())}
            else:
                return self.cache_stats.copy()
                
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    async def optimize_cache(self):
        """优化缓存性能"""
        try:
            # 分析访问模式
            hot_keys = await self._analyze_hot_keys()
            
            # 预加载热点数据到L1缓存
            await self._preload_hot_data(hot_keys)
            
            # 清理过期数据
            await self._cleanup_expired_data()
            
            # 调整缓存策略
            await self._adjust_cache_strategies()
            
            logger.info("缓存优化完成")
            
        except Exception as e:
            logger.error(f"缓存优化失败: {e}")
    
    # 私有辅助方法
    def _build_cache_key(self, key: str, region: str) -> str:
        """构建缓存键"""
        return f"cache:{region}:{key}"
    
    def _get_region_config(self, region: str) -> CacheConfig:
        """获取区域配置"""
        return self.cache_regions.get(region, self.default_config)
    
    async def _get_from_level(
        self,
        key: str,
        level: CacheLevel,
        config: CacheConfig
    ) -> Any:
        """从指定级别获取缓存"""
        try:
            if level == CacheLevel.L1_MEMORY:
                cache_item = self.memory_cache.get(key)
                if cache_item:
                    # 检查是否过期
                    if cache_item["expires_at"] > datetime.now():
                        return cache_item["value"]
                    else:
                        # 过期，删除
                        del self.memory_cache[key]
                        
            elif level == CacheLevel.L2_REDIS and self.redis_client:
                data = await self.redis_client.get(key)
                if data:
                    return self._deserialize(data, config)
                    
            return None
            
        except Exception as e:
            logger.error(f"从缓存级别 {level.value} 获取数据失败: {e}")
            return None
    
    async def _set_to_level(
        self,
        key: str,
        value: Any,
        level: CacheLevel,
        config: CacheConfig
    ) -> bool:
        """设置到指定级别缓存"""
        try:
            if level == CacheLevel.L1_MEMORY:
                # 检查内存缓存大小限制
                if len(self.memory_cache) >= config.max_size:
                    await self._evict_memory_cache(config)
                
                expires_at = datetime.now() + timedelta(seconds=config.ttl)
                self.memory_cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "access_count": 0,
                    "last_access": datetime.now()
                }
                
            elif level == CacheLevel.L2_REDIS and self.redis_client:
                serialized_data = self._serialize(value, config)
                await self.redis_client.setex(key, config.ttl, serialized_data)
                
            return True
            
        except Exception as e:
            logger.error(f"设置到缓存级别 {level.value} 失败: {e}")
            return False
    
    async def _delete_from_level(self, key: str, level: CacheLevel) -> bool:
        """从指定级别删除缓存"""
        try:
            if level == CacheLevel.L1_MEMORY:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    
            elif level == CacheLevel.L2_REDIS and self.redis_client:
                await self.redis_client.delete(key)
                
            return True
            
        except Exception as e:
            logger.error(f"从缓存级别 {level.value} 删除数据失败: {e}")
            return False
    
    async def _exists_in_level(self, key: str, level: CacheLevel) -> bool:
        """检查指定级别是否存在缓存"""
        try:
            if level == CacheLevel.L1_MEMORY:
                return key in self.memory_cache
                
            elif level == CacheLevel.L2_REDIS and self.redis_client:
                return await self.redis_client.exists(key) > 0
                
            return False
            
        except Exception as e:
            logger.error(f"检查缓存级别 {level.value} 存在性失败: {e}")
            return False
    
    def _serialize(self, value: Any, config: CacheConfig) -> bytes:
        """序列化数据"""
        if config.serialize_method == "json":
            data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        else:  # pickle
            data = pickle.dumps(value)
        
        if config.compress:
            import gzip
            data = gzip.compress(data)
        
        return data
    
    def _deserialize(self, data: bytes, config: CacheConfig) -> Any:
        """反序列化数据"""
        if config.compress:
            import gzip
            data = gzip.decompress(data)
        
        if config.serialize_method == "json":
            return json.loads(data.decode('utf-8'))
        else:  # pickle
            return pickle.loads(data)
    
    async def _evict_memory_cache(self, config: CacheConfig):
        """内存缓存淘汰"""
        if config.strategy == CacheStrategy.LRU:
            # 删除最近最少使用的项
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["last_access"]
            )
            del self.memory_cache[oldest_key]
            
        elif config.strategy == CacheStrategy.LFU:
            # 删除使用频率最低的项
            least_used_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["access_count"]
            )
            del self.memory_cache[least_used_key]
    
    async def _record_access_pattern(self, key: str):
        """记录访问模式"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                "count": 0,
                "last_access": None,
                "access_times": []
            }
        
        pattern = self.access_patterns[key]
        pattern["count"] += 1
        pattern["last_access"] = datetime.now()
        pattern["access_times"].append(datetime.now())
        
        # 只保留最近100次访问记录
        if len(pattern["access_times"]) > 100:
            pattern["access_times"] = pattern["access_times"][-100:]
    
    async def _record_hit(self, region: str):
        """记录缓存命中"""
        if region not in self.cache_stats:
            self.cache_stats[region] = CacheStats()
        self.cache_stats[region].hits += 1
    
    async def _record_miss(self, region: str):
        """记录缓存未命中"""
        if region not in self.cache_stats:
            self.cache_stats[region] = CacheStats()
        self.cache_stats[region].misses += 1
    
    async def _record_set(self, region: str):
        """记录缓存设置"""
        if region not in self.cache_stats:
            self.cache_stats[region] = CacheStats()
        self.cache_stats[region].sets += 1
    
    async def _record_delete(self, region: str):
        """记录缓存删除"""
        if region not in self.cache_stats:
            self.cache_stats[region] = CacheStats()
        self.cache_stats[region].deletes += 1
    
    async def _analyze_hot_keys(self) -> List[str]:
        """分析热点键"""
        # 根据访问频率和最近访问时间分析热点键
        hot_keys = []
        for key, pattern in self.access_patterns.items():
            if pattern["count"] > 10 and pattern["last_access"]:
                # 最近1小时内有访问
                if (datetime.now() - pattern["last_access"]).seconds < 3600:
                    hot_keys.append(key)
        
        return sorted(hot_keys, key=lambda k: self.access_patterns[k]["count"], reverse=True)[:100]
    
    async def _preload_hot_data(self, hot_keys: List[str]):
        """预加载热点数据"""
        # 将热点数据从L2加载到L1
        for key in hot_keys:
            if key not in self.memory_cache and self.redis_client:
                data = await self.redis_client.get(key)
                if data:
                    # 简化处理，直接存储到内存
                    expires_at = datetime.now() + timedelta(seconds=3600)
                    self.memory_cache[key] = {
                        "value": data,
                        "expires_at": expires_at,
                        "access_count": 0,
                        "last_access": datetime.now()
                    }
    
    async def _cleanup_expired_data(self):
        """清理过期数据"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item["expires_at"] < now
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def _adjust_cache_strategies(self):
        """调整缓存策略"""
        # 根据访问模式调整缓存策略
        # 这里可以实现更复杂的策略调整逻辑
        pass


# 全局缓存服务实例
cache_service = CacheService()
