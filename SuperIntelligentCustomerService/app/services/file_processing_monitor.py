"""
文件处理状态监控服务
实现文件处理状态的实时监控、进度跟踪、错误处理等功能
"""
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.models.knowledge import KnowledgeFile
from app.models.enums import EmbeddingStatus
from app.log import logger


class ProcessingEvent(Enum):
    """处理事件类型"""
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingStatus:
    """文件处理状态"""
    file_id: int
    filename: str
    status: str
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "processing_time": self.processing_time
        }


class FileProcessingMonitor:
    """文件处理监控器"""
    
    def __init__(self):
        self.processing_files: Dict[int, ProcessingStatus] = {}
        self.event_listeners: List[Callable] = []
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.check_interval = 5  # 检查间隔（秒）
        
    async def start(self):
        """启动监控器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("文件处理监控器已启动")
    
    async def stop(self):
        """停止监控器"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("文件处理监控器已停止")
    
    async def add_file(self, file_id: int, filename: str):
        """添加文件到监控列表"""
        status = ProcessingStatus(
            file_id=file_id,
            filename=filename,
            status=EmbeddingStatus.PENDING,
            started_at=datetime.now()
        )
        self.processing_files[file_id] = status
        await self._emit_event(ProcessingEvent.STARTED, status)
        logger.info(f"添加文件到监控: {filename} (ID: {file_id})")
    
    async def update_progress(self, file_id: int, progress: float, status: str = None):
        """更新文件处理进度"""
        if file_id not in self.processing_files:
            return
        
        file_status = self.processing_files[file_id]
        file_status.progress = progress
        
        if status:
            file_status.status = status
        
        # 估算完成时间
        if progress > 0 and file_status.started_at:
            elapsed = (datetime.now() - file_status.started_at).total_seconds()
            estimated_total = elapsed / (progress / 100)
            file_status.estimated_completion = file_status.started_at + timedelta(seconds=estimated_total)
        
        await self._emit_event(ProcessingEvent.PROGRESS, file_status)
    
    async def mark_completed(self, file_id: int):
        """标记文件处理完成"""
        if file_id not in self.processing_files:
            return
        
        file_status = self.processing_files[file_id]
        file_status.status = EmbeddingStatus.COMPLETED
        file_status.progress = 100.0
        file_status.completed_at = datetime.now()
        
        if file_status.started_at:
            file_status.processing_time = (file_status.completed_at - file_status.started_at).total_seconds()
        
        await self._emit_event(ProcessingEvent.COMPLETED, file_status)
        
        # 延迟移除，让前端有时间获取完成状态
        asyncio.create_task(self._delayed_remove(file_id, 30))
    
    async def mark_failed(self, file_id: int, error_message: str):
        """标记文件处理失败"""
        if file_id not in self.processing_files:
            return
        
        file_status = self.processing_files[file_id]
        file_status.status = EmbeddingStatus.FAILED
        file_status.error_message = error_message
        file_status.completed_at = datetime.now()
        
        if file_status.started_at:
            file_status.processing_time = (file_status.completed_at - file_status.started_at).total_seconds()
        
        await self._emit_event(ProcessingEvent.FAILED, file_status)
        
        # 失败的文件保留更长时间
        asyncio.create_task(self._delayed_remove(file_id, 300))
    
    async def cancel_processing(self, file_id: int):
        """取消文件处理"""
        if file_id not in self.processing_files:
            return
        
        file_status = self.processing_files[file_id]
        file_status.status = EmbeddingStatus.CANCELLED
        file_status.completed_at = datetime.now()
        
        await self._emit_event(ProcessingEvent.CANCELLED, file_status)
        del self.processing_files[file_id]
    
    def get_status(self, file_id: int) -> Optional[ProcessingStatus]:
        """获取文件处理状态"""
        return self.processing_files.get(file_id)
    
    def get_all_status(self) -> List[ProcessingStatus]:
        """获取所有文件处理状态"""
        return list(self.processing_files.values())
    
    def get_processing_count(self) -> int:
        """获取正在处理的文件数量"""
        return len([s for s in self.processing_files.values() 
                   if s.status in [EmbeddingStatus.PENDING, EmbeddingStatus.PROCESSING]])
    
    def add_event_listener(self, listener: Callable):
        """添加事件监听器"""
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable):
        """移除事件监听器"""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                await self._check_database_status()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_database_status(self):
        """检查数据库中的文件状态"""
        try:
            # 获取所有监控中的文件ID
            file_ids = list(self.processing_files.keys())
            if not file_ids:
                return
            
            # 查询数据库中的最新状态
            files = await KnowledgeFile.filter(id__in=file_ids).all()
            
            for file_obj in files:
                if file_obj.id in self.processing_files:
                    monitor_status = self.processing_files[file_obj.id]
                    db_status = file_obj.embedding_status
                    
                    # 如果数据库状态与监控状态不同，更新监控状态
                    if monitor_status.status != db_status:
                        if db_status == EmbeddingStatus.COMPLETED:
                            await self.mark_completed(file_obj.id)
                        elif db_status == EmbeddingStatus.FAILED:
                            await self.mark_failed(file_obj.id, file_obj.embedding_error or "处理失败")
                        else:
                            monitor_status.status = db_status
            
        except Exception as e:
            logger.error(f"检查数据库状态失败: {e}")
    
    async def _emit_event(self, event: ProcessingEvent, status: ProcessingStatus):
        """发送事件"""
        for listener in self.event_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event, status)
                else:
                    listener(event, status)
            except Exception as e:
                logger.error(f"事件监听器错误: {e}")
    
    async def _delayed_remove(self, file_id: int, delay: int):
        """延迟移除文件"""
        await asyncio.sleep(delay)
        if file_id in self.processing_files:
            del self.processing_files[file_id]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        total_files = len(self.processing_files)
        pending_files = len([s for s in self.processing_files.values() if s.status == EmbeddingStatus.PENDING])
        processing_files = len([s for s in self.processing_files.values() if s.status == EmbeddingStatus.PROCESSING])
        completed_files = len([s for s in self.processing_files.values() if s.status == EmbeddingStatus.COMPLETED])
        failed_files = len([s for s in self.processing_files.values() if s.status == EmbeddingStatus.FAILED])
        
        # 计算平均处理时间
        completed_with_time = [s for s in self.processing_files.values() 
                              if s.status == EmbeddingStatus.COMPLETED and s.processing_time]
        avg_processing_time = sum(s.processing_time for s in completed_with_time) / len(completed_with_time) if completed_with_time else 0
        
        return {
            "total_files": total_files,
            "pending_files": pending_files,
            "processing_files": processing_files,
            "completed_files": completed_files,
            "failed_files": failed_files,
            "average_processing_time": avg_processing_time,
            "monitor_running": self.is_running
        }


# 全局文件处理监控器实例
file_processing_monitor = FileProcessingMonitor()


async def start_monitoring():
    """启动文件处理监控"""
    await file_processing_monitor.start()


async def stop_monitoring():
    """停止文件处理监控"""
    await file_processing_monitor.stop()


async def add_file_to_monitor(file_id: int, filename: str):
    """添加文件到监控"""
    await file_processing_monitor.add_file(file_id, filename)


async def update_file_progress(file_id: int, progress: float, status: str = None):
    """更新文件处理进度"""
    await file_processing_monitor.update_progress(file_id, progress, status)


async def mark_file_completed(file_id: int):
    """标记文件处理完成"""
    await file_processing_monitor.mark_completed(file_id)


async def mark_file_failed(file_id: int, error_message: str):
    """标记文件处理失败"""
    await file_processing_monitor.mark_failed(file_id, error_message)


def get_file_status(file_id: int) -> Optional[Dict[str, Any]]:
    """获取文件处理状态"""
    status = file_processing_monitor.get_status(file_id)
    return status.to_dict() if status else None


def get_all_file_status() -> List[Dict[str, Any]]:
    """获取所有文件处理状态"""
    return [status.to_dict() for status in file_processing_monitor.get_all_status()]
