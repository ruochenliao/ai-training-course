# Copyright (c) 2025 左岚. All rights reserved.
"""
Prometheus监控指标系统
"""

# # Standard library imports
from datetime import datetime
from functools import wraps
import logging
import threading
import time
from typing import Any, Dict, Optional

# # Third-party imports
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_client.core import REGISTRY
import psutil

# # Local application imports
from app.core.config import settings

logger = logging.getLogger(__name__)


class MetricsManager:
    """Prometheus指标管理器"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._lock = threading.Lock()
        
        # HTTP请求指标
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # 数据库指标
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.db_connections_idle = Gauge(
            'db_connections_idle',
            'Idle database connections',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            registry=self.registry
        )
        
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['query_type', 'status'],
            registry=self.registry
        )
        
        # Redis缓存指标
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        self.cache_memory_usage = Gauge(
            'cache_memory_usage_bytes',
            'Cache memory usage in bytes',
            registry=self.registry
        )
        
        # AI模型指标
        self.ai_model_requests_total = Counter(
            'ai_model_requests_total',
            'Total AI model requests',
            ['model_name', 'status'],
            registry=self.registry
        )
        
        self.ai_model_response_time = Histogram(
            'ai_model_response_time_seconds',
            'AI model response time in seconds',
            ['model_name'],
            registry=self.registry
        )
        
        self.ai_model_tokens_used = Counter(
            'ai_model_tokens_used_total',
            'Total tokens used by AI models',
            ['model_name', 'token_type'],
            registry=self.registry
        )
        
        # 系统资源指标
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['device'],
            registry=self.registry
        )
        
        # 应用指标
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'active_users_total',
            'Total active users',
            registry=self.registry
        )
        
        self.active_conversations = Gauge(
            'active_conversations_total',
            'Total active conversations',
            registry=self.registry
        )
        
        # Celery任务指标
        self.celery_tasks_total = Counter(
            'celery_tasks_total',
            'Total Celery tasks',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.celery_task_duration = Histogram(
            'celery_task_duration_seconds',
            'Celery task duration in seconds',
            ['task_name'],
            registry=self.registry
        )
        
        self.celery_queue_size = Gauge(
            'celery_queue_size',
            'Celery queue size',
            ['queue_name'],
            registry=self.registry
        )
        
        # 初始化应用信息
        self.app_info.info({
            'version': settings.VERSION,
            'environment': settings.ENVIRONMENT,
            'project_name': settings.PROJECT_NAME
        })
        
        # 启动系统监控
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """启动系统资源监控"""
        def monitor_system():
            while True:
                try:
                    # CPU使用率
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_cpu_usage.set(cpu_percent)
                    
                    # 内存使用
                    memory = psutil.virtual_memory()
                    self.system_memory_usage.set(memory.used)
                    
                    # 磁盘使用
                    for partition in psutil.disk_partitions():
                        try:
                            disk_usage = psutil.disk_usage(partition.mountpoint)
                            self.system_disk_usage.labels(device=partition.device).set(disk_usage.used)
                        except PermissionError:
                            continue
                    
                    time.sleep(30)  # 每30秒更新一次
                except Exception as e:
                    logger.error(f"系统监控错误: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_db_query(self, query_type: str, duration: float, status: str = 'success'):
        """记录数据库查询指标"""
        self.db_queries_total.labels(query_type=query_type, status=status).inc()
        self.db_query_duration.labels(query_type=query_type).observe(duration)
    
    def update_db_connections(self, active: int, idle: int):
        """更新数据库连接指标"""
        self.db_connections_active.set(active)
        self.db_connections_idle.set(idle)
    
    def record_cache_operation(self, operation: str, status: str = 'success'):
        """记录缓存操作指标"""
        self.cache_operations_total.labels(operation=operation, status=status).inc()
    
    def update_cache_metrics(self, hit_ratio: float, memory_usage: int):
        """更新缓存指标"""
        self.cache_hit_ratio.set(hit_ratio)
        self.cache_memory_usage.set(memory_usage)
    
    def record_ai_model_request(self, model_name: str, response_time: float, 
                               status: str = 'success', input_tokens: int = 0, 
                               output_tokens: int = 0):
        """记录AI模型请求指标"""
        self.ai_model_requests_total.labels(model_name=model_name, status=status).inc()
        self.ai_model_response_time.labels(model_name=model_name).observe(response_time)
        
        if input_tokens > 0:
            self.ai_model_tokens_used.labels(model_name=model_name, token_type='input').inc(input_tokens)
        if output_tokens > 0:
            self.ai_model_tokens_used.labels(model_name=model_name, token_type='output').inc(output_tokens)
    
    def record_celery_task(self, task_name: str, duration: float, status: str = 'success'):
        """记录Celery任务指标"""
        self.celery_tasks_total.labels(task_name=task_name, status=status).inc()
        self.celery_task_duration.labels(task_name=task_name).observe(duration)
    
    def update_queue_size(self, queue_name: str, size: int):
        """更新队列大小指标"""
        self.celery_queue_size.labels(queue_name=queue_name).set(size)
    
    def update_active_users(self, count: int):
        """更新活跃用户数"""
        self.active_users.set(count)
    
    def update_active_conversations(self, count: int):
        """更新活跃对话数"""
        self.active_conversations.set(count)
    
    def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_usage': psutil.cpu_percent(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent if psutil.disk_partitions() else 0
                },
                'application': {
                    'version': settings.VERSION,
                    'environment': settings.ENVIRONMENT,
                    'uptime': time.time() - getattr(self, '_start_time', time.time())
                }
            }
        except Exception as e:
            logger.error(f"获取指标摘要失败: {e}")
            return {'error': str(e)}


def monitor_http_requests(func):
    """HTTP请求监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = kwargs.get('method', 'GET')
        endpoint = kwargs.get('endpoint', 'unknown')
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            metrics_manager.record_http_request(method, endpoint, status_code, duration)
    
    return wrapper


def monitor_db_query(query_type: str = 'unknown'):
    """数据库查询监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                metrics_manager.record_db_query(query_type, duration, status)
        
        return wrapper
    return decorator


def monitor_ai_model(model_name: str):
    """AI模型请求监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                metrics_manager.record_ai_model_request(model_name, duration, status)
        
        return wrapper
    return decorator


# 全局指标管理器实例
metrics_manager = MetricsManager()
metrics_manager._start_time = time.time()
