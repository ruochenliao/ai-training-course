# Copyright (c) 2025 左岚. All rights reserved.
"""
监控和性能API端点
"""

# Standard library imports
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

# Local application imports
from app.api.deps import get_current_active_superuser
from app.core.simple_cache import cache_manager
from app.core.database_pool import db_pool_manager
from app.core.logging_config import get_logger
from app.core.log_aggregator import log_aggregator
from app.core.metrics import metrics_manager
from app.core.tracing import tracing_manager
from app.core.celery_app import task_manager
from app.db.session import get_db
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """系统健康检查"""
    try:
        # 检查各个组件的健康状态
        db_health = db_pool_manager.health_check()
        cache_health = cache_manager.health_check()
        celery_health = task_manager.health_check()
        
        # 综合健康状态
        overall_status = "healthy"
        if (db_health.get('status') != 'healthy' or 
            cache_health.get('status') != 'healthy' or 
            celery_health.get('status') != 'healthy'):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_health,
                "cache": cache_health,
                "task_queue": celery_health
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")


@router.get("/metrics")
async def get_metrics(response: Response):
    """获取Prometheus格式的指标"""
    try:
        metrics_data = metrics_manager.get_metrics()
        response.headers["Content-Type"] = "text/plain; version=0.0.4; charset=utf-8"
        return Response(content=metrics_data, media_type="text/plain")
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标失败")


@router.get("/metrics/summary")
async def get_metrics_summary(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取指标摘要"""
    try:
        return metrics_manager.get_metrics_summary()
    except Exception as e:
        logger.error(f"获取指标摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标摘要失败")


@router.get("/performance/database")
async def get_database_performance(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取数据库性能指标"""
    try:
        return db_pool_manager.get_pool_stats()
    except Exception as e:
        logger.error(f"获取数据库性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据库性能指标失败")


@router.get("/performance/cache")
async def get_cache_performance(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取缓存性能指标"""
    try:
        return cache_manager.get_stats()
    except Exception as e:
        logger.error(f"获取缓存性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取缓存性能指标失败")


@router.get("/performance/tasks")
async def get_task_performance(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取任务队列性能指标"""
    try:
        queue_stats = task_manager.get_queue_stats()
        worker_stats = task_manager.get_worker_stats()
        
        return {
            "queue_stats": queue_stats,
            "worker_stats": worker_stats
        }
    except Exception as e:
        logger.error(f"获取任务性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务性能指标失败")


@router.get("/logs/stats")
async def get_log_stats(
    hours: int = 24,
    current_user: User = Depends(get_current_active_superuser)
):
    """获取日志统计信息"""
    try:
        return log_aggregator.get_log_stats(hours)
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取日志统计失败")


@router.get("/logs/errors")
async def get_error_analysis(
    hours: int = 24,
    current_user: User = Depends(get_current_active_superuser)
):
    """获取错误分析报告"""
    try:
        return log_aggregator.get_error_analysis(hours)
    except Exception as e:
        logger.error(f"获取错误分析失败: {e}")
        raise HTTPException(status_code=500, detail="获取错误分析失败")


@router.get("/logs/performance")
async def get_performance_report(
    hours: int = 24,
    current_user: User = Depends(get_current_active_superuser)
):
    """获取性能报告"""
    try:
        return log_aggregator.get_performance_report(hours)
    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能报告失败")


@router.get("/tracing/stats")
async def get_tracing_stats(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取追踪统计信息"""
    try:
        return tracing_manager.get_stats()
    except Exception as e:
        logger.error(f"获取追踪统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取追踪统计失败")


@router.get("/tracing/trace/{trace_id}")
async def get_trace(
    trace_id: str,
    current_user: User = Depends(get_current_active_superuser)
):
    """获取特定追踪信息"""
    try:
        trace_data = tracing_manager.get_trace(trace_id)
        if not trace_data:
            raise HTTPException(status_code=404, detail="追踪信息未找到")
        
        return {
            "trace_id": trace_id,
            "spans": [span.to_dict() for span in trace_data]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取追踪信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取追踪信息失败")


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """清除缓存"""
    try:
        if pattern:
            cleared = cache_manager.clear_pattern(pattern)
            return {"message": f"清除了 {cleared} 个匹配的缓存项", "pattern": pattern}
        else:
            # 这里可以实现清除所有缓存的逻辑
            return {"message": "缓存清除功能需要指定模式"}
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail="清除缓存失败")


@router.post("/logs/cleanup")
async def cleanup_logs(
    days: int = 30,
    current_user: User = Depends(get_current_active_superuser)
):
    """清理旧日志"""
    try:
        log_aggregator.cleanup_old_logs(days)
        return {"message": f"清理了 {days} 天前的日志文件"}
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(status_code=500, detail="清理日志失败")


@router.post("/tracing/cleanup")
async def cleanup_traces(
    max_traces: int = 1000,
    current_user: User = Depends(get_current_active_superuser)
):
    """清理旧追踪数据"""
    try:
        tracing_manager.cleanup_old_traces(max_traces)
        return {"message": f"保留了最新的 {max_traces} 个追踪"}
    except Exception as e:
        logger.error(f"清理追踪数据失败: {e}")
        raise HTTPException(status_code=500, detail="清理追踪数据失败")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_superuser)
):
    """获取监控仪表板数据"""
    try:
        # 收集所有监控数据
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "health": {
                "database": db_pool_manager.health_check(),
                "cache": cache_manager.health_check(),
                "task_queue": task_manager.health_check()
            },
            "performance": {
                "database": db_pool_manager.get_pool_stats(),
                "cache": cache_manager.get_stats(),
                "tasks": task_manager.get_queue_stats()
            },
            "logs": {
                "stats": log_aggregator.get_log_stats(24),
                "errors": log_aggregator.get_error_analysis(24)
            },
            "tracing": tracing_manager.get_stats(),
            "metrics": metrics_manager.get_metrics_summary()
        }
        
        return dashboard_data
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取仪表板数据失败")


@router.post("/database/optimize")
async def optimize_database_pool(
    current_user: User = Depends(get_current_active_superuser)
):
    """优化数据库连接池"""
    try:
        db_pool_manager.optimize_pool()
        return {"message": "数据库连接池优化完成"}
    except Exception as e:
        logger.error(f"优化数据库连接池失败: {e}")
        raise HTTPException(status_code=500, detail="优化数据库连接池失败")


@router.post("/database/reset-stats")
async def reset_database_stats(
    current_user: User = Depends(get_current_active_superuser)
):
    """重置数据库统计信息"""
    try:
        db_pool_manager.reset_stats()
        return {"message": "数据库统计信息已重置"}
    except Exception as e:
        logger.error(f"重置数据库统计失败: {e}")
        raise HTTPException(status_code=500, detail="重置数据库统计失败")
