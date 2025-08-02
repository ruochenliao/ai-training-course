"""
健康检查API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import time
import psutil
from typing import Dict, Any

from app.db.session import get_db, check_db_connection
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """详细健康检查"""
    
    # 检查数据库连接
    db_status = "healthy" if check_db_connection() else "unhealthy"
    
    # 获取系统信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": {
                "status": db_status,
                "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "unknown"
            },
            "redis": {
                "status": "unknown",  # TODO: 实现Redis健康检查
                "url": settings.REDIS_URL.split("@")[1] if "@" in settings.REDIS_URL else "unknown"
            },
            "milvus": {
                "status": "unknown",  # TODO: 实现Milvus健康检查
                "host": f"{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
            }
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查"""
    # 检查关键服务是否就绪
    db_ready = check_db_connection()
    
    # TODO: 添加其他服务的就绪检查
    # redis_ready = check_redis_connection()
    # milvus_ready = check_milvus_connection()
    
    all_ready = db_ready  # and redis_ready and milvus_ready
    
    return {
        "ready": all_ready,
        "timestamp": time.time(),
        "services": {
            "database": db_ready,
            # "redis": redis_ready,
            # "milvus": milvus_ready
        }
    }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """存活检查"""
    return {
        "alive": True,
        "timestamp": time.time(),
        "uptime": time.time()  # TODO: 实现真实的运行时间计算
    }
