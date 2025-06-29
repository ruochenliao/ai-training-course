"""
缓存管理API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.core import get_current_user, PermissionChecker
from app.core.redis_cache import get_redis_cache
from app.core.multi_level_cache import get_multi_level_cache
from app.services.cache_service import get_business_cache
from app.models import User

router = APIRouter()

# 权限检查器
require_cache_admin = PermissionChecker("cache:admin")
require_cache_view = PermissionChecker("cache:view")


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    multi_level_cache: Dict[str, Any]
    redis_cache: Dict[str, Any]
    namespaces: Dict[str, str]
    ttl_config: Dict[str, int]


class CacheHealthResponse(BaseModel):
    """缓存健康响应"""
    overall: Dict[str, Any]
    l1_cache: Dict[str, Any]
    l2_cache: Dict[str, Any]
    cache_operations: Dict[str, Any]


@router.get("/stats", response_model=CacheStatsResponse, summary="获取缓存统计")
async def get_cache_stats(
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取缓存系统统计信息
    """
    cache_service = get_business_cache()
    stats = await cache_service.get_cache_stats()
    
    return CacheStatsResponse(**stats)


@router.get("/health", response_model=CacheHealthResponse, summary="获取缓存健康状态")
async def get_cache_health(
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取缓存系统健康状态
    """
    cache_service = get_business_cache()
    health = await cache_service.health_check()
    
    return CacheHealthResponse(**health)


@router.get("/redis/info", summary="获取Redis信息")
async def get_redis_info(
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取Redis详细信息
    """
    try:
        redis_cache = await get_redis_cache()
        
        # 获取Redis统计
        stats = await redis_cache.get_stats()
        
        # 获取内存使用情况
        memory_usage = await redis_cache.get_memory_usage()
        
        return {
            "connection_status": "connected" if redis_cache.connected else "disconnected",
            "stats": stats,
            "memory_usage": memory_usage
        }
        
    except Exception as e:
        return {
            "connection_status": "error",
            "error": str(e)
        }


@router.get("/multi-level/stats", summary="获取多层缓存统计")
async def get_multi_level_cache_stats(
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取多层缓存详细统计
    """
    cache_manager = get_multi_level_cache()
    stats = cache_manager.get_stats()
    
    return stats


@router.post("/clear", summary="清空缓存")
async def clear_cache(
    namespace: Optional[str] = Query(None, description="命名空间，不指定则清空所有"),
    cache_level: Optional[str] = Query(None, description="缓存级别: l1, l2, all"),
    current_user: User = Depends(require_cache_admin)
) -> Any:
    """
    清空缓存数据
    """
    cleared_count = 0
    
    try:
        if cache_level == "l1" or cache_level is None:
            # 清空L1缓存（内存缓存）
            cache_manager = get_multi_level_cache()
            if namespace:
                l1_cleared = await cache_manager.clear_namespace(namespace)
                cleared_count += l1_cleared
            else:
                # 清空所有L1缓存
                cache_manager.l1_cache.clear()
                cache_manager.l1_access_times.clear()
                cache_manager.l1_access_counts.clear()
                cleared_count += len(cache_manager.l1_cache)
        
        if cache_level == "l2" or cache_level is None:
            # 清空L2缓存（Redis）
            redis_cache = await get_redis_cache()
            if namespace:
                l2_cleared = await redis_cache.clear_namespace(namespace)
                cleared_count += l2_cleared
            else:
                # 清空所有Redis缓存（谨慎操作）
                if redis_cache.connected:
                    await redis_cache.redis_client.flushdb()
                    cleared_count += 1000  # 估计值
        
        return {
            "success": True,
            "message": f"缓存清空完成",
            "cleared_count": cleared_count,
            "namespace": namespace or "all",
            "cache_level": cache_level or "all",
            "cleared_by": current_user.username
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"缓存清空失败: {str(e)}",
            "error": str(e)
        }


@router.post("/warm-up", summary="缓存预热")
async def warm_up_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_cache_admin)
) -> Any:
    """
    执行缓存预热
    """
    async def warm_up_task():
        try:
            cache_service = get_business_cache()
            await cache_service.warm_up_cache()
            logger.info(f"缓存预热任务完成，执行者: {current_user.username}")
            
        except Exception as e:
            logger.error(f"缓存预热任务失败: {e}")
    
    # 在后台执行预热任务
    background_tasks.add_task(warm_up_task)
    
    return {
        "success": True,
        "message": "缓存预热任务已启动",
        "initiated_by": current_user.username
    }


@router.get("/namespace/{namespace}/keys", summary="获取命名空间键列表")
async def get_namespace_keys(
    namespace: str,
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取指定命名空间的缓存键列表
    """
    try:
        redis_cache = await get_redis_cache()
        
        if not redis_cache.connected:
            return {
                "namespace": namespace,
                "keys": [],
                "total": 0,
                "error": "Redis未连接"
            }
        
        # 获取命名空间下的键
        pattern = f"cache:{namespace}:*"
        keys = await redis_cache.redis_client.keys(pattern)
        
        # 限制返回数量
        limited_keys = keys[:limit]
        
        # 获取键的详细信息
        key_details = []
        for key in limited_keys:
            try:
                ttl = await redis_cache.redis_client.ttl(key)
                key_type = await redis_cache.redis_client.type(key)
                
                key_details.append({
                    "key": key.decode('utf-8') if isinstance(key, bytes) else key,
                    "ttl": ttl,
                    "type": key_type
                })
                
            except Exception as e:
                key_details.append({
                    "key": key.decode('utf-8') if isinstance(key, bytes) else key,
                    "error": str(e)
                })
        
        return {
            "namespace": namespace,
            "keys": key_details,
            "total": len(keys),
            "returned": len(limited_keys)
        }
        
    except Exception as e:
        return {
            "namespace": namespace,
            "keys": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/key/{namespace}/{key}", summary="获取缓存键值")
async def get_cache_key_value(
    namespace: str,
    key: str,
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取指定缓存键的值
    """
    try:
        # 先尝试从多层缓存获取
        cache_manager = get_multi_level_cache()
        value = await cache_manager.get(key, namespace)
        
        if value is not None:
            return {
                "namespace": namespace,
                "key": key,
                "value": value,
                "source": "multi_level_cache",
                "found": True
            }
        
        # 如果多层缓存没有，尝试直接从Redis获取
        redis_cache = await get_redis_cache()
        redis_value = await redis_cache.get(key, namespace)
        
        if redis_value is not None:
            return {
                "namespace": namespace,
                "key": key,
                "value": redis_value,
                "source": "redis_cache",
                "found": True
            }
        
        return {
            "namespace": namespace,
            "key": key,
            "value": None,
            "source": None,
            "found": False
        }
        
    except Exception as e:
        return {
            "namespace": namespace,
            "key": key,
            "value": None,
            "error": str(e),
            "found": False
        }


@router.delete("/key/{namespace}/{key}", summary="删除缓存键")
async def delete_cache_key(
    namespace: str,
    key: str,
    current_user: User = Depends(require_cache_admin)
) -> Any:
    """
    删除指定的缓存键
    """
    try:
        cache_manager = get_multi_level_cache()
        success = await cache_manager.delete(key, namespace)
        
        return {
            "success": success,
            "message": f"缓存键删除{'成功' if success else '失败'}",
            "namespace": namespace,
            "key": key,
            "deleted_by": current_user.username
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"删除缓存键失败: {str(e)}",
            "namespace": namespace,
            "key": key,
            "error": str(e)
        }


@router.post("/invalidate/user/{user_id}", summary="使用户缓存失效")
async def invalidate_user_cache(
    user_id: int,
    current_user: User = Depends(require_cache_admin)
) -> Any:
    """
    使指定用户的所有相关缓存失效
    """
    try:
        cache_service = get_business_cache()
        await cache_service.invalidate_user_related_cache(user_id)
        
        return {
            "success": True,
            "message": f"用户 {user_id} 相关缓存已失效",
            "user_id": user_id,
            "invalidated_by": current_user.username
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"用户缓存失效失败: {str(e)}",
            "user_id": user_id,
            "error": str(e)
        }


@router.post("/invalidate/knowledge-base/{kb_id}", summary="使知识库缓存失效")
async def invalidate_knowledge_base_cache(
    kb_id: int,
    current_user: User = Depends(require_cache_admin)
) -> Any:
    """
    使指定知识库的所有相关缓存失效
    """
    try:
        cache_service = get_business_cache()
        await cache_service.invalidate_knowledge_base_related_cache(kb_id)
        
        return {
            "success": True,
            "message": f"知识库 {kb_id} 相关缓存已失效",
            "knowledge_base_id": kb_id,
            "invalidated_by": current_user.username
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"知识库缓存失效失败: {str(e)}",
            "knowledge_base_id": kb_id,
            "error": str(e)
        }


@router.get("/performance/analysis", summary="缓存性能分析")
async def get_cache_performance_analysis(
    current_user: User = Depends(require_cache_view)
) -> Any:
    """
    获取缓存性能分析报告
    """
    try:
        # 获取多层缓存统计
        cache_manager = get_multi_level_cache()
        multi_level_stats = cache_manager.get_stats()
        
        # 获取Redis统计
        redis_cache = await get_redis_cache()
        redis_stats = await redis_cache.get_stats()
        
        # 获取业务缓存统计
        cache_service = get_business_cache()
        business_stats = await cache_service.get_cache_stats()
        
        # 性能分析
        analysis = {
            "overall_performance": {
                "overall_hit_rate": multi_level_stats["overall_stats"]["overall_hit_rate"],
                "l1_hit_rate": multi_level_stats["l1_stats"]["hit_rate"],
                "l2_hit_rate": multi_level_stats["l2_stats"]["hit_rate"],
                "total_operations": multi_level_stats["overall_stats"]["total_operations"]
            },
            "memory_efficiency": {
                "l1_cache_size": multi_level_stats["l1_stats"]["size"],
                "l1_max_size": multi_level_stats["l1_stats"]["max_size"],
                "l1_utilization": (
                    multi_level_stats["l1_stats"]["size"] / 
                    multi_level_stats["l1_stats"]["max_size"]
                    if multi_level_stats["l1_stats"]["max_size"] else 0
                ),
                "redis_memory": redis_stats.get("memory_usage", {})
            },
            "cache_effectiveness": {
                "cache_promotions": multi_level_stats["overall_stats"]["cache_promotions"],
                "cache_evictions": multi_level_stats["overall_stats"]["cache_evictions"],
                "promotion_rate": (
                    multi_level_stats["overall_stats"]["cache_promotions"] /
                    max(multi_level_stats["overall_stats"]["total_operations"], 1)
                )
            },
            "recommendations": []
        }
        
        # 生成优化建议
        if analysis["overall_performance"]["overall_hit_rate"] < 0.7:
            analysis["recommendations"].append({
                "type": "performance",
                "priority": "high",
                "message": "整体缓存命中率较低，建议检查缓存策略和TTL配置"
            })
        
        if analysis["memory_efficiency"]["l1_utilization"] > 0.9:
            analysis["recommendations"].append({
                "type": "memory",
                "priority": "medium",
                "message": "L1缓存使用率过高，建议增加缓存大小或调整驱逐策略"
            })
        
        if multi_level_stats["overall_stats"]["cache_evictions"] > multi_level_stats["overall_stats"]["total_operations"] * 0.1:
            analysis["recommendations"].append({
                "type": "eviction",
                "priority": "medium",
                "message": "缓存驱逐频率较高，建议优化缓存大小或TTL配置"
            })
        
        return analysis
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "缓存性能分析失败"
        }
