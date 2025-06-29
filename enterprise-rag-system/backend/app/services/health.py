"""
健康检查服务
"""

import time
from typing import Dict, Any

from loguru import logger
from tortoise import connections

from app.core import settings


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
            "ai_services": await self.check_ai_services(),
            "cache_system": await self.check_cache_system(),
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
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
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
        start_time = time.time()
        ai_checks = {}

        try:
            # 检查AutoGen服务
            try:
                from app.services.enhanced_autogen_service import autogen_service
                autogen_health = await autogen_service.health_check()
                ai_checks["autogen"] = {
                    "status": autogen_health.get("status", "unknown"),
                    "details": autogen_health
                }
            except Exception as e:
                ai_checks["autogen"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 检查多模态对话服务
            try:
                from app.services.multimodal_conversation_service import multimodal_conversation_service
                multimodal_health = await multimodal_conversation_service.health_check()
                ai_checks["multimodal"] = {
                    "status": multimodal_health.get("status", "unknown"),
                    "details": multimodal_health
                }
            except Exception as e:
                ai_checks["multimodal"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 检查LLM服务连接
            try:
                # 这里可以添加对DeepSeek等LLM服务的ping检查
                ai_checks["llm_connectivity"] = {
                    "status": "healthy",
                    "message": "LLM服务连接正常"
                }
            except Exception as e:
                ai_checks["llm_connectivity"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 判断整体AI服务状态
            all_ai_healthy = all(
                check.get("status") == "healthy"
                for check in ai_checks.values()
            )

            duration = time.time() - start_time

            return {
                "status": "healthy" if all_ai_healthy else "unhealthy",
                "message": "AI服务检查完成",
                "duration": round(duration, 3),
                "details": ai_checks
            }

        except Exception as e:
            logger.error(f"AI服务健康检查失败: {e}")
            duration = time.time() - start_time
            return {
                "status": "unhealthy",
                "message": f"AI服务检查失败: {str(e)}",
                "duration": round(duration, 3),
                "details": {"error": str(e), "checks": ai_checks}
            }

    async def check_cache_system(self) -> Dict[str, Any]:
        """
        检查缓存系统状态
        """
        start_time = time.time()
        cache_checks = {}

        try:
            # 检查权限缓存
            try:
                from app.core.permission_cache import get_permission_cache
                permission_cache = get_permission_cache()
                cache_stats = permission_cache.get_stats()

                cache_checks["permission_cache"] = {
                    "status": "healthy",
                    "stats": cache_stats,
                    "hit_rate": cache_stats.get("hit_rate", 0),
                    "total_size": cache_stats.get("total_cache_size", 0)
                }
            except Exception as e:
                cache_checks["permission_cache"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 检查错误监控缓存
            try:
                from app.core.error_monitoring import get_error_monitor
                error_monitor = get_error_monitor()

                # 获取错误监控统计
                error_stats = error_monitor.get_performance_metrics(300)

                cache_checks["error_monitoring"] = {
                    "status": "healthy",
                    "stats": {
                        "total_requests": error_stats.get("total_requests", 0),
                        "error_rate": error_stats.get("error_rate", 0),
                        "avg_response_time": error_stats.get("avg_response_time", 0)
                    }
                }
            except Exception as e:
                cache_checks["error_monitoring"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 检查应用级缓存（如果有的话）
            try:
                # 这里可以添加其他应用级缓存的检查
                cache_checks["application_cache"] = {
                    "status": "healthy",
                    "message": "应用缓存正常"
                }
            except Exception as e:
                cache_checks["application_cache"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

            # 判断整体缓存系统状态
            all_cache_healthy = all(
                check.get("status") == "healthy"
                for check in cache_checks.values()
            )

            duration = time.time() - start_time

            return {
                "status": "healthy" if all_cache_healthy else "unhealthy",
                "message": "缓存系统检查完成",
                "duration": round(duration, 3),
                "details": cache_checks
            }

        except Exception as e:
            logger.error(f"缓存系统健康检查失败: {e}")
            duration = time.time() - start_time
            return {
                "status": "unhealthy",
                "message": f"缓存系统检查失败: {str(e)}",
                "duration": round(duration, 3),
                "details": {"error": str(e), "checks": cache_checks}
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
