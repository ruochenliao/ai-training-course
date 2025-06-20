"""
监控API端点
提供系统监控、性能指标和健康检查接口
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.services.monitoring_service import monitoring_service
from app.core.cache_manager import get_cache_manager
from app.core.graph_store import get_graph_store
from app.models.user import User

logger = logging.getLogger(__name__)

monitoring_router = APIRouter(tags=["系统监控"])


@monitoring_router.get("/health", summary="系统健康检查")
async def system_health_check():
    """
    系统健康检查
    检查各个组件的运行状态
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 检查缓存服务
        try:
            cache_manager = get_cache_manager()
            cache_health = await cache_manager.health_check()
            health_status["components"]["cache"] = cache_health
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # 检查图数据库
        try:
            graph_store = get_graph_store()
            graph_health = await graph_store.health_check()
            health_status["components"]["graph_database"] = graph_health
        except Exception as e:
            health_status["components"]["graph_database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # 检查监控服务
        try:
            current_metrics = await monitoring_service.get_current_metrics()
            health_status["components"]["monitoring"] = {
                "status": "healthy",
                "metrics_available": bool(current_metrics)
            }
        except Exception as e:
            health_status["components"]["monitoring"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # 检查是否有严重告警
        try:
            current_metrics = await monitoring_service.get_current_metrics()
            critical_alerts = [
                alert for alert in current_metrics.get("alerts", [])
                if alert.get("level") == "critical"
            ]
            
            if critical_alerts:
                health_status["status"] = "unhealthy"
                health_status["critical_alerts"] = critical_alerts
        except:
            pass
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@monitoring_router.get("/metrics", summary="获取当前系统指标")
async def get_current_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前系统指标
    包括系统资源、应用性能和模型使用情况
    """
    try:
        metrics = await monitoring_service.get_current_metrics()
        
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "message": "指标获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@monitoring_router.get("/metrics/history", summary="获取历史指标")
async def get_metrics_history(
    hours: int = Query(24, description="历史时间范围（小时）", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """
    获取历史指标数据
    """
    try:
        history = await monitoring_service.get_metrics_history(hours=hours)
        
        return {
            "success": True,
            "history": history,
            "hours": hours,
            "count": len(history),
            "message": f"获取 {hours} 小时内的历史指标"
        }
        
    except Exception as e:
        logger.error(f"获取历史指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史指标失败: {str(e)}")


@monitoring_router.get("/alerts", summary="获取告警信息")
async def get_alerts(
    level: Optional[str] = Query(None, description="告警级别过滤"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统告警信息
    """
    try:
        # 获取当前指标中的告警
        current_metrics = await monitoring_service.get_current_metrics()
        alerts = current_metrics.get("alerts", [])
        
        # 按级别过滤
        if level:
            alerts = [alert for alert in alerts if alert.get("level") == level]
        
        # 限制数量
        alerts = alerts[-limit:]
        
        # 按时间倒序排列
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "alerts": alerts,
            "total": len(alerts),
            "level_filter": level,
            "message": "告警信息获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取告警失败: {str(e)}")


@monitoring_router.get("/performance", summary="获取性能统计")
async def get_performance_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取性能统计信息
    """
    try:
        # 获取缓存统计
        cache_manager = get_cache_manager()
        cache_stats = await cache_manager.get_stats()
        
        # 获取当前指标
        current_metrics = await monitoring_service.get_current_metrics()
        
        # 构建性能统计
        performance_stats = {
            "cache": cache_stats,
            "system": current_metrics.get("system", {}),
            "application": current_metrics.get("application", {}),
            "model": current_metrics.get("model", {}),
            "summary": {
                "total_requests": monitoring_service.performance_counters["total_requests"],
                "total_errors": monitoring_service.performance_counters["total_errors"],
                "model_requests": monitoring_service.performance_counters["model_requests"],
                "uptime": "计算中..."  # TODO: 实现运行时间计算
            }
        }
        
        return {
            "success": True,
            "performance": performance_stats,
            "timestamp": datetime.now().isoformat(),
            "message": "性能统计获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取性能统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@monitoring_router.get("/components", summary="获取组件状态")
async def get_component_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取各个组件的详细状态
    """
    try:
        components = {}
        
        # 缓存组件状态
        try:
            cache_manager = get_cache_manager()
            cache_health = await cache_manager.health_check()
            cache_stats = await cache_manager.get_stats()
            
            components["cache"] = {
                "name": "Redis缓存",
                "status": cache_health["status"],
                "health": cache_health,
                "stats": cache_stats,
                "description": "Redis缓存服务"
            }
        except Exception as e:
            components["cache"] = {
                "name": "Redis缓存",
                "status": "error",
                "error": str(e),
                "description": "Redis缓存服务"
            }
        
        # 图数据库组件状态
        try:
            graph_store = get_graph_store()
            graph_health = await graph_store.health_check()
            graph_stats = await graph_store.get_graph_statistics()
            
            components["graph_database"] = {
                "name": "Neo4j图数据库",
                "status": graph_health["status"],
                "health": graph_health,
                "stats": graph_stats,
                "description": "Neo4j知识图谱数据库"
            }
        except Exception as e:
            components["graph_database"] = {
                "name": "Neo4j图数据库",
                "status": "error",
                "error": str(e),
                "description": "Neo4j知识图谱数据库"
            }
        
        # 监控组件状态
        try:
            current_metrics = await monitoring_service.get_current_metrics()
            
            components["monitoring"] = {
                "name": "监控服务",
                "status": "healthy",
                "metrics": current_metrics,
                "description": "系统性能监控服务"
            }
        except Exception as e:
            components["monitoring"] = {
                "name": "监控服务",
                "status": "error",
                "error": str(e),
                "description": "系统性能监控服务"
            }
        
        # 计算整体状态
        overall_status = "healthy"
        error_count = sum(1 for comp in components.values() if comp["status"] == "error")
        
        if error_count > 0:
            overall_status = "degraded" if error_count < len(components) else "unhealthy"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "components": components,
            "component_count": len(components),
            "healthy_count": sum(1 for comp in components.values() if comp["status"] == "healthy"),
            "error_count": error_count,
            "timestamp": datetime.now().isoformat(),
            "message": "组件状态获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取组件状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取组件状态失败: {str(e)}")


@monitoring_router.post("/alerts/acknowledge", summary="确认告警")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    确认告警
    """
    try:
        # TODO: 实现告警确认逻辑
        # 这里应该更新告警状态，记录确认人和时间
        
        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged_by": current_user.username,
            "acknowledged_at": datetime.now().isoformat(),
            "message": "告警确认成功"
        }
        
    except Exception as e:
        logger.error(f"确认告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@monitoring_router.get("/dashboard", summary="获取监控仪表板数据")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    """
    获取监控仪表板所需的所有数据
    """
    try:
        # 获取当前指标
        current_metrics = await monitoring_service.get_current_metrics()
        
        # 获取组件状态
        components_response = await get_component_status(current_user)
        components = components_response["components"]
        
        # 获取最近的告警
        alerts = current_metrics.get("alerts", [])[-10:]
        
        # 构建仪表板数据
        dashboard_data = {
            "overview": {
                "system_status": components_response["overall_status"],
                "total_requests": monitoring_service.performance_counters["total_requests"],
                "error_rate": current_metrics.get("application", {}).get("error_rate", 0),
                "avg_response_time": current_metrics.get("application", {}).get("avg_response_time", 0),
                "cache_hit_rate": current_metrics.get("application", {}).get("cache_hit_rate", 0)
            },
            "system_metrics": current_metrics.get("system", {}),
            "application_metrics": current_metrics.get("application", {}),
            "model_metrics": current_metrics.get("model", {}),
            "components": components,
            "recent_alerts": alerts,
            "alert_counts": {
                "critical": len([a for a in alerts if a.get("level") == "critical"]),
                "warning": len([a for a in alerts if a.get("level") == "warning"]),
                "info": len([a for a in alerts if a.get("level") == "info"])
            }
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat(),
            "message": "仪表板数据获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@monitoring_router.get("/export", summary="导出监控数据")
async def export_monitoring_data(
    format: str = Query("json", description="导出格式", regex="^(json|csv)$"),
    hours: int = Query(24, description="时间范围（小时）", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """
    导出监控数据
    """
    try:
        # 获取历史数据
        history = await monitoring_service.get_metrics_history(hours=hours)
        
        if format == "json":
            return {
                "success": True,
                "data": history,
                "format": "json",
                "hours": hours,
                "count": len(history),
                "exported_at": datetime.now().isoformat()
            }
        elif format == "csv":
            # TODO: 实现CSV格式导出
            return {
                "success": False,
                "message": "CSV格式导出功能开发中"
            }
        
    except Exception as e:
        logger.error(f"导出监控数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")
