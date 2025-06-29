"""
监控API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core import get_current_user, PermissionChecker
from app.core.error_monitoring import get_error_monitor
from app.models import User

router = APIRouter()

# 权限检查器
require_monitoring_access = PermissionChecker("system:monitoring")


class ErrorStatisticsResponse(BaseModel):
    """错误统计响应"""
    time_window: int
    total_errors: int
    error_breakdown: Dict[str, Any]
    timestamp: float


class PerformanceMetricsResponse(BaseModel):
    """性能指标响应"""
    time_window: int
    total_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    error_count: int
    timestamp: float


class TopErrorsResponse(BaseModel):
    """热门错误响应"""
    errors: List[Dict[str, Any]]


@router.get("/errors/statistics", response_model=ErrorStatisticsResponse, summary="获取错误统计")
async def get_error_statistics(
    time_window: int = Query(3600, description="时间窗口（秒）", ge=60, le=86400),
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取错误统计信息
    
    - **time_window**: 统计时间窗口，默认1小时
    """
    error_monitor = get_error_monitor()
    stats = error_monitor.get_error_statistics(time_window)
    
    return ErrorStatisticsResponse(**stats)


@router.get("/performance/metrics", response_model=PerformanceMetricsResponse, summary="获取性能指标")
async def get_performance_metrics(
    time_window: int = Query(3600, description="时间窗口（秒）", ge=60, le=86400),
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取性能指标
    
    - **time_window**: 统计时间窗口，默认1小时
    """
    error_monitor = get_error_monitor()
    metrics = error_monitor.get_performance_metrics(time_window)
    
    return PerformanceMetricsResponse(**metrics)


@router.get("/errors/top", response_model=TopErrorsResponse, summary="获取热门错误")
async def get_top_errors(
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    time_window: int = Query(3600, description="时间窗口（秒）", ge=60, le=86400),
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取最频繁的错误
    
    - **limit**: 返回的错误数量
    - **time_window**: 统计时间窗口，默认1小时
    """
    error_monitor = get_error_monitor()
    top_errors = error_monitor.get_top_errors(limit, time_window)
    
    return TopErrorsResponse(errors=top_errors)


@router.get("/health/detailed", summary="详细健康检查")
async def get_detailed_health(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取详细的系统健康状态
    """
    from app.services.health import HealthService
    
    health_service = HealthService()
    error_monitor = get_error_monitor()
    
    # 获取基础健康检查
    health_status = await health_service.check_all()
    
    # 获取性能指标
    performance_metrics = error_monitor.get_performance_metrics(300)  # 5分钟窗口
    error_stats = error_monitor.get_error_statistics(300)
    
    # 判断系统整体状态
    overall_healthy = (
        health_status["status"] == "healthy" and
        performance_metrics["error_rate"] < 0.05 and  # 错误率小于5%
        performance_metrics["p95_response_time"] < 2.0  # 95分位响应时间小于2秒
    )
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": health_status["timestamp"],
        "services": health_status["checks"],
        "performance": {
            "response_time": {
                "avg": performance_metrics["avg_response_time"],
                "p95": performance_metrics["p95_response_time"],
                "p99": performance_metrics["p99_response_time"],
            },
            "throughput": {
                "requests_per_minute": performance_metrics["total_requests"] / 5,  # 5分钟窗口
                "error_rate": performance_metrics["error_rate"],
            }
        },
        "errors": {
            "total_errors": error_stats["total_errors"],
            "error_breakdown": error_stats["error_breakdown"],
        },
        "alerts": {
            "high_error_rate": performance_metrics["error_rate"] > 0.05,
            "slow_response": performance_metrics["p95_response_time"] > 2.0,
            "service_down": health_status["status"] != "healthy",
        }
    }


@router.get("/metrics/prometheus", summary="Prometheus指标")
async def get_prometheus_metrics(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取Prometheus格式的指标
    """
    error_monitor = get_error_monitor()
    
    # 获取指标数据
    performance_metrics = error_monitor.get_performance_metrics(300)
    error_stats = error_monitor.get_error_statistics(300)
    
    # 生成Prometheus格式的指标
    metrics_lines = []
    
    # 响应时间指标
    metrics_lines.append(f"# HELP http_request_duration_seconds HTTP request duration in seconds")
    metrics_lines.append(f"# TYPE http_request_duration_seconds histogram")
    metrics_lines.append(f"http_request_duration_seconds_avg {performance_metrics['avg_response_time']}")
    metrics_lines.append(f"http_request_duration_seconds_p95 {performance_metrics['p95_response_time']}")
    metrics_lines.append(f"http_request_duration_seconds_p99 {performance_metrics['p99_response_time']}")
    
    # 请求总数
    metrics_lines.append(f"# HELP http_requests_total Total number of HTTP requests")
    metrics_lines.append(f"# TYPE http_requests_total counter")
    metrics_lines.append(f"http_requests_total {performance_metrics['total_requests']}")
    
    # 错误率
    metrics_lines.append(f"# HELP http_request_error_rate HTTP request error rate")
    metrics_lines.append(f"# TYPE http_request_error_rate gauge")
    metrics_lines.append(f"http_request_error_rate {performance_metrics['error_rate']}")
    
    # 错误计数
    metrics_lines.append(f"# HELP http_errors_total Total number of HTTP errors")
    metrics_lines.append(f"# TYPE http_errors_total counter")
    for error_code, stats in error_stats["error_breakdown"].items():
        metrics_lines.append(f'http_errors_total{{error_code="{error_code}"}} {stats["count"]}')
    
    return "\n".join(metrics_lines)


@router.post("/monitoring/clear-data", summary="清理监控数据")
async def clear_monitoring_data(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    清理过期的监控数据
    """
    error_monitor = get_error_monitor()
    error_monitor.clear_old_data()
    
    return {
        "success": True,
        "message": "监控数据已清理",
        "timestamp": error_monitor.get_performance_metrics()["timestamp"]
    }


@router.get("/monitoring/config", summary="获取监控配置")
async def get_monitoring_config(
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    获取监控系统配置
    """
    error_monitor = get_error_monitor()
    
    return {
        "max_history": error_monitor.max_history,
        "time_window": error_monitor.time_window,
        "alert_thresholds": error_monitor.alert_thresholds,
        "alert_states": dict(error_monitor.alert_states),
        "data_counts": {
            "error_history": len(error_monitor.error_history),
            "response_times": len(error_monitor.response_times),
            "error_types": len(error_monitor.error_details),
        }
    }


@router.put("/monitoring/config", summary="更新监控配置")
async def update_monitoring_config(
    config: Dict[str, Any],
    current_user: User = Depends(require_monitoring_access)
) -> Any:
    """
    更新监控系统配置
    """
    error_monitor = get_error_monitor()
    
    # 更新告警阈值
    if "alert_thresholds" in config:
        error_monitor.alert_thresholds.update(config["alert_thresholds"])
    
    # 更新时间窗口
    if "time_window" in config:
        error_monitor.time_window = config["time_window"]
    
    return {
        "success": True,
        "message": "监控配置已更新",
        "config": {
            "time_window": error_monitor.time_window,
            "alert_thresholds": error_monitor.alert_thresholds,
        }
    }
