# Copyright (c) 2025 左岚. All rights reserved.
"""
Celery异步任务队列 - 完善版本
"""

# # Standard library imports
from datetime import datetime, timedelta
import logging
import time
from typing import Any, Dict, List, Optional

# # Third-party imports
from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import task_failure, task_postrun, task_prerun, task_success
from kombu import Exchange, Queue
import redis

# # Local application imports
from app.core.config import settings
from app.core.metrics import metrics_manager

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """自定义任务基类，支持回调和监控"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info(f"任务成功: {task_id}")
        metrics_manager.record_celery_task(self.name, 0, 'success')
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error(f"任务失败: {task_id}, 错误: {exc}")
        metrics_manager.record_celery_task(self.name, 0, 'failure')
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试回调"""
        logger.warning(f"任务重试: {task_id}, 错误: {exc}")
        metrics_manager.record_celery_task(self.name, 0, 'retry')


# 创建Celery应用
celery_app = Celery(
    'ai_platform',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    task_cls=CallbackTask
)

# Celery配置
celery_app.conf.update(
    # 基础配置
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    
    # 任务路由和队列
    task_routes={
        'ai_platform.tasks.ai_model.*': {'queue': 'ai_model'},
        'ai_platform.tasks.file_processing.*': {'queue': 'file_processing'},
        'ai_platform.tasks.embedding.*': {'queue': 'embedding'},
        'ai_platform.tasks.notification.*': {'queue': 'notification'},
        'ai_platform.tasks.cleanup.*': {'queue': 'cleanup'},
    },
    
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('ai_model', Exchange('ai_model'), routing_key='ai_model', 
              queue_arguments={'x-max-priority': 10}),
        Queue('file_processing', Exchange('file_processing'), routing_key='file_processing'),
        Queue('embedding', Exchange('embedding'), routing_key='embedding'),
        Queue('notification', Exchange('notification'), routing_key='notification'),
        Queue('cleanup', Exchange('cleanup'), routing_key='cleanup'),
    ),
    
    # 任务执行配置
    task_acks_late=True,  # 任务完成后确认
    worker_prefetch_multiplier=1,  # 每次只预取一个任务
    task_reject_on_worker_lost=True,  # 工作进程丢失时拒绝任务
    
    # 重试配置
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 最大重试次数
    
    # 结果配置
    result_expires=3600,  # 结果过期时间1小时
    result_persistent=True,  # 持久化结果
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 性能优化
    worker_disable_rate_limits=True,
    task_compression='gzip',
    result_compression='gzip',
    
    # 安全配置
    worker_hijack_root_logger=False,
    worker_log_color=False,
)


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        self._task_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'retry_tasks': 0,
            'pending_tasks': 0
        }
    
    def submit_task(self, task_name: str, args: tuple = (), kwargs: dict = None, 
                   queue: str = 'default', priority: int = 5, 
                   countdown: int = 0, eta: datetime = None) -> AsyncResult:
        """提交任务"""
        try:
            kwargs = kwargs or {}
            
            # 提交任务
            result = celery_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                queue=queue,
                priority=priority,
                countdown=countdown,
                eta=eta
            )
            
            self._task_stats['total_tasks'] += 1
            self._task_stats['pending_tasks'] += 1
            
            logger.info(f"任务已提交: {task_name} (ID: {result.id})")
            return result
            
        except Exception as e:
            logger.error(f"任务提交失败: {task_name}, 错误: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            result = AsyncResult(task_id, app=celery_app)
            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'traceback': result.traceback,
                'date_done': result.date_done,
                'successful': result.successful(),
                'failed': result.failed(),
                'ready': result.ready()
            }
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
            return {'error': str(e)}
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"任务已取消: {task_id}")
            return True
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            inspect = celery_app.control.inspect()
            
            # 获取活跃任务
            active_tasks = inspect.active()
            
            # 获取预定任务
            scheduled_tasks = inspect.scheduled()
            
            # 获取保留任务
            reserved_tasks = inspect.reserved()
            
            # 获取队列长度
            queue_lengths = {}
            for queue_name in ['default', 'ai_model', 'file_processing', 'embedding', 'notification', 'cleanup']:
                try:
                    length = self.redis_client.llen(queue_name)
                    queue_lengths[queue_name] = length
                    metrics_manager.update_queue_size(queue_name, length)
                except Exception:
                    queue_lengths[queue_name] = 0
            
            return {
                'active_tasks': active_tasks,
                'scheduled_tasks': scheduled_tasks,
                'reserved_tasks': reserved_tasks,
                'queue_lengths': queue_lengths,
                'task_stats': self._task_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"获取队列统计失败: {e}")
            return {'error': str(e)}
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作进程统计信息"""
        try:
            inspect = celery_app.control.inspect()
            
            # 获取工作进程状态
            stats = inspect.stats()
            
            # 获取注册的任务
            registered_tasks = inspect.registered()
            
            # 获取活跃队列
            active_queues = inspect.active_queues()
            
            return {
                'worker_stats': stats,
                'registered_tasks': registered_tasks,
                'active_queues': active_queues
            }
            
        except Exception as e:
            logger.error(f"获取工作进程统计失败: {e}")
            return {'error': str(e)}
    
    def purge_queue(self, queue_name: str) -> int:
        """清空队列"""
        try:
            purged = celery_app.control.purge()
            logger.info(f"队列 {queue_name} 已清空，删除了 {purged} 个任务")
            return purged
        except Exception as e:
            logger.error(f"清空队列失败: {queue_name}, 错误: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查Celery连接
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                status = 'healthy'
                worker_count = len(stats)
            else:
                status = 'unhealthy'
                worker_count = 0
            
            # 检查Redis连接
            redis_status = 'healthy'
            try:
                self.redis_client.ping()
            except Exception:
                redis_status = 'unhealthy'
            
            return {
                'status': status,
                'worker_count': worker_count,
                'redis_status': redis_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 任务信号处理
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """任务开始前处理"""
    logger.info(f"任务开始: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """任务完成后处理"""
    logger.info(f"任务完成: {task.name} (ID: {task_id}), 状态: {state}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功处理"""
    task_manager._task_stats['successful_tasks'] += 1
    task_manager._task_stats['pending_tasks'] = max(0, task_manager._task_stats['pending_tasks'] - 1)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """任务失败处理"""
    task_manager._task_stats['failed_tasks'] += 1
    task_manager._task_stats['pending_tasks'] = max(0, task_manager._task_stats['pending_tasks'] - 1)
    logger.error(f"任务失败: {sender.name} (ID: {task_id}), 异常: {exception}")


# 全局任务管理器实例
task_manager = TaskManager()


# 自动发现任务模块
celery_app.autodiscover_tasks(['app.tasks'])
