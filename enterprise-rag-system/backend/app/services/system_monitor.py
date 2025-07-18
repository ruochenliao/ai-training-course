"""
系统监控服务 - 第四阶段核心组件
提供系统健康检查、性能监控、资源使用统计等功能
"""

import asyncio
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import settings


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int
    process_count: int
    load_average: List[float]
    uptime: float


@dataclass
class ServiceHealth:
    """服务健康状态"""
    service_name: str
    status: str  # healthy, unhealthy, degraded
    response_time: float
    last_check: str
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ApplicationMetrics:
    """应用指标"""
    active_users: int
    total_requests: int
    error_rate: float
    avg_response_time: float
    database_connections: int
    cache_hit_rate: float
    queue_size: int


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.redis_client = None
        self.monitoring_interval = 30  # 30秒
        self.metrics_retention_hours = 24  # 保留24小时数据
        self.is_monitoring = False
        
        # 初始化Redis连接
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用内存存储: {e}")
            self.redis_client = None
        
        # 内存存储（Redis不可用时的备选方案）
        self.memory_metrics = []
        self.memory_health_status = {}
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络IO
            network = psutil.net_io_counters()
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 系统负载
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows系统不支持getloadavg
                load_average = [0.0, 0.0, 0.0]
            
            # 系统运行时间
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_percent=disk.percent,
                disk_used=disk.used,
                disk_total=disk.total,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                process_count=process_count,
                load_average=load_average,
                uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            # 返回默认值
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used=0,
                memory_total=0,
                disk_percent=0.0,
                disk_used=0,
                disk_total=0,
                network_sent=0,
                network_recv=0,
                process_count=0,
                load_average=[0.0, 0.0, 0.0],
                uptime=0.0
            )
    
    async def check_service_health(self, service_name: str, check_func) -> ServiceHealth:
        """检查服务健康状态"""
        start_time = time.time()
        
        try:
            result = await check_func()
            response_time = time.time() - start_time
            
            return ServiceHealth(
                service_name=service_name,
                status="healthy",
                response_time=response_time,
                last_check=datetime.utcnow().isoformat(),
                details=result if isinstance(result, dict) else None
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"服务{service_name}健康检查失败: {e}")
            
            return ServiceHealth(
                service_name=service_name,
                status="unhealthy",
                response_time=response_time,
                last_check=datetime.utcnow().isoformat(),
                error_message=str(e)
            )
    
    async def check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            db = next(get_db())
            result = db.execute(text("SELECT 1")).fetchone()
            
            # 获取连接池信息
            pool = db.get_bind().pool
            pool_status = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            return {
                "query_result": result[0] if result else None,
                "connection_pool": pool_status
            }
            
        except Exception as e:
            raise Exception(f"数据库连接失败: {e}")
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """检查Redis健康状态"""
        if not self.redis_client:
            raise Exception("Redis客户端未初始化")
        
        try:
            # 测试连接
            pong = self.redis_client.ping()
            
            # 获取Redis信息
            info = self.redis_client.info()
            
            return {
                "ping": pong,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed")
            }
            
        except Exception as e:
            raise Exception(f"Redis连接失败: {e}")
    
    async def check_milvus_health(self) -> Dict[str, Any]:
        """检查Milvus健康状态"""
        try:
            from app.services.milvus_service import milvus_service
            
            # 检查连接
            await milvus_service.connect()
            
            # 获取集合信息
            collections = await milvus_service.list_collections()
            
            return {
                "connected": True,
                "collections_count": len(collections),
                "collections": collections[:5]  # 只返回前5个集合名
            }
            
        except Exception as e:
            raise Exception(f"Milvus连接失败: {e}")
    
    async def check_neo4j_health(self) -> Dict[str, Any]:
        """检查Neo4j健康状态"""
        try:
            from app.services.neo4j_graph_service import Neo4jGraphService
            
            graph_service = Neo4jGraphService()
            await graph_service.connect()
            
            # 执行简单查询测试连接
            result = await graph_service.execute_query("RETURN 1 as test")
            
            await graph_service.disconnect()
            
            return {
                "connected": True,
                "test_query_result": result
            }
            
        except Exception as e:
            raise Exception(f"Neo4j连接失败: {e}")
    
    async def get_application_metrics(self) -> ApplicationMetrics:
        """获取应用指标"""
        try:
            # 这里应该从实际的应用统计中获取数据
            # 暂时使用模拟数据
            
            active_users = 0
            total_requests = 0
            error_rate = 0.0
            avg_response_time = 0.0
            database_connections = 0
            cache_hit_rate = 0.0
            queue_size = 0
            
            # 从Redis获取统计数据（如果可用）
            if self.redis_client:
                try:
                    active_users = int(self.redis_client.get("stats:active_users") or 0)
                    total_requests = int(self.redis_client.get("stats:total_requests") or 0)
                    error_rate = float(self.redis_client.get("stats:error_rate") or 0.0)
                    avg_response_time = float(self.redis_client.get("stats:avg_response_time") or 0.0)
                    cache_hit_rate = float(self.redis_client.get("stats:cache_hit_rate") or 0.0)
                    queue_size = int(self.redis_client.get("stats:queue_size") or 0)
                except Exception as e:
                    logger.warning(f"获取Redis统计数据失败: {e}")
            
            return ApplicationMetrics(
                active_users=active_users,
                total_requests=total_requests,
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                queue_size=queue_size
            )
            
        except Exception as e:
            logger.error(f"获取应用指标失败: {e}")
            return ApplicationMetrics(
                active_users=0,
                total_requests=0,
                error_rate=0.0,
                avg_response_time=0.0,
                database_connections=0,
                cache_hit_rate=0.0,
                queue_size=0
            )
    
    def store_metrics(self, metrics: SystemMetrics):
        """存储指标数据"""
        metrics_data = asdict(metrics)
        
        if self.redis_client:
            try:
                # 存储到Redis时间序列
                key = "system_metrics"
                self.redis_client.lpush(key, json.dumps(metrics_data))
                
                # 保留最近的数据点（基于时间）
                retention_seconds = self.metrics_retention_hours * 3600
                cutoff_time = datetime.utcnow() - timedelta(seconds=retention_seconds)
                
                # 清理过期数据（简化实现）
                self.redis_client.ltrim(key, 0, 2880)  # 保留最近2880个数据点（24小时，每30秒一个）
                
            except Exception as e:
                logger.error(f"存储指标到Redis失败: {e}")
                self._store_to_memory(metrics_data)
        else:
            self._store_to_memory(metrics_data)
    
    def _store_to_memory(self, metrics_data: Dict[str, Any]):
        """存储指标到内存"""
        self.memory_metrics.append(metrics_data)
        
        # 保留最近的数据点
        max_points = 2880  # 24小时，每30秒一个
        if len(self.memory_metrics) > max_points:
            self.memory_metrics = self.memory_metrics[-max_points:]
    
    def get_historical_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取历史指标数据"""
        if self.redis_client:
            try:
                key = "system_metrics"
                # 计算需要获取的数据点数量
                points_needed = (hours * 3600) // self.monitoring_interval
                
                metrics_list = self.redis_client.lrange(key, 0, points_needed - 1)
                return [json.loads(metrics) for metrics in metrics_list]
                
            except Exception as e:
                logger.error(f"从Redis获取历史指标失败: {e}")
                return self._get_memory_metrics(hours)
        else:
            return self._get_memory_metrics(hours)
    
    def _get_memory_metrics(self, hours: int) -> List[Dict[str, Any]]:
        """从内存获取指标数据"""
        points_needed = (hours * 3600) // self.monitoring_interval
        return self.memory_metrics[-points_needed:] if self.memory_metrics else []
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        logger.info("开始系统监控...")
        
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self.get_system_metrics()
                self.store_metrics(metrics)
                
                # 检查服务健康状态
                health_checks = [
                    ("database", self.check_database_health),
                    ("redis", self.check_redis_health),
                    ("milvus", self.check_milvus_health),
                    ("neo4j", self.check_neo4j_health)
                ]
                
                for service_name, check_func in health_checks:
                    health = await self.check_service_health(service_name, check_func)
                    self._store_health_status(health)
                
                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def _store_health_status(self, health: ServiceHealth):
        """存储健康状态"""
        health_data = asdict(health)
        
        if self.redis_client:
            try:
                key = f"health:{health.service_name}"
                self.redis_client.setex(key, 300, json.dumps(health_data))  # 5分钟过期
            except Exception as e:
                logger.error(f"存储健康状态到Redis失败: {e}")
                self.memory_health_status[health.service_name] = health_data
        else:
            self.memory_health_status[health.service_name] = health_data
    
    def get_health_status(self) -> Dict[str, ServiceHealth]:
        """获取所有服务健康状态"""
        health_status = {}
        
        services = ["database", "redis", "milvus", "neo4j"]
        
        for service in services:
            if self.redis_client:
                try:
                    key = f"health:{service}"
                    health_data = self.redis_client.get(key)
                    if health_data:
                        health_status[service] = ServiceHealth(**json.loads(health_data))
                except Exception as e:
                    logger.error(f"从Redis获取健康状态失败: {e}")
            
            # 从内存获取（备选方案）
            if service not in health_status and service in self.memory_health_status:
                health_status[service] = ServiceHealth(**self.memory_health_status[service])
        
        return health_status
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        logger.info("系统监控已停止")


# 全局监控实例
system_monitor = SystemMonitor()
