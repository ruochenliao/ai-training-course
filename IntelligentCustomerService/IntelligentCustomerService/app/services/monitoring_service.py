"""
性能监控服务
提供系统性能监控、指标收集和告警功能
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from ..core.cache_manager import get_cache_manager
from ..core.graph_store import get_graph_store

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_average: List[float]


@dataclass
class ApplicationMetrics:
    """应用指标数据类"""
    timestamp: str
    active_connections: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    queue_size: int


@dataclass
class ModelMetrics:
    """模型指标数据类"""
    timestamp: str
    model_requests: Dict[str, int]
    model_response_times: Dict[str, float]
    model_error_rates: Dict[str, float]
    token_usage: Dict[str, int]
    concurrent_requests: int


class MonitoringService:
    """
    性能监控服务
    
    主要功能：
    - 系统资源监控
    - 应用性能监控
    - 模型使用监控
    - 告警和通知
    """
    
    def __init__(self):
        """初始化监控服务"""
        self.cache_manager = get_cache_manager()
        self.graph_store = get_graph_store()
        
        # 监控配置
        self.monitoring_interval = 30  # 监控间隔（秒）
        self.metrics_retention_days = 7  # 指标保留天数
        
        # 告警阈值
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate": 5.0,
            "response_time": 5.0,
            "cache_hit_rate": 50.0
        }
        
        # 指标存储
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts_history: List[Dict[str, Any]] = []
        
        # 性能计数器
        self.performance_counters = {
            "total_requests": 0,
            "total_errors": 0,
            "response_times": [],
            "model_requests": {},
            "model_errors": {},
            "model_response_times": {}
        }
        
        logger.info("性能监控服务初始化完成")
    
    async def start_monitoring(self):
        """开始监控"""
        logger.info("🔍 开始性能监控...")
        
        while True:
            try:
                # 收集系统指标
                system_metrics = await self.collect_system_metrics()
                
                # 收集应用指标
                app_metrics = await self.collect_application_metrics()
                
                # 收集模型指标
                model_metrics = await self.collect_model_metrics()
                
                # 存储指标
                await self.store_metrics({
                    "system": asdict(system_metrics),
                    "application": asdict(app_metrics),
                    "model": asdict(model_metrics)
                })
                
                # 检查告警
                await self.check_alerts(system_metrics, app_metrics, model_metrics)
                
                # 清理过期数据
                await self.cleanup_old_metrics()
                
                logger.debug("监控数据收集完成")
                
            except Exception as e:
                logger.error(f"监控数据收集失败: {str(e)}")
            
            # 等待下次监控
            await asyncio.sleep(self.monitoring_interval)
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # 网络使用情况
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024**2)
            network_recv_mb = network.bytes_recv / (1024**2)
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 负载平均值
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows系统不支持getloadavg
                load_average = [0.0, 0.0, 0.0]
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=round(disk_percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                network_sent_mb=round(network_sent_mb, 2),
                network_recv_mb=round(network_recv_mb, 2),
                process_count=process_count,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_total_gb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                process_count=0,
                load_average=[0.0, 0.0, 0.0]
            )
    
    async def collect_application_metrics(self) -> ApplicationMetrics:
        """收集应用指标"""
        try:
            # 获取缓存统计
            cache_stats = await self.cache_manager.get_stats()
            cache_hit_rate = cache_stats.get("cache_stats", {}).get("hit_rate", 0.0)
            
            # 计算平均响应时间
            response_times = self.performance_counters["response_times"]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # 计算错误率
            total_requests = self.performance_counters["total_requests"]
            total_errors = self.performance_counters["total_errors"]
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0
            
            # 获取数据库连接数
            try:
                graph_health = await self.graph_store.health_check()
                database_connections = 1 if graph_health["status"] == "healthy" else 0
            except:
                database_connections = 0
            
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                active_connections=0,  # 需要从应用服务器获取
                total_requests=total_requests,
                avg_response_time=round(avg_response_time, 3),
                error_rate=round(error_rate, 2),
                cache_hit_rate=cache_hit_rate,
                database_connections=database_connections,
                queue_size=0  # 需要从任务队列获取
            )
            
        except Exception as e:
            logger.error(f"收集应用指标失败: {str(e)}")
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                active_connections=0,
                total_requests=0,
                avg_response_time=0.0,
                error_rate=0.0,
                cache_hit_rate=0.0,
                database_connections=0,
                queue_size=0
            )
    
    async def collect_model_metrics(self) -> ModelMetrics:
        """收集模型指标"""
        try:
            model_requests = self.performance_counters["model_requests"].copy()
            model_errors = self.performance_counters["model_errors"]
            model_times = self.performance_counters["model_response_times"]
            
            # 计算模型响应时间
            model_response_times = {}
            for model, times in model_times.items():
                if times:
                    model_response_times[model] = sum(times) / len(times)
                else:
                    model_response_times[model] = 0.0
            
            # 计算模型错误率
            model_error_rates = {}
            for model in model_requests:
                total = model_requests[model]
                errors = model_errors.get(model, 0)
                model_error_rates[model] = (errors / total * 100) if total > 0 else 0.0
            
            return ModelMetrics(
                timestamp=datetime.now().isoformat(),
                model_requests=model_requests,
                model_response_times=model_response_times,
                model_error_rates=model_error_rates,
                token_usage={},  # 需要从模型服务获取
                concurrent_requests=0  # 需要从模型服务获取
            )
            
        except Exception as e:
            logger.error(f"收集模型指标失败: {str(e)}")
            return ModelMetrics(
                timestamp=datetime.now().isoformat(),
                model_requests={},
                model_response_times={},
                model_error_rates={},
                token_usage={},
                concurrent_requests=0
            )
    
    async def store_metrics(self, metrics: Dict[str, Any]):
        """存储指标数据"""
        try:
            # 添加到历史记录
            self.metrics_history.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            })
            
            # 存储到缓存
            await self.cache_manager.set(
                "monitoring",
                f"metrics_{int(time.time())}",
                metrics,
                ttl=self.metrics_retention_days * 24 * 3600
            )
            
        except Exception as e:
            logger.error(f"存储指标数据失败: {str(e)}")
    
    async def check_alerts(
        self,
        system_metrics: SystemMetrics,
        app_metrics: ApplicationMetrics,
        model_metrics: ModelMetrics
    ):
        """检查告警条件"""
        alerts = []
        
        # 检查系统指标告警
        if system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "metric": "cpu_percent",
                "value": system_metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
                "message": f"CPU使用率过高: {system_metrics.cpu_percent}%"
            })
        
        if system_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "metric": "memory_percent",
                "value": system_metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
                "message": f"内存使用率过高: {system_metrics.memory_percent}%"
            })
        
        if system_metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "type": "system",
                "level": "critical",
                "metric": "disk_percent",
                "value": system_metrics.disk_percent,
                "threshold": self.alert_thresholds["disk_percent"],
                "message": f"磁盘使用率过高: {system_metrics.disk_percent}%"
            })
        
        # 检查应用指标告警
        if app_metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append({
                "type": "application",
                "level": "warning",
                "metric": "error_rate",
                "value": app_metrics.error_rate,
                "threshold": self.alert_thresholds["error_rate"],
                "message": f"错误率过高: {app_metrics.error_rate}%"
            })
        
        if app_metrics.avg_response_time > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "application",
                "level": "warning",
                "metric": "avg_response_time",
                "value": app_metrics.avg_response_time,
                "threshold": self.alert_thresholds["response_time"],
                "message": f"平均响应时间过长: {app_metrics.avg_response_time}s"
            })
        
        if app_metrics.cache_hit_rate < self.alert_thresholds["cache_hit_rate"]:
            alerts.append({
                "type": "application",
                "level": "info",
                "metric": "cache_hit_rate",
                "value": app_metrics.cache_hit_rate,
                "threshold": self.alert_thresholds["cache_hit_rate"],
                "message": f"缓存命中率过低: {app_metrics.cache_hit_rate}%"
            })
        
        # 处理告警
        for alert in alerts:
            await self.handle_alert(alert)
    
    async def handle_alert(self, alert: Dict[str, Any]):
        """处理告警"""
        try:
            # 添加时间戳
            alert["timestamp"] = datetime.now().isoformat()
            
            # 记录告警
            self.alerts_history.append(alert)
            
            # 存储告警到缓存
            await self.cache_manager.set(
                "monitoring",
                f"alert_{int(time.time())}",
                alert,
                ttl=24 * 3600  # 告警保留1天
            )
            
            # 记录日志
            level = alert["level"]
            message = alert["message"]
            
            if level == "critical":
                logger.critical(f"🚨 {message}")
            elif level == "warning":
                logger.warning(f"⚠️ {message}")
            else:
                logger.info(f"ℹ️ {message}")
            
            # TODO: 发送通知（邮件、短信、Webhook等）
            
        except Exception as e:
            logger.error(f"处理告警失败: {str(e)}")
    
    async def cleanup_old_metrics(self):
        """清理过期指标数据"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.metrics_retention_days)
            
            # 清理内存中的历史数据
            self.metrics_history = [
                metric for metric in self.metrics_history
                if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
            ]
            
            self.alerts_history = [
                alert for alert in self.alerts_history
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
            ]
            
            # 重置性能计数器
            if len(self.performance_counters["response_times"]) > 1000:
                self.performance_counters["response_times"] = self.performance_counters["response_times"][-100:]
            
            for model in self.performance_counters["model_response_times"]:
                times = self.performance_counters["model_response_times"][model]
                if len(times) > 1000:
                    self.performance_counters["model_response_times"][model] = times[-100:]
            
        except Exception as e:
            logger.error(f"清理过期数据失败: {str(e)}")
    
    def record_request(self, response_time: float, error: bool = False):
        """记录请求指标"""
        self.performance_counters["total_requests"] += 1
        self.performance_counters["response_times"].append(response_time)
        
        if error:
            self.performance_counters["total_errors"] += 1
    
    def record_model_request(self, model_name: str, response_time: float, error: bool = False):
        """记录模型请求指标"""
        if model_name not in self.performance_counters["model_requests"]:
            self.performance_counters["model_requests"][model_name] = 0
            self.performance_counters["model_errors"][model_name] = 0
            self.performance_counters["model_response_times"][model_name] = []
        
        self.performance_counters["model_requests"][model_name] += 1
        self.performance_counters["model_response_times"][model_name].append(response_time)
        
        if error:
            self.performance_counters["model_errors"][model_name] += 1
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        try:
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()
            model_metrics = await self.collect_model_metrics()
            
            return {
                "system": asdict(system_metrics),
                "application": asdict(app_metrics),
                "model": asdict(model_metrics),
                "alerts": self.alerts_history[-10:],  # 最近10个告警
                "thresholds": self.alert_thresholds
            }
            
        except Exception as e:
            logger.error(f"获取当前指标失败: {str(e)}")
            return {}
    
    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取指标历史"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return [
                metric for metric in self.metrics_history
                if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"获取指标历史失败: {str(e)}")
            return []


# 全局监控服务实例
monitoring_service = MonitoringService()
