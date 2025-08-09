# Copyright (c) 2025 左岚. All rights reserved.
"""
简化缓存管理器 - 内存缓存实现
"""

import time
import json
import logging
import threading
from typing import Any, Optional, Dict
from datetime import datetime
from functools import wraps
import hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleCacheManager:
    """简化缓存管理器 - 使用内存缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        self._max_size = 10000  # 最大缓存项数
    
    def _generate_key(self, key: str, prefix: str = "ai_platform") -> str:
        """生成缓存键"""
        return f"{prefix}:{key}"
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_data in self._cache.items():
            expires = cache_data.get('expires')
            if expires and current_time > expires:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "ai_platform") -> bool:
        """设置缓存值"""
        try:
            with self._lock:
                # 清理过期缓存
                self._cleanup_expired()
                
                # 检查缓存大小限制
                if len(self._cache) >= self._max_size:
                    # 删除最旧的缓存项
                    oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get('created', 0))
                    del self._cache[oldest_key]
                
                cache_key = self._generate_key(key, prefix)
                self._cache[cache_key] = {
                    'value': value,
                    'expires': time.time() + ttl if ttl else None,
                    'created': time.time()
                }
                
                self._stats['sets'] += 1
                logger.debug(f"缓存设置成功: {cache_key}")
                return True
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存设置失败: {key}, 错误: {e}")
            return False
    
    def get(self, key: str, default: Any = None, prefix: str = "ai_platform") -> Any:
        """获取缓存值"""
        try:
            with self._lock:
                cache_key = self._generate_key(key, prefix)
                cache_data = self._cache.get(cache_key)
                
                if cache_data is None:
                    self._stats['misses'] += 1
                    logger.debug(f"缓存未命中: {cache_key}")
                    return default
                
                # 检查是否过期
                expires = cache_data.get('expires')
                if expires and time.time() > expires:
                    del self._cache[cache_key]
                    self._stats['misses'] += 1
                    logger.debug(f"缓存已过期: {cache_key}")
                    return default
                
                self._stats['hits'] += 1
                logger.debug(f"缓存命中: {cache_key}")
                return cache_data['value']
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存获取失败: {key}, 错误: {e}")
            return default
    
    def delete(self, key: str, prefix: str = "ai_platform") -> bool:
        """删除缓存"""
        try:
            with self._lock:
                cache_key = self._generate_key(key, prefix)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    self._stats['deletes'] += 1
                    logger.debug(f"缓存删除成功: {cache_key}")
                    return True
                return False
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"缓存删除失败: {key}, 错误: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "ai_platform") -> bool:
        """检查缓存是否存在"""
        try:
            with self._lock:
                cache_key = self._generate_key(key, prefix)
                cache_data = self._cache.get(cache_key)
                
                if cache_data is None:
                    return False
                
                # 检查是否过期
                expires = cache_data.get('expires')
                if expires and time.time() > expires:
                    del self._cache[cache_key]
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"缓存存在检查失败: {key}, 错误: {e}")
            return False
    
    def expire(self, key: str, ttl: int, prefix: str = "ai_platform") -> bool:
        """设置缓存过期时间"""
        try:
            with self._lock:
                cache_key = self._generate_key(key, prefix)
                if cache_key in self._cache:
                    self._cache[cache_key]['expires'] = time.time() + ttl
                    return True
                return False
                
        except Exception as e:
            logger.error(f"缓存过期设置失败: {key}, 错误: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            with self._lock:
                current_time = time.time()
                active_items = 0
                expired_items = 0
                
                for cache_data in self._cache.values():
                    expires = cache_data.get('expires')
                    if expires is None or current_time <= expires:
                        active_items += 1
                    else:
                        expired_items += 1
                
                return {
                    'cache_stats': self._stats.copy(),
                    'memory_cache_info': {
                        'total_items': len(self._cache),
                        'active_items': active_items,
                        'expired_items': expired_items,
                        'max_size': self._max_size,
                        'redis_available': self._redis_available
                    }
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {'error': str(e)}
    
    def clear_pattern(self, pattern: str, prefix: str = "ai_platform") -> int:
        """清除匹配模式的缓存"""
        try:
            with self._lock:
                cache_pattern = self._generate_key(pattern, prefix)
                # 简单的模式匹配
                pattern_key = cache_pattern.replace('*', '')
                
                deleted = 0
                keys_to_delete = []
                
                for cache_key in self._cache.keys():
                    if pattern_key in cache_key:
                        keys_to_delete.append(cache_key)
                
                for key in keys_to_delete:
                    del self._cache[key]
                    deleted += 1
                
                self._stats['deletes'] += deleted
                logger.info(f"清除缓存模式 {cache_pattern}: {deleted} 个键")
                return deleted
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"清除缓存模式失败: {pattern}, 错误: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            
            # 测试缓存操作
            test_key = "health_check_test"
            self.set(test_key, "test_value", ttl=1)
            result = self.get(test_key)
            self.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy' if result == "test_value" else 'unhealthy',
                'response_time_ms': round(response_time, 2),
                'cache_type': 'redis' if self._redis_available else 'memory',
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
            with self._lock:
                self._cache.clear()
            logger.info("缓存已清理")
        except Exception as e:
            logger.error(f"关闭缓存失败: {e}")


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
cache_manager = SimpleCacheManager()
