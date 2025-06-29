"""
监控仪表板API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.core import get_current_user, PermissionChecker
from app.services.health import HealthService
from app.services.business_metrics import get_business_metrics_service
from app.services.alert_service import get_alert_service, AlertLevel, AlertType
from app.core.error_monitoring import get_error_monitor
from app.core.permission_cache import get_permission_cache
from app.core.permission_audit import get_permission_auditor
from app.models import User

router = APIRouter()

# 权限检查器
require_monitoring_access = PermissionChecker("monitoring:view")
require_monitoring_admin = PermissionChecker("monitoring:admin")


class DashboardOverviewResponse(BaseModel):
    """仪表板概览响应"""
    system_status: str
    health_checks: Dict[str, Any]
    performance_summary: Dict[str, Any]
    business_summary: Dict[str, Any]
    alert_summary: Dict[str, Any]
    timestamp: float


class SystemHealthResponse(BaseModel):
    """系统健康响应"""
    overall_status: str
    components: Dict[str, Any]
    uptime: float
    last_check: float


class PerformanceMetricsResponse(BaseModel):
    """性能指标响应"""
    response_times: Dict[str, float]
    throughput: Dict[str, int]
    error_rates: Dict[str, float]
    cache_performance: Dict[str, Any]


@router.get("/overview", response_model=DashboardOverviewResponse, summary="获取监控概览")
async def get_monitoring_overview(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取监控仪表板概览信息
    """
    import time
    
    # 获取系统健康状态
    health_service = HealthService()
    health_status = await health_service.check_all()
    
    # 获取性能指标
    error_monitor = get_error_monitor()
    performance_metrics = error_monitor.get_performance_metrics(3600)  # 1小时
    
    # 获取业务指标
    business_service = get_business_metrics_service()
    business_metrics = await business_service.collect_all_metrics()
    
    # 获取告警信息
    alert_service = get_alert_service()
    active_alerts = alert_service.get_active_alerts()
    alert_stats = alert_service.get_stats()
    
    # 判断系统整体状态
    system_status = "healthy"
    if health_status["status"] != "healthy":
        system_status = "unhealthy"
    elif len(active_alerts) > 0:
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        if critical_alerts:
            system_status = "critical"
        else:
            system_status = "warning"
    
    return DashboardOverviewResponse(
        system_status=system_status,
        health_checks={
            "status": health_status["status"],
            "components": len(health_status["checks"]),
            "healthy_components": len([
                c for c in health_status["checks"].values() 
                if c.get("status") == "healthy"
            ])
        },
        performance_summary={
            "avg_response_time": performance_metrics.get("avg_response_time", 0),
            "p95_response_time": performance_metrics.get("p95_response_time", 0),
            "error_rate": performance_metrics.get("error_rate", 0),
            "total_requests": performance_metrics.get("total_requests", 0)
        },
        business_summary={
            "total_users": business_metrics.user_metrics.get("total_users", 0),
            "active_users_24h": business_metrics.user_metrics.get("active_users_24h", 0),
            "total_knowledge_bases": business_metrics.knowledge_base_metrics.get("total_knowledge_bases", 0),
            "total_documents": business_metrics.document_metrics.get("total_documents", 0),
            "total_conversations": business_metrics.conversation_metrics.get("total_conversations", 0)
        },
        alert_summary={
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "total_alerts_24h": alert_stats.get("total_alerts", 0)
        },
        timestamp=time.time()
    )


@router.get("/health", response_model=SystemHealthResponse, summary="获取系统健康状态")
async def get_system_health(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取详细的系统健康状态
    """
    import time
    
    health_service = HealthService()
    health_status = await health_service.check_all()
    
    # 计算系统运行时间（简化版本）
    uptime = time.time() - health_status.get("start_time", time.time())
    
    return SystemHealthResponse(
        overall_status=health_status["status"],
        components=health_status["checks"],
        uptime=uptime,
        last_check=health_status["timestamp"]
    )


@router.get("/performance", response_model=PerformanceMetricsResponse, summary="获取性能指标")
async def get_performance_metrics(
    time_window: int = Query(3600, ge=300, le=86400, description="时间窗口（秒）"),
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取系统性能指标
    """
    # 获取错误监控指标
    error_monitor = get_error_monitor()
    performance_metrics = error_monitor.get_performance_metrics(time_window)
    
    # 获取缓存性能指标
    permission_cache = get_permission_cache()
    cache_stats = permission_cache.get_stats()
    
    return PerformanceMetricsResponse(
        response_times={
            "avg": performance_metrics.get("avg_response_time", 0),
            "p95": performance_metrics.get("p95_response_time", 0),
            "p99": performance_metrics.get("p99_response_time", 0)
        },
        throughput={
            "requests_per_hour": performance_metrics.get("total_requests", 0),
            "requests_per_minute": performance_metrics.get("total_requests", 0) / (time_window / 60)
        },
        error_rates={
            "overall": performance_metrics.get("error_rate", 0),
            "4xx_rate": 0,  # 可以从详细统计中获取
            "5xx_rate": 0
        },
        cache_performance={
            "hit_rate": cache_stats.get("hit_rate", 0),
            "total_hits": cache_stats.get("hits", 0),
            "total_misses": cache_stats.get("misses", 0),
            "cache_size": cache_stats.get("total_cache_size", 0)
        }
    )


@router.get("/business-metrics", summary="获取业务指标")
async def get_business_metrics(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取业务相关指标
    """
    business_service = get_business_metrics_service()
    metrics = await business_service.collect_all_metrics()
    
    return {
        "user_metrics": metrics.user_metrics,
        "knowledge_base_metrics": metrics.knowledge_base_metrics,
        "document_metrics": metrics.document_metrics,
        "conversation_metrics": metrics.conversation_metrics,
        "system_metrics": metrics.system_metrics,
        "timestamp": metrics.timestamp
    }


@router.get("/alerts", summary="获取告警信息")
async def get_alerts(
    alert_type: Optional[str] = Query(None, description="告警类型"),
    level: Optional[str] = Query(None, description="告警级别"),
    active_only: bool = Query(True, description="仅显示活跃告警"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取告警信息
    """
    alert_service = get_alert_service()
    
    # 转换参数
    alert_type_enum = None
    if alert_type:
        try:
            alert_type_enum = AlertType(alert_type)
        except ValueError:
            pass
    
    level_enum = None
    if level:
        try:
            level_enum = AlertLevel(level)
        except ValueError:
            pass
    
    # 获取告警
    if active_only:
        alerts = alert_service.get_active_alerts(alert_type_enum, level_enum)
    else:
        alerts = alert_service.get_alert_history(24, limit)
        if alert_type_enum:
            alerts = [a for a in alerts if a.type == alert_type_enum]
        if level_enum:
            alerts = [a for a in alerts if a.level == level_enum]
    
    # 限制返回数量
    alerts = alerts[:limit]
    
    # 转换为可序列化格式
    result = []
    for alert in alerts:
        result.append({
            "id": alert.id,
            "type": alert.type.value,
            "level": alert.level.value,
            "title": alert.title,
            "message": alert.message,
            "details": alert.details,
            "timestamp": alert.timestamp,
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at,
            "resolved_by": alert.resolved_by
        })
    
    return {
        "alerts": result,
        "total": len(result),
        "stats": alert_service.get_stats()
    }


@router.post("/alerts/{alert_id}/resolve", summary="解决告警")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_monitoring_admin)
) -> Any:
    """
    解决指定告警
    """
    alert_service = get_alert_service()
    success = alert_service.resolve_alert(alert_id, current_user.username)
    
    if success:
        return {
            "success": True,
            "message": f"告警 {alert_id} 已解决",
            "resolved_by": current_user.username
        }
    else:
        return {
            "success": False,
            "message": f"告警 {alert_id} 不存在或已解决"
        }


@router.post("/check-alerts", summary="手动检查告警")
async def manual_alert_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_monitoring_admin)
) -> Any:
    """
    手动触发告警检查
    """
    async def run_alert_check():
        try:
            # 收集系统数据
            health_service = HealthService()
            health_data = await health_service.check_all()
            
            error_monitor = get_error_monitor()
            performance_data = error_monitor.get_performance_metrics(300)
            
            business_service = get_business_metrics_service()
            business_data = await business_service.collect_all_metrics()
            
            # 组合数据
            check_data = {
                **health_data.get("checks", {}),
                "performance": performance_data,
                "business": {
                    "document_metrics": business_data.document_metrics,
                    "user_metrics": business_data.user_metrics
                }
            }
            
            # 检查告警
            alert_service = get_alert_service()
            triggered_alerts = await alert_service.check_alerts(check_data)
            
            logger.info(f"手动告警检查完成，触发 {len(triggered_alerts)} 个告警")
            
        except Exception as e:
            logger.error(f"手动告警检查失败: {e}")
    
    # 在后台执行告警检查
    background_tasks.add_task(run_alert_check)
    
    return {
        "success": True,
        "message": "告警检查已启动",
        "triggered_by": current_user.username
    }


@router.get("/real-time-stats", summary="获取实时统计")
async def get_real_time_stats(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取实时系统统计信息
    """
    import time
    
    # 获取各种实时统计
    error_monitor = get_error_monitor()
    permission_cache = get_permission_cache()
    permission_auditor = get_permission_auditor()
    alert_service = get_alert_service()
    
    # 最近5分钟的性能指标
    recent_performance = error_monitor.get_performance_metrics(300)
    
    # 缓存统计
    cache_stats = permission_cache.get_stats()
    
    # 审计统计
    audit_stats = permission_auditor.get_stats()
    
    # 告警统计
    alert_stats = alert_service.get_stats()
    active_alerts = len(alert_service.get_active_alerts())
    
    return {
        "timestamp": time.time(),
        "performance": {
            "requests_5min": recent_performance.get("total_requests", 0),
            "avg_response_time": recent_performance.get("avg_response_time", 0),
            "error_rate": recent_performance.get("error_rate", 0)
        },
        "cache": {
            "hit_rate": cache_stats.get("hit_rate", 0),
            "total_size": cache_stats.get("total_cache_size", 0)
        },
        "audit": {
            "total_logs": audit_stats.get("total_logs", 0),
            "success_rate": audit_stats.get("success_rate", 0)
        },
        "alerts": {
            "active": active_alerts,
            "total": alert_stats.get("total_alerts", 0)
        }
    }


@router.post("/cleanup", summary="清理监控数据")
async def cleanup_monitoring_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_monitoring_admin)
) -> Any:
    """
    清理过期的监控数据
    """
    async def run_cleanup():
        try:
            # 清理错误监控数据
            error_monitor = get_error_monitor()
            error_monitor.clear_old_data()
            
            # 清理审计日志
            permission_auditor = get_permission_auditor()
            audit_cleared = permission_auditor.clear_old_logs(168)  # 7天
            
            # 清理告警数据
            alert_service = get_alert_service()
            alerts_cleared = alert_service.clear_old_alerts(168)  # 7天
            
            logger.info(f"监控数据清理完成: 审计日志 {audit_cleared} 条, 告警 {alerts_cleared} 条")
            
        except Exception as e:
            logger.error(f"监控数据清理失败: {e}")
    
    # 在后台执行清理
    background_tasks.add_task(run_cleanup)
    
    return {
        "success": True,
        "message": "监控数据清理已启动",
        "initiated_by": current_user.username
    }
