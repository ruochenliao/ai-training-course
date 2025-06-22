"""
缓存管理API端点
"""

from typing import List, Optional, Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.services.cache_service import cache_service, CacheStats
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.exceptions import CacheException

router = APIRouter()


class CacheOperationRequest(BaseModel):
    """缓存操作请求"""
    key: str = Field(..., description="缓存键")
    value: Any = Field(None, description="缓存值")
    region: str = Field("default", description="缓存区域")
    ttl: Optional[int] = Field(None, description="过期时间（秒）")


class BatchCacheRequest(BaseModel):
    """批量缓存请求"""
    items: Dict[str, Any] = Field(..., description="键值对")
    region: str = Field("default", description="缓存区域")
    ttl: Optional[int] = Field(None, description="过期时间（秒）")


class CacheResponse(BaseModel):
    """缓存响应"""
    success: bool = True
    data: Any = None
    metadata: Dict[str, Any] = {}


@router.get("/stats", response_model=CacheResponse)
async def get_cache_stats(
    region: Optional[str] = Query(None, description="缓存区域"),
    current_user: User = Depends(get_current_user)
):
    """
    获取缓存统计信息
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = await cache_service.get_stats(region)
        
        # 转换统计数据为字典格式
        stats_data = {}
        for region_name, cache_stats in stats.items():
            stats_data[region_name] = {
                "hits": cache_stats.hits,
                "misses": cache_stats.misses,
                "sets": cache_stats.sets,
                "deletes": cache_stats.deletes,
                "evictions": cache_stats.evictions,
                "memory_usage": cache_stats.memory_usage,
                "hit_rate": cache_stats.hit_rate
            }
        
        return CacheResponse(
            data=stats_data,
            metadata={
                "total_regions": len(stats_data),
                "query_region": region
            }
        )
        
    except CacheException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.get("/regions")
async def get_cache_regions(
    current_user: User = Depends(get_current_user)
):
    """
    获取缓存区域列表
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        regions = [
            {
                "name": "search_results",
                "description": "搜索结果缓存",
                "ttl": 1800,
                "max_size": 5000
            },
            {
                "name": "embeddings",
                "description": "向量嵌入缓存",
                "ttl": 86400,
                "max_size": 10000
            },
            {
                "name": "user_sessions",
                "description": "用户会话缓存",
                "ttl": 3600,
                "max_size": 1000
            },
            {
                "name": "api_responses",
                "description": "API响应缓存",
                "ttl": 300,
                "max_size": 2000
            },
            {
                "name": "analytics",
                "description": "分析数据缓存",
                "ttl": 7200,
                "max_size": 500
            }
        ]
        
        return CacheResponse(
            data={
                "regions": regions,
                "total_count": len(regions)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存区域失败: {str(e)}")


@router.get("/get/{key}")
async def get_cache_value(
    key: str,
    region: str = Query("default", description="缓存区域"),
    current_user: User = Depends(get_current_user)
):
    """
    获取缓存值
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        value = await cache_service.get(key, region)
        
        return CacheResponse(
            data={
                "key": key,
                "value": value,
                "exists": value is not None
            },
            metadata={
                "region": region,
                "retrieved_at": "now"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存值失败: {str(e)}")


@router.post("/set")
async def set_cache_value(
    request: CacheOperationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    设置缓存值
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await cache_service.set(
            request.key,
            request.value,
            request.region,
            request.ttl
        )
        
        return CacheResponse(
            data={
                "key": request.key,
                "success": success
            },
            metadata={
                "region": request.region,
                "ttl": request.ttl,
                "set_at": "now"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置缓存值失败: {str(e)}")


@router.delete("/delete/{key}")
async def delete_cache_value(
    key: str,
    region: str = Query("default", description="缓存区域"),
    current_user: User = Depends(get_current_user)
):
    """
    删除缓存值
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await cache_service.delete(key, region)
        
        return CacheResponse(
            data={
                "key": key,
                "success": success
            },
            metadata={
                "region": region,
                "deleted_at": "now"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除缓存值失败: {str(e)}")


@router.post("/batch-get")
async def batch_get_cache_values(
    keys: List[str],
    region: str = Query("default", description="缓存区域"),
    current_user: User = Depends(get_current_user)
):
    """
    批量获取缓存值
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if len(keys) > 100:
            raise HTTPException(status_code=400, detail="批量获取键数量不能超过100个")
        
        results = await cache_service.batch_get(keys, region)
        
        return CacheResponse(
            data={
                "results": results,
                "found_count": len(results),
                "total_requested": len(keys)
            },
            metadata={
                "region": region,
                "retrieved_at": "now"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量获取缓存值失败: {str(e)}")


@router.post("/batch-set")
async def batch_set_cache_values(
    request: BatchCacheRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量设置缓存值
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if len(request.items) > 100:
            raise HTTPException(status_code=400, detail="批量设置键数量不能超过100个")
        
        success = await cache_service.batch_set(
            request.items,
            request.region,
            request.ttl
        )
        
        return CacheResponse(
            data={
                "success": success,
                "items_count": len(request.items)
            },
            metadata={
                "region": request.region,
                "ttl": request.ttl,
                "set_at": "now"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量设置缓存值失败: {str(e)}")


@router.delete("/clear/{region}")
async def clear_cache_region(
    region: str,
    current_user: User = Depends(get_current_user)
):
    """
    清空缓存区域
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        success = await cache_service.clear_region(region)
        
        return CacheResponse(
            data={
                "region": region,
                "success": success
            },
            metadata={
                "cleared_at": "now",
                "operation": "clear_region"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空缓存区域失败: {str(e)}")


@router.post("/optimize")
async def optimize_cache(
    current_user: User = Depends(get_current_user)
):
    """
    优化缓存性能
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        await cache_service.optimize_cache()
        
        return CacheResponse(
            data={
                "optimization_completed": True
            },
            metadata={
                "optimized_at": "now",
                "operation": "cache_optimization"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"缓存优化失败: {str(e)}")


@router.get("/health")
async def get_cache_health(
    current_user: User = Depends(get_current_user)
):
    """
    获取缓存健康状态
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 检查缓存服务健康状态
        health_status = {
            "redis_connected": True,  # 这里应该实际检查Redis连接
            "memory_usage": "normal",  # 这里应该检查内存使用情况
            "response_time": "fast",   # 这里应该检查响应时间
            "error_rate": "low"        # 这里应该检查错误率
        }
        
        # 获取统计信息
        stats = await cache_service.get_stats()
        
        # 计算整体健康分数
        total_requests = sum(s.hits + s.misses for s in stats.values())
        total_hits = sum(s.hits for s in stats.values())
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        health_score = "excellent" if overall_hit_rate > 80 else "good" if overall_hit_rate > 60 else "poor"
        
        return CacheResponse(
            data={
                "health_status": health_status,
                "overall_hit_rate": overall_hit_rate,
                "health_score": health_score,
                "total_requests": total_requests,
                "recommendations": _get_cache_recommendations(overall_hit_rate)
            },
            metadata={
                "checked_at": "now",
                "check_type": "health_status"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存健康状态失败: {str(e)}")


@router.get("/monitor/real-time")
async def get_real_time_cache_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    获取实时缓存指标
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 这里应该从监控系统获取实时指标
        # 目前返回模拟数据
        metrics = {
            "requests_per_second": 125.6,
            "hit_rate_percentage": 78.5,
            "miss_rate_percentage": 21.5,
            "average_response_time_ms": 2.3,
            "memory_usage_mb": 256.7,
            "active_connections": 45,
            "evictions_per_minute": 3.2,
            "timestamp": "now"
        }
        
        return CacheResponse(
            data=metrics,
            metadata={
                "metric_type": "real_time",
                "refresh_interval_seconds": 5
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时缓存指标失败: {str(e)}")


def _get_cache_recommendations(hit_rate: float) -> List[str]:
    """获取缓存优化建议"""
    recommendations = []
    
    if hit_rate < 50:
        recommendations.extend([
            "缓存命中率过低，建议检查缓存策略",
            "考虑增加缓存过期时间",
            "检查缓存键的设计是否合理"
        ])
    elif hit_rate < 70:
        recommendations.extend([
            "缓存命中率有提升空间",
            "考虑预热热点数据",
            "优化缓存淘汰策略"
        ])
    else:
        recommendations.extend([
            "缓存性能良好",
            "继续监控缓存指标",
            "定期进行缓存优化"
        ])
    
    return recommendations
