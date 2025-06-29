"""
业务数据缓存服务
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from loguru import logger

from app.core.multi_level_cache import get_multi_level_cache, CacheLevel
from app.core.redis_cache import get_redis_cache, CacheConfig, SerializationType
from app.models import User, KnowledgeBase, Document, Conversation


class BusinessCacheService:
    """业务数据缓存服务"""
    
    def __init__(self):
        self.cache_manager = get_multi_level_cache()
        
        # 缓存命名空间
        self.namespaces = {
            "users": "users",
            "knowledge_bases": "knowledge_bases",
            "documents": "documents",
            "conversations": "conversations",
            "search_results": "search_results",
            "ai_responses": "ai_responses",
            "statistics": "statistics",
            "configurations": "configurations"
        }
        
        # 缓存TTL配置
        self.ttl_config = {
            "users": 1800,  # 30分钟
            "knowledge_bases": 3600,  # 1小时
            "documents": 1800,  # 30分钟
            "conversations": 900,  # 15分钟
            "search_results": 300,  # 5分钟
            "ai_responses": 1800,  # 30分钟
            "statistics": 600,  # 10分钟
            "configurations": 3600,  # 1小时
        }
    
    # 用户缓存
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户缓存"""
        cache_key = f"user:{user_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["users"])
    
    async def set_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """设置用户缓存"""
        cache_key = f"user:{user_id}"
        ttl = self.ttl_config["users"]
        return await self.cache_manager.set(
            cache_key, user_data, ttl, self.namespaces["users"]
        )
    
    async def invalidate_user(self, user_id: int) -> bool:
        """使用户缓存失效"""
        cache_key = f"user:{user_id}"
        return await self.cache_manager.delete(cache_key, self.namespaces["users"])
    
    async def get_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """获取用户权限缓存"""
        cache_key = f"permissions:{user_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["users"])
    
    async def set_user_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """设置用户权限缓存"""
        cache_key = f"permissions:{user_id}"
        ttl = self.ttl_config["users"]
        return await self.cache_manager.set(
            cache_key, permissions, ttl, self.namespaces["users"]
        )
    
    # 知识库缓存
    async def get_knowledge_base(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """获取知识库缓存"""
        cache_key = f"kb:{kb_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["knowledge_bases"])
    
    async def set_knowledge_base(self, kb_id: int, kb_data: Dict[str, Any]) -> bool:
        """设置知识库缓存"""
        cache_key = f"kb:{kb_id}"
        ttl = self.ttl_config["knowledge_bases"]
        return await self.cache_manager.set(
            cache_key, kb_data, ttl, self.namespaces["knowledge_bases"]
        )
    
    async def invalidate_knowledge_base(self, kb_id: int) -> bool:
        """使知识库缓存失效"""
        cache_key = f"kb:{kb_id}"
        return await self.cache_manager.delete(cache_key, self.namespaces["knowledge_bases"])
    
    async def get_user_knowledge_bases(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取用户知识库列表缓存"""
        cache_key = f"user_kbs:{user_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["knowledge_bases"])
    
    async def set_user_knowledge_bases(self, user_id: int, kb_list: List[Dict[str, Any]]) -> bool:
        """设置用户知识库列表缓存"""
        cache_key = f"user_kbs:{user_id}"
        ttl = self.ttl_config["knowledge_bases"]
        return await self.cache_manager.set(
            cache_key, kb_list, ttl, self.namespaces["knowledge_bases"]
        )
    
    # 文档缓存
    async def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """获取文档缓存"""
        cache_key = f"doc:{doc_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["documents"])
    
    async def set_document(self, doc_id: int, doc_data: Dict[str, Any]) -> bool:
        """设置文档缓存"""
        cache_key = f"doc:{doc_id}"
        ttl = self.ttl_config["documents"]
        return await self.cache_manager.set(
            cache_key, doc_data, ttl, self.namespaces["documents"]
        )
    
    async def invalidate_document(self, doc_id: int) -> bool:
        """使文档缓存失效"""
        cache_key = f"doc:{doc_id}"
        return await self.cache_manager.delete(cache_key, self.namespaces["documents"])
    
    async def get_knowledge_base_documents(self, kb_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取知识库文档列表缓存"""
        cache_key = f"kb_docs:{kb_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["documents"])
    
    async def set_knowledge_base_documents(self, kb_id: int, doc_list: List[Dict[str, Any]]) -> bool:
        """设置知识库文档列表缓存"""
        cache_key = f"kb_docs:{kb_id}"
        ttl = self.ttl_config["documents"]
        return await self.cache_manager.set(
            cache_key, doc_list, ttl, self.namespaces["documents"]
        )
    
    # 对话缓存
    async def get_conversation(self, conv_id: int) -> Optional[Dict[str, Any]]:
        """获取对话缓存"""
        cache_key = f"conv:{conv_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["conversations"])
    
    async def set_conversation(self, conv_id: int, conv_data: Dict[str, Any]) -> bool:
        """设置对话缓存"""
        cache_key = f"conv:{conv_id}"
        ttl = self.ttl_config["conversations"]
        return await self.cache_manager.set(
            cache_key, conv_data, ttl, self.namespaces["conversations"]
        )
    
    async def invalidate_conversation(self, conv_id: int) -> bool:
        """使对话缓存失效"""
        cache_key = f"conv:{conv_id}"
        return await self.cache_manager.delete(cache_key, self.namespaces["conversations"])
    
    async def get_user_conversations(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取用户对话列表缓存"""
        cache_key = f"user_convs:{user_id}"
        return await self.cache_manager.get(cache_key, self.namespaces["conversations"])
    
    async def set_user_conversations(self, user_id: int, conv_list: List[Dict[str, Any]]) -> bool:
        """设置用户对话列表缓存"""
        cache_key = f"user_convs:{user_id}"
        ttl = self.ttl_config["conversations"]
        return await self.cache_manager.set(
            cache_key, conv_list, ttl, self.namespaces["conversations"]
        )
    
    # 搜索结果缓存
    async def get_search_results(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """获取搜索结果缓存"""
        cache_key = f"search:{query_hash}"
        return await self.cache_manager.get(cache_key, self.namespaces["search_results"])
    
    async def set_search_results(self, query_hash: str, results: Dict[str, Any]) -> bool:
        """设置搜索结果缓存"""
        cache_key = f"search:{query_hash}"
        ttl = self.ttl_config["search_results"]
        return await self.cache_manager.set(
            cache_key, results, ttl, self.namespaces["search_results"]
        )
    
    # AI响应缓存
    async def get_ai_response(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """获取AI响应缓存"""
        cache_key = f"ai_response:{prompt_hash}"
        return await self.cache_manager.get(cache_key, self.namespaces["ai_responses"])
    
    async def set_ai_response(self, prompt_hash: str, response: Dict[str, Any]) -> bool:
        """设置AI响应缓存"""
        cache_key = f"ai_response:{prompt_hash}"
        ttl = self.ttl_config["ai_responses"]
        return await self.cache_manager.set(
            cache_key, response, ttl, self.namespaces["ai_responses"]
        )
    
    # 统计数据缓存
    async def get_statistics(self, stat_type: str, time_range: str = "daily") -> Optional[Dict[str, Any]]:
        """获取统计数据缓存"""
        cache_key = f"stats:{stat_type}:{time_range}"
        return await self.cache_manager.get(cache_key, self.namespaces["statistics"])
    
    async def set_statistics(self, stat_type: str, time_range: str, stats_data: Dict[str, Any]) -> bool:
        """设置统计数据缓存"""
        cache_key = f"stats:{stat_type}:{time_range}"
        ttl = self.ttl_config["statistics"]
        return await self.cache_manager.set(
            cache_key, stats_data, ttl, self.namespaces["statistics"]
        )
    
    # 配置缓存
    async def get_configuration(self, config_key: str) -> Optional[Any]:
        """获取配置缓存"""
        cache_key = f"config:{config_key}"
        return await self.cache_manager.get(cache_key, self.namespaces["configurations"])
    
    async def set_configuration(self, config_key: str, config_value: Any) -> bool:
        """设置配置缓存"""
        cache_key = f"config:{config_key}"
        ttl = self.ttl_config["configurations"]
        return await self.cache_manager.set(
            cache_key, config_value, ttl, self.namespaces["configurations"]
        )
    
    # 批量操作
    async def invalidate_user_related_cache(self, user_id: int):
        """使用户相关的所有缓存失效"""
        tasks = [
            self.invalidate_user(user_id),
            self.cache_manager.delete(f"permissions:{user_id}", self.namespaces["users"]),
            self.cache_manager.delete(f"user_kbs:{user_id}", self.namespaces["knowledge_bases"]),
            self.cache_manager.delete(f"user_convs:{user_id}", self.namespaces["conversations"]),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"用户相关缓存失效: {user_id}")
    
    async def invalidate_knowledge_base_related_cache(self, kb_id: int):
        """使知识库相关的所有缓存失效"""
        tasks = [
            self.invalidate_knowledge_base(kb_id),
            self.cache_manager.delete(f"kb_docs:{kb_id}", self.namespaces["documents"]),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"知识库相关缓存失效: {kb_id}")
    
    async def warm_up_cache(self):
        """缓存预热"""
        logger.info("开始缓存预热...")
        
        try:
            # 预热热门用户数据
            active_users = await User.filter(is_active=True).limit(50)
            for user in active_users:
                user_data = await user.to_dict()
                await self.set_user(user.id, user_data)
            
            # 预热公开知识库
            public_kbs = await KnowledgeBase.filter(
                visibility="public", 
                is_deleted=False
            ).limit(20)
            for kb in public_kbs:
                kb_data = await kb.to_dict()
                await self.set_knowledge_base(kb.id, kb_data)
            
            logger.info("缓存预热完成")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        multi_level_stats = self.cache_manager.get_stats()
        
        # 获取Redis统计
        redis_stats = {}
        try:
            redis_cache = await get_redis_cache()
            redis_stats = await redis_cache.get_stats()
        except Exception as e:
            logger.error(f"获取Redis统计失败: {e}")
        
        return {
            "multi_level_cache": multi_level_stats,
            "redis_cache": redis_stats,
            "namespaces": self.namespaces,
            "ttl_config": self.ttl_config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """缓存健康检查"""
        health_status = await self.cache_manager.health_check()
        
        # 测试基本缓存操作
        test_key = "health_check_test"
        test_value = {"timestamp": time.time(), "test": True}
        
        try:
            # 测试设置和获取
            await self.cache_manager.set(test_key, test_value, 60, "test")
            retrieved_value = await self.cache_manager.get(test_key, "test")
            
            if retrieved_value == test_value:
                health_status["cache_operations"] = {"status": "healthy"}
            else:
                health_status["cache_operations"] = {"status": "unhealthy", "error": "数据不一致"}
            
            # 清理测试数据
            await self.cache_manager.delete(test_key, "test")
            
        except Exception as e:
            health_status["cache_operations"] = {"status": "unhealthy", "error": str(e)}
        
        return health_status


# 全局业务缓存服务实例
business_cache_service = BusinessCacheService()


def get_business_cache() -> BusinessCacheService:
    """获取业务缓存服务实例"""
    return business_cache_service


# 业务缓存装饰器
def business_cache(
    cache_type: str,
    ttl: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """业务缓存装饰器"""
    def decorator(func: callable) -> callable:
        async def wrapper(*args, **kwargs):
            cache_service = get_business_cache()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
                cache_key = ":".join(key_parts)
            
            # 根据缓存类型选择命名空间
            namespace = cache_service.namespaces.get(cache_type, "default")
            cache_ttl = ttl or cache_service.ttl_config.get(cache_type, 3600)
            
            # 尝试从缓存获取
            cached_result = await cache_service.cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # 调用原函数
            result = await func(*args, **kwargs)
            
            # 设置缓存
            await cache_service.cache_manager.set(cache_key, result, cache_ttl, namespace)
            
            return result
        
        return wrapper
    
    return decorator
