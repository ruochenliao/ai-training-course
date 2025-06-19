"""
健康检查服务
"""

import asyncio
import time
from typing import Dict, Any

from tortoise import connections
from loguru import logger

from app.core.config import settings


class HealthService:
    """健康检查服务类"""
    
    async def check_all(self) -> Dict[str, Any]:
        """
        检查所有服务的健康状态
        """
        start_time = time.time()
        
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "milvus": await self.check_milvus(),
            "neo4j": await self.check_neo4j(),
            "minio": await self.check_minio(),
        }
        
        # 计算总体状态
        all_healthy = all(check["status"] == "healthy" for check in checks.values())
        overall_status = "healthy" if all_healthy else "unhealthy"
        
        # 计算检查耗时
        check_duration = time.time() - start_time
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "duration": round(check_duration, 3),
            "checks": checks,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """
        检查数据库连接
        """
        try:
            start_time = time.time()
            
            # 获取数据库连接
            conn = connections.get("default")
            
            # 执行简单查询
            await conn.execute_query("SELECT 1")
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "数据库连接正常",
                "duration": round(duration, 3),
                "details": {
                    "type": "MySQL",
                    "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "unknown"
                }
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"数据库连接失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """
        检查Redis连接
        """
        try:
            import redis.asyncio as redis
            
            start_time = time.time()
            
            # 创建Redis连接
            r = redis.from_url(settings.REDIS_URL)
            
            # 执行ping命令
            await r.ping()
            
            # 关闭连接
            await r.close()
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "Redis连接正常",
                "duration": round(duration, 3),
                "details": {
                    "type": "Redis",
                    "url": settings.REDIS_URL.split("@")[1] if "@" in settings.REDIS_URL else settings.REDIS_URL
                }
            }
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis连接失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def check_milvus(self) -> Dict[str, Any]:
        """
        检查Milvus连接
        """
        try:
            from pymilvus import connections, utility
            
            start_time = time.time()
            
            # 连接Milvus
            connections.connect(
                alias="health_check",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD,
            )
            
            # 检查连接状态
            is_healthy = utility.get_server_version(using="health_check")
            
            # 断开连接
            connections.disconnect("health_check")
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "Milvus连接正常",
                "duration": round(duration, 3),
                "details": {
                    "type": "Milvus",
                    "host": settings.MILVUS_HOST,
                    "port": settings.MILVUS_PORT,
                    "version": is_healthy
                }
            }
        except Exception as e:
            logger.error(f"Milvus健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"Milvus连接失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def check_neo4j(self) -> Dict[str, Any]:
        """
        检查Neo4j连接
        """
        try:
            from neo4j import AsyncGraphDatabase
            
            start_time = time.time()
            
            # 创建驱动
            driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # 验证连接
            await driver.verify_connectivity()
            
            # 关闭驱动
            await driver.close()
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "Neo4j连接正常",
                "duration": round(duration, 3),
                "details": {
                    "type": "Neo4j",
                    "uri": settings.NEO4J_URI,
                    "database": settings.NEO4J_DATABASE
                }
            }
        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"Neo4j连接失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def check_minio(self) -> Dict[str, Any]:
        """
        检查MinIO连接
        """
        try:
            from minio import Minio
            
            start_time = time.time()
            
            # 创建MinIO客户端
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # 检查存储桶是否存在
            bucket_exists = client.bucket_exists(settings.MINIO_BUCKET_NAME)
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "message": "MinIO连接正常",
                "duration": round(duration, 3),
                "details": {
                    "type": "MinIO",
                    "endpoint": settings.MINIO_ENDPOINT,
                    "bucket": settings.MINIO_BUCKET_NAME,
                    "bucket_exists": bucket_exists
                }
            }
        except Exception as e:
            logger.error(f"MinIO健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"MinIO连接失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def check_ai_services(self) -> Dict[str, Any]:
        """
        检查AI服务状态
        """
        try:
            # 这里可以添加AI服务的健康检查
            # 例如检查LLM、嵌入模型、重排模型等服务的可用性
            
            return {
                "status": "healthy",
                "message": "AI服务正常",
                "duration": 0,
                "details": {
                    "llm_service": "available",
                    "embedding_service": "available",
                    "reranker_service": "available"
                }
            }
        except Exception as e:
            logger.error(f"AI服务健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"AI服务检查失败: {str(e)}",
                "duration": 0,
                "details": {"error": str(e)}
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        """
        import psutil
        import platform
        
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        return {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "cpu": {
                "count": cpu_count,
                "usage_percent": cpu_percent,
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "usage_percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": (disk.used / disk.total) * 100,
            },
            "python_version": platform.python_version(),
        }
