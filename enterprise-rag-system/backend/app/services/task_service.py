"""
Celery异步任务服务
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List

import redis
from app.core.config import settings
from celery import Celery
from celery.result import AsyncResult
from loguru import logger

from app.core.exceptions import TaskException


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskType(Enum):
    """任务类型枚举"""
    DOCUMENT_PROCESSING = "document_processing"
    VECTOR_INDEXING = "vector_indexing"
    GRAPH_EXTRACTION = "graph_extraction"
    BATCH_PROCESSING = "batch_processing"
    CLEANUP = "cleanup"


# 创建Celery应用
celery_app = Celery(
    'enterprise_rag',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.document_tasks',
        'app.tasks.vector_tasks',
        'app.tasks.graph_tasks',
        'app.tasks.cleanup_tasks'
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 结果保存1小时
    task_routes={
        'app.tasks.document_tasks.*': {'queue': 'document'},
        'app.tasks.vector_tasks.*': {'queue': 'vector'},
        'app.tasks.graph_tasks.*': {'queue': 'graph'},
        'app.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    }
)


class TaskService:
    """任务服务类"""
    
    def __init__(self):
        """初始化任务服务"""
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.task_prefix = "task:"
        logger.info("任务服务初始化完成")
    
    async def submit_document_processing_task(
        self,
        document_id: int,
        file_path: str,
        knowledge_base_id: int,
        user_id: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        提交文档处理任务
        
        Args:
            document_id: 文档ID
            file_path: 文件路径
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            options: 处理选项
            
        Returns:
            任务ID
        """
        try:
            from app.tasks.document_tasks import process_document_task
            
            task_data = {
                'document_id': document_id,
                'file_path': file_path,
                'knowledge_base_id': knowledge_base_id,
                'user_id': user_id,
                'options': options or {}
            }
            
            # 提交任务
            result = process_document_task.delay(**task_data)
            task_id = result.id
            
            # 保存任务信息
            await self._save_task_info(
                task_id=task_id,
                task_type=TaskType.DOCUMENT_PROCESSING,
                task_data=task_data,
                user_id=user_id
            )
            
            logger.info(f"文档处理任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交文档处理任务失败: {e}")
            raise TaskException(f"提交文档处理任务失败: {e}")
    
    async def submit_vector_indexing_task(
        self,
        document_chunks: List[Dict[str, Any]],
        knowledge_base_id: int,
        user_id: int
    ) -> str:
        """
        提交向量索引任务
        
        Args:
            document_chunks: 文档分块列表
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            任务ID
        """
        try:
            from app.tasks.vector_tasks import index_vectors_task
            
            task_data = {
                'document_chunks': document_chunks,
                'knowledge_base_id': knowledge_base_id,
                'user_id': user_id
            }
            
            result = index_vectors_task.delay(**task_data)
            task_id = result.id
            
            await self._save_task_info(
                task_id=task_id,
                task_type=TaskType.VECTOR_INDEXING,
                task_data=task_data,
                user_id=user_id
            )
            
            logger.info(f"向量索引任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交向量索引任务失败: {e}")
            raise TaskException(f"提交向量索引任务失败: {e}")
    
    async def submit_graph_extraction_task(
        self,
        document_id: int,
        content: str,
        knowledge_base_id: int,
        user_id: int
    ) -> str:
        """
        提交图谱抽取任务
        
        Args:
            document_id: 文档ID
            content: 文档内容
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            任务ID
        """
        try:
            from app.tasks.graph_tasks import extract_graph_task
            
            task_data = {
                'document_id': document_id,
                'content': content,
                'knowledge_base_id': knowledge_base_id,
                'user_id': user_id
            }
            
            result = extract_graph_task.delay(**task_data)
            task_id = result.id
            
            await self._save_task_info(
                task_id=task_id,
                task_type=TaskType.GRAPH_EXTRACTION,
                task_data=task_data,
                user_id=user_id
            )
            
            logger.info(f"图谱抽取任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交图谱抽取任务失败: {e}")
            raise TaskException(f"提交图谱抽取任务失败: {e}")
    
    async def submit_batch_processing_task(
        self,
        document_ids: List[int],
        knowledge_base_id: int,
        user_id: int,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        提交批量处理任务
        
        Args:
            document_ids: 文档ID列表
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            options: 处理选项
            
        Returns:
            任务ID
        """
        try:
            from app.tasks.document_tasks import batch_process_documents_task
            
            task_data = {
                'document_ids': document_ids,
                'knowledge_base_id': knowledge_base_id,
                'user_id': user_id,
                'options': options or {}
            }
            
            result = batch_process_documents_task.delay(**task_data)
            task_id = result.id
            
            await self._save_task_info(
                task_id=task_id,
                task_type=TaskType.BATCH_PROCESSING,
                task_data=task_data,
                user_id=user_id
            )
            
            logger.info(f"批量处理任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交批量处理任务失败: {e}")
            raise TaskException(f"提交批量处理任务失败: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            # 从Celery获取任务结果
            result = AsyncResult(task_id, app=celery_app)
            
            # 从Redis获取任务信息
            task_info = await self._get_task_info(task_id)
            
            status_info = {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.successful() else None,
                'error': str(result.result) if result.failed() else None,
                'progress': self._get_task_progress(task_id),
                'created_at': task_info.get('created_at'),
                'started_at': task_info.get('started_at'),
                'completed_at': task_info.get('completed_at'),
                'task_type': task_info.get('task_type'),
                'user_id': task_info.get('user_id')
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise TaskException(f"获取任务状态失败: {e}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        try:
            celery_app.control.revoke(task_id, terminate=True)
            
            # 更新任务状态
            await self._update_task_status(task_id, TaskStatus.REVOKED)
            
            logger.info(f"任务已取消: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return False
    
    async def get_user_tasks(
        self,
        user_id: int,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户任务列表
        
        Args:
            user_id: 用户ID
            task_type: 任务类型过滤
            status: 状态过滤
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        try:
            # 从Redis获取用户任务列表
            pattern = f"{self.task_prefix}user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            tasks = []
            for key in keys[:limit]:
                task_info = self.redis_client.hgetall(key)
                if task_info:
                    # 解码Redis数据
                    decoded_info = {k.decode(): v.decode() for k, v in task_info.items()}
                    
                    # 应用过滤条件
                    if task_type and decoded_info.get('task_type') != task_type.value:
                        continue
                    if status and decoded_info.get('status') != status.value:
                        continue
                    
                    # 获取最新状态
                    task_id = decoded_info['task_id']
                    current_status = await self.get_task_status(task_id)
                    
                    tasks.append(current_status)
            
            # 按创建时间排序
            tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}")
            raise TaskException(f"获取用户任务列表失败: {e}")
    
    async def cleanup_expired_tasks(self, days: int = 7) -> int:
        """
        清理过期任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            pattern = f"{self.task_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                task_info = self.redis_client.hgetall(key)
                if task_info:
                    created_at_str = task_info.get(b'created_at', b'').decode()
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_date:
                            self.redis_client.delete(key)
                            cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个过期任务")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期任务失败: {e}")
            raise TaskException(f"清理过期任务失败: {e}")
    
    async def _save_task_info(
        self,
        task_id: str,
        task_type: TaskType,
        task_data: Dict[str, Any],
        user_id: int
    ):
        """保存任务信息到Redis"""
        task_info = {
            'task_id': task_id,
            'task_type': task_type.value,
            'user_id': str(user_id),
            'created_at': datetime.now().isoformat(),
            'status': TaskStatus.PENDING.value,
            'task_data': str(task_data)
        }
        
        # 保存到Redis
        key = f"{self.task_prefix}user:{user_id}:{task_id}"
        self.redis_client.hset(key, mapping=task_info)
        self.redis_client.expire(key, 7 * 24 * 3600)  # 7天过期
    
    async def _get_task_info(self, task_id: str) -> Dict[str, Any]:
        """从Redis获取任务信息"""
        # 查找任务信息
        pattern = f"{self.task_prefix}*:{task_id}"
        keys = self.redis_client.keys(pattern)
        
        if keys:
            task_info = self.redis_client.hgetall(keys[0])
            return {k.decode(): v.decode() for k, v in task_info.items()}
        
        return {}
    
    async def _update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        pattern = f"{self.task_prefix}*:{task_id}"
        keys = self.redis_client.keys(pattern)
        
        if keys:
            self.redis_client.hset(keys[0], 'status', status.value)
            if status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
                self.redis_client.hset(keys[0], 'completed_at', datetime.now().isoformat())
    
    def _get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        try:
            progress_key = f"task_progress:{task_id}"
            progress_data = self.redis_client.get(progress_key)
            if progress_data:
                import json
                return json.loads(progress_data)
            return None
        except Exception:
            return None
    
    async def update_task_progress(
        self,
        task_id: str,
        current: int,
        total: int,
        message: str = ""
    ):
        """更新任务进度"""
        try:
            progress_data = {
                'current': current,
                'total': total,
                'percentage': round((current / total) * 100, 2) if total > 0 else 0,
                'message': message,
                'updated_at': datetime.now().isoformat()
            }
            
            progress_key = f"task_progress:{task_id}"
            import json
            self.redis_client.setex(
                progress_key,
                3600,  # 1小时过期
                json.dumps(progress_data)
            )
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")


# 全局任务服务实例
task_service = TaskService()
