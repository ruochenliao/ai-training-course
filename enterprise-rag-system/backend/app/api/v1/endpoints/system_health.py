"""
系统健康检查API端点 - 第四阶段核心功能
提供系统状态、性能指标、健康检查等API
"""

import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from loguru import logger

from app.core.response import success_response, error_response
from app.core.security import get_current_user, require_permissions
from app.models.user import User
from app.services.system_monitor import system_monitor, SystemMetrics, ServiceHealth, ApplicationMetrics

router = APIRouter(prefix="/system", tags=["系统健康检查"])


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="系统状态: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="检查时间")
    services: Dict[str, Dict[str, Any]] = Field(..., description="各服务状态")
    system_metrics: Dict[str, Any] = Field(..., description="系统指标")
    application_metrics: Dict[str, Any] = Field(..., description="应用指标")


class MetricsResponse(BaseModel):
    """指标响应模型"""
    current_metrics: Dict[str, Any]
    historical_metrics: List[Dict[str, Any]]
    time_range: str
    data_points: int


class ServiceStatusResponse(BaseModel):
    """服务状态响应模型"""
    service_name: str
    status: str
    response_time: float
    last_check: str
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@router.get("/health", response_model=HealthCheckResponse, summary="系统健康检查")
async def system_health_check(
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """
    系统健康检查
    
    返回系统整体健康状态，包括：
    - 各个服务的健康状态
    - 系统资源使用情况
    - 应用性能指标
    """
    try:
        # 获取系统指标
        system_metrics = system_monitor.get_system_metrics()
        
        # 获取服务健康状态
        health_status = system_monitor.get_health_status()
        
        # 获取应用指标
        app_metrics = await system_monitor.get_application_metrics()
        
        # 计算整体系统状态
        overall_status = _calculate_overall_status(health_status, system_metrics)
        
        # 构建响应
        services_status = {}
        for service_name, health in health_status.items():
            services_status[service_name] = {
                "status": health.status,
                "response_time": health.response_time,
                "last_check": health.last_check,
                "error_message": health.error_message,
                "details": health.details
            }
        
        response = HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services=services_status,
            system_metrics={
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
                "process_count": system_metrics.process_count,
                "uptime": system_metrics.uptime
            },
            application_metrics={
                "active_users": app_metrics.active_users,
                "total_requests": app_metrics.total_requests,
                "error_rate": app_metrics.error_rate,
                "avg_response_time": app_metrics.avg_response_time,
                "cache_hit_rate": app_metrics.cache_hit_rate
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/metrics", summary="获取系统指标")
async def get_system_metrics(
    hours: int = Query(default=1, ge=1, le=24, description="获取最近N小时的数据"),
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """获取系统性能指标"""
    try:
        # 获取当前指标
        current_metrics = system_monitor.get_system_metrics()
        
        # 获取历史指标
        historical_metrics = system_monitor.get_historical_metrics(hours)
        
        response = MetricsResponse(
            current_metrics={
                "timestamp": current_metrics.timestamp,
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "memory_used": current_metrics.memory_used,
                "memory_total": current_metrics.memory_total,
                "disk_percent": current_metrics.disk_percent,
                "disk_used": current_metrics.disk_used,
                "disk_total": current_metrics.disk_total,
                "network_sent": current_metrics.network_sent,
                "network_recv": current_metrics.network_recv,
                "process_count": current_metrics.process_count,
                "load_average": current_metrics.load_average,
                "uptime": current_metrics.uptime
            },
            historical_metrics=historical_metrics,
            time_range=f"{hours}h",
            data_points=len(historical_metrics)
        )
        
        return success_response(
            data=response.dict(),
            message=f"成功获取最近{hours}小时的系统指标"
        )
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return error_response(message=f"获取系统指标失败: {str(e)}")


@router.get("/services/{service_name}/health", summary="获取特定服务健康状态")
async def get_service_health(
    service_name: str,
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """获取特定服务的健康状态"""
    try:
        # 支持的服务列表
        supported_services = ["database", "redis", "milvus", "neo4j"]
        
        if service_name not in supported_services:
            return error_response(
                message=f"不支持的服务: {service_name}. 支持的服务: {supported_services}"
            )
        
        # 执行健康检查
        check_functions = {
            "database": system_monitor.check_database_health,
            "redis": system_monitor.check_redis_health,
            "milvus": system_monitor.check_milvus_health,
            "neo4j": system_monitor.check_neo4j_health
        }
        
        health = await system_monitor.check_service_health(
            service_name, 
            check_functions[service_name]
        )
        
        response = ServiceStatusResponse(
            service_name=health.service_name,
            status=health.status,
            response_time=health.response_time,
            last_check=health.last_check,
            error_message=health.error_message,
            details=health.details
        )
        
        return success_response(
            data=response.dict(),
            message=f"服务{service_name}健康检查完成"
        )
        
    except Exception as e:
        logger.error(f"服务{service_name}健康检查失败: {e}")
        return error_response(message=f"服务健康检查失败: {str(e)}")


@router.get("/services/health", summary="获取所有服务健康状态")
async def get_all_services_health(
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """获取所有服务的健康状态"""
    try:
        health_status = system_monitor.get_health_status()
        
        services_data = []
        for service_name, health in health_status.items():
            services_data.append({
                "service_name": service_name,
                "status": health.status,
                "response_time": health.response_time,
                "last_check": health.last_check,
                "error_message": health.error_message,
                "details": health.details
            })
        
        return success_response(
            data={"services": services_data},
            message="成功获取所有服务健康状态"
        )
        
    except Exception as e:
        logger.error(f"获取服务健康状态失败: {e}")
        return error_response(message=f"获取服务健康状态失败: {str(e)}")


@router.get("/application/metrics", summary="获取应用指标")
async def get_application_metrics(
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """获取应用性能指标"""
    try:
        app_metrics = await system_monitor.get_application_metrics()
        
        return success_response(
            data={
                "active_users": app_metrics.active_users,
                "total_requests": app_metrics.total_requests,
                "error_rate": app_metrics.error_rate,
                "avg_response_time": app_metrics.avg_response_time,
                "database_connections": app_metrics.database_connections,
                "cache_hit_rate": app_metrics.cache_hit_rate,
                "queue_size": app_metrics.queue_size,
                "timestamp": datetime.utcnow().isoformat()
            },
            message="成功获取应用指标"
        )
        
    except Exception as e:
        logger.error(f"获取应用指标失败: {e}")
        return error_response(message=f"获取应用指标失败: {str(e)}")


@router.post("/monitoring/start", summary="启动系统监控")
async def start_monitoring(
    current_user: User = Depends(require_permissions(["system:admin"]))
):
    """启动系统监控"""
    try:
        if system_monitor.is_monitoring:
            return success_response(
                data={"status": "already_running"},
                message="系统监控已在运行中"
            )
        
        # 在后台启动监控
        asyncio.create_task(system_monitor.start_monitoring())
        
        return success_response(
            data={"status": "started"},
            message="系统监控已启动"
        )
        
    except Exception as e:
        logger.error(f"启动系统监控失败: {e}")
        return error_response(message=f"启动系统监控失败: {str(e)}")


@router.post("/monitoring/stop", summary="停止系统监控")
async def stop_monitoring(
    current_user: User = Depends(require_permissions(["system:admin"]))
):
    """停止系统监控"""
    try:
        system_monitor.stop_monitoring()
        
        return success_response(
            data={"status": "stopped"},
            message="系统监控已停止"
        )
        
    except Exception as e:
        logger.error(f"停止系统监控失败: {e}")
        return error_response(message=f"停止系统监控失败: {str(e)}")


@router.get("/monitoring/status", summary="获取监控状态")
async def get_monitoring_status(
    current_user: User = Depends(require_permissions(["system:read"]))
):
    """获取监控运行状态"""
    try:
        return success_response(
            data={
                "is_monitoring": system_monitor.is_monitoring,
                "monitoring_interval": system_monitor.monitoring_interval,
                "metrics_retention_hours": system_monitor.metrics_retention_hours,
                "redis_available": system_monitor.redis_client is not None
            },
            message="成功获取监控状态"
        )
        
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        return error_response(message=f"获取监控状态失败: {str(e)}")


def _calculate_overall_status(health_status: Dict[str, ServiceHealth], system_metrics: SystemMetrics) -> str:
    """计算系统整体状态"""
    # 检查服务状态
    unhealthy_services = [name for name, health in health_status.items() if health.status == "unhealthy"]
    degraded_services = [name for name, health in health_status.items() if health.status == "degraded"]
    
    # 检查系统资源
    high_resource_usage = (
        system_metrics.cpu_percent > 90 or 
        system_metrics.memory_percent > 95 or 
        system_metrics.disk_percent > 90
    )
    
    # 计算整体状态
    if unhealthy_services or high_resource_usage:
        return "unhealthy"
    elif degraded_services or system_metrics.cpu_percent > 80 or system_metrics.memory_percent > 85:
        return "degraded"
    else:
        return "healthy"
