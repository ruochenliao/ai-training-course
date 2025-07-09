"""
任务管理器
管理文件处理任务的状态和数据库同步
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .processor_config import ProcessorConfig, ProcessingStatus, FileType

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """处理任务数据结构"""
    task_id: str
    file_path: str
    file_type: FileType
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    retry_count: int = 0
    error_message: str = ""
    result: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "status": self.status.value,
            "metadata": self.metadata,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "result": self.result,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingTask':
        """从字典创建任务对象"""
        return cls(
            task_id=data["task_id"],
            file_path=data["file_path"],
            file_type=FileType(data["file_type"]),
            status=ProcessingStatus(data["status"]),
            metadata=data.get("metadata", {}),
            priority=data.get("priority", 0),
            retry_count=data.get("retry_count", 0),
            error_message=data.get("error_message", ""),
            result=data.get("result"),
            processing_time=data.get("processing_time", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            last_updated=datetime.fromisoformat(data.get("last_updated", data["created_at"]))
        )


class TaskManager:
    """
    任务管理器
    管理处理任务的状态和数据库同步
    """
    
    def __init__(self, config: ProcessorConfig):
        """
        初始化任务管理器
        
        Args:
            config: 处理器配置
        """
        self.config = config
        
        # 内存中的任务存储
        self.tasks: Dict[str, ProcessingTask] = {}
        self.pending_updates: Dict[str, ProcessingTask] = {}
        
        # 锁和事件
        self.tasks_lock = asyncio.Lock()
        self.update_lock = asyncio.Lock()
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_updates": 0
        }
        
        logger.info("任务管理器初始化完成")
    
    async def add_task(self, task: ProcessingTask) -> None:
        """
        添加任务
        
        Args:
            task: 处理任务
        """
        try:
            async with self.tasks_lock:
                self.tasks[task.task_id] = task
                self.stats["total_tasks"] += 1
                self.stats["active_tasks"] += 1
                
                # 标记为待更新
                await self._mark_for_update(task)
            
            logger.debug(f"任务已添加: {task.task_id}")
            
        except Exception as e:
            logger.error(f"添加任务失败: {task.task_id}, 错误: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            处理任务
        """
        try:
            async with self.tasks_lock:
                return self.tasks.get(task_id)
        except Exception as e:
            logger.error(f"获取任务失败: {task_id}, 错误: {e}")
            return None
    
    async def update_task(self, task: ProcessingTask) -> None:
        """
        更新任务
        
        Args:
            task: 处理任务
        """
        try:
            async with self.tasks_lock:
                if task.task_id in self.tasks:
                    # 更新统计信息
                    old_task = self.tasks[task.task_id]
                    if old_task.status != task.status:
                        await self._update_status_stats(old_task.status, task.status)
                    
                    # 更新任务
                    task.last_updated = datetime.now()
                    self.tasks[task.task_id] = task
                    
                    # 标记为待更新
                    await self._mark_for_update(task)
                else:
                    logger.warning(f"尝试更新不存在的任务: {task.task_id}")
            
        except Exception as e:
            logger.error(f"更新任务失败: {task.task_id}, 错误: {e}")
            raise
    
    async def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功移除
        """
        try:
            async with self.tasks_lock:
                if task_id in self.tasks:
                    task = self.tasks.pop(task_id)
                    self.stats["active_tasks"] -= 1
                    
                    # 从待更新列表中移除
                    self.pending_updates.pop(task_id, None)
                    
                    logger.debug(f"任务已移除: {task_id}")
                    return True
                else:
                    logger.warning(f"尝试移除不存在的任务: {task_id}")
                    return False
        except Exception as e:
            logger.error(f"移除任务失败: {task_id}, 错误: {e}")
            return False
    
    async def get_tasks_by_status(self, status: ProcessingStatus) -> List[ProcessingTask]:
        """
        根据状态获取任务列表
        
        Args:
            status: 处理状态
            
        Returns:
            任务列表
        """
        try:
            async with self.tasks_lock:
                return [task for task in self.tasks.values() if task.status == status]
        except Exception as e:
            logger.error(f"根据状态获取任务失败: {status.value}, 错误: {e}")
            return []
    
    async def get_expired_tasks(self, timeout_minutes: int = 30) -> List[ProcessingTask]:
        """
        获取超时任务
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            超时任务列表
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
            
            async with self.tasks_lock:
                expired_tasks = []
                for task in self.tasks.values():
                    if (task.status == ProcessingStatus.PROCESSING and 
                        task.started_at and 
                        task.started_at < cutoff_time):
                        expired_tasks.append(task)
                
                return expired_tasks
                
        except Exception as e:
            logger.error(f"获取超时任务失败: {e}")
            return []
    
    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            async with self.tasks_lock:
                tasks_to_remove = []
                
                for task_id, task in self.tasks.items():
                    if (task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED] and
                        task.completed_at and
                        task.completed_at < cutoff_time):
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    self.tasks.pop(task_id, None)
                    self.pending_updates.pop(task_id, None)
                    cleaned_count += 1
                
                self.stats["active_tasks"] -= cleaned_count
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个旧任务")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")
            return 0
    
    async def batch_update_status(self) -> None:
        """批量更新任务状态到数据库"""
        try:
            if not self.config.database_config.get("batch_update", True):
                return
            
            async with self.update_lock:
                if not self.pending_updates:
                    return
                
                # 获取待更新的任务
                updates = dict(self.pending_updates)
                self.pending_updates.clear()
                self.stats["pending_updates"] = 0
                
                # 这里可以实现实际的数据库更新逻辑
                # 例如：await self._update_database(updates)
                
                logger.debug(f"批量更新了 {len(updates)} 个任务状态")
                
        except Exception as e:
            logger.error(f"批量更新任务状态失败: {e}")
    
    async def _mark_for_update(self, task: ProcessingTask) -> None:
        """
        标记任务为待更新
        
        Args:
            task: 处理任务
        """
        try:
            async with self.update_lock:
                self.pending_updates[task.task_id] = task
                self.stats["pending_updates"] = len(self.pending_updates)
        except Exception as e:
            logger.error(f"标记任务更新失败: {task.task_id}, 错误: {e}")
    
    async def _update_status_stats(self, old_status: ProcessingStatus, new_status: ProcessingStatus) -> None:
        """
        更新状态统计
        
        Args:
            old_status: 旧状态
            new_status: 新状态
        """
        # 从旧状态移除
        if old_status == ProcessingStatus.COMPLETED:
            self.stats["completed_tasks"] -= 1
        elif old_status == ProcessingStatus.FAILED:
            self.stats["failed_tasks"] -= 1
        
        # 添加到新状态
        if new_status == ProcessingStatus.COMPLETED:
            self.stats["completed_tasks"] += 1
        elif new_status == ProcessingStatus.FAILED:
            self.stats["failed_tasks"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        return {
            **self.stats,
            "total_in_memory": len(self.tasks),
            "status_distribution": self._get_status_distribution()
        }
    
    def _get_status_distribution(self) -> Dict[str, int]:
        """获取状态分布"""
        distribution = {}
        for task in self.tasks.values():
            status = task.status.value
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
