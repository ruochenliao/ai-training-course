"""
异步文件处理系统
支持多种文档格式转换为Markdown，使用asyncio.Queue实现任务队列
"""
import asyncio
import hashlib
import logging
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

from .processor_config import ProcessorConfig, ProcessingStatus, FileType, ConversionMethod
from .document_converter import DocumentConverter
from .multimodal_processor import MultimodalProcessor
from .task_manager import TaskManager, ProcessingTask

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """处理结果数据结构"""
    task_id: str
    file_path: str
    file_type: FileType
    status: ProcessingStatus
    markdown_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    processing_time: float = 0.0
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "status": self.status.value,
            "markdown_content": self.markdown_content,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class FileProcessor:
    """
    异步文件处理器
    支持多种文档格式转换为Markdown，使用任务队列和进程池
    """
    
    def __init__(self, config: ProcessorConfig = None):
        """
        初始化文件处理器
        
        Args:
            config: 处理器配置
        """
        self.config = config or ProcessorConfig()
        
        # 初始化组件
        self.task_manager = TaskManager(self.config)
        self.document_converter = DocumentConverter(self.config)
        self.multimodal_processor = MultimodalProcessor(self.config)
        
        # 任务队列
        self.task_queue = asyncio.Queue(maxsize=self.config.queue_size)
        self.result_queue = asyncio.Queue()
        
        # 进程池和线程池
        self.process_executor = None
        self.thread_executor = None
        
        # 工作器任务
        self.workers = []
        self.running = False
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_workers": 0,
            "queue_size": 0,
            "average_processing_time": 0.0,
            "start_time": None
        }
        
        # 回调函数
        self.progress_callbacks: Dict[str, Callable] = {}
        self.completion_callbacks: Dict[str, Callable] = {}
        
        logger.info(f"文件处理器初始化完成，最大工作进程数: {self.config.max_workers}")
    
    async def start(self) -> None:
        """启动文件处理器"""
        if self.running:
            logger.warning("文件处理器已在运行")
            return
        
        try:
            # 初始化执行器
            self.process_executor = ProcessPoolExecutor(max_workers=self.config.max_workers)
            self.thread_executor = ThreadPoolExecutor(max_workers=self.config.max_workers * 2)
            
            # 初始化组件
            await self.document_converter.initialize()
            await self.multimodal_processor.initialize()
            
            # 启动工作器
            self.running = True
            self.stats["start_time"] = datetime.now()
            
            for i in range(self.config.max_workers):
                worker = asyncio.create_task(self._worker(f"worker-{i}"))
                self.workers.append(worker)
            
            # 启动结果处理器
            result_processor = asyncio.create_task(self._result_processor())
            self.workers.append(result_processor)
            
            # 启动状态更新器
            status_updater = asyncio.create_task(self._status_updater())
            self.workers.append(status_updater)
            
            logger.info(f"文件处理器已启动，工作器数量: {len(self.workers)}")
            
        except Exception as e:
            logger.error(f"启动文件处理器失败: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """停止文件处理器"""
        if not self.running:
            return
        
        try:
            self.running = False
            
            # 取消所有工作器
            for worker in self.workers:
                worker.cancel()
            
            # 等待工作器完成
            if self.workers:
                await asyncio.gather(*self.workers, return_exceptions=True)
            
            # 关闭执行器
            if self.process_executor:
                self.process_executor.shutdown(wait=True)
            if self.thread_executor:
                self.thread_executor.shutdown(wait=True)
            
            # 关闭组件
            await self.document_converter.close()
            await self.multimodal_processor.close()
            
            logger.info("文件处理器已停止")
            
        except Exception as e:
            logger.error(f"停止文件处理器失败: {e}")
    
    async def submit_file(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None,
        priority: int = 0,
        progress_callback: Callable = None,
        completion_callback: Callable = None
    ) -> str:
        """
        提交文件处理任务
        
        Args:
            file_path: 文件路径
            metadata: 文件元数据
            priority: 任务优先级（数字越大优先级越高）
            progress_callback: 进度回调函数
            completion_callback: 完成回调函数
            
        Returns:
            任务ID
        """
        try:
            # 验证文件
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            file_size = Path(file_path).stat().st_size
            if file_size > self.config.max_file_size:
                raise ValueError(f"文件过大: {file_size} bytes")
            
            # 检测文件类型
            file_type = self.config.detect_file_type(file_path)
            if not self.config.is_supported(file_type):
                raise ValueError(f"不支持的文件类型: {file_type.value}")
            
            # 创建任务
            task_id = str(uuid.uuid4())
            task = ProcessingTask(
                task_id=task_id,
                file_path=file_path,
                file_type=file_type,
                metadata=metadata or {},
                priority=priority,
                created_at=datetime.now()
            )
            
            # 注册回调函数
            if progress_callback:
                self.progress_callbacks[task_id] = progress_callback
            if completion_callback:
                self.completion_callbacks[task_id] = completion_callback
            
            # 添加到任务管理器
            await self.task_manager.add_task(task)
            
            # 添加到队列
            await self.task_queue.put((priority, task))
            
            self.stats["total_tasks"] += 1
            self.stats["queue_size"] = self.task_queue.qsize()
            
            logger.info(f"任务已提交: {task_id}, 文件: {file_path}, 类型: {file_type.value}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"提交文件处理任务失败: {e}")
            raise
    
    async def submit_batch(
        self,
        file_paths: List[str],
        metadata_list: List[Dict[str, Any]] = None,
        priority: int = 0,
        batch_callback: Callable = None
    ) -> List[str]:
        """
        批量提交文件处理任务
        
        Args:
            file_paths: 文件路径列表
            metadata_list: 元数据列表
            priority: 任务优先级
            batch_callback: 批处理回调函数
            
        Returns:
            任务ID列表
        """
        try:
            if not file_paths:
                return []
            
            # 准备元数据列表
            if metadata_list is None:
                metadata_list = [{}] * len(file_paths)
            elif len(metadata_list) < len(file_paths):
                metadata_list.extend([{}] * (len(file_paths) - len(metadata_list)))
            
            # 批量提交任务
            task_ids = []
            for file_path, metadata in zip(file_paths, metadata_list):
                try:
                    task_id = await self.submit_file(
                        file_path=file_path,
                        metadata=metadata,
                        priority=priority
                    )
                    task_ids.append(task_id)
                except Exception as e:
                    logger.error(f"批量提交任务失败: {file_path}, 错误: {e}")
                    # 继续处理其他文件
                    continue
            
            # 注册批处理回调
            if batch_callback and task_ids:
                batch_id = str(uuid.uuid4())
                self.completion_callbacks[batch_id] = batch_callback
                
                # 为每个任务添加批处理标识
                for task_id in task_ids:
                    task = await self.task_manager.get_task(task_id)
                    if task:
                        task.metadata["batch_id"] = batch_id
                        await self.task_manager.update_task(task)
            
            logger.info(f"批量提交完成: {len(task_ids)}/{len(file_paths)} 个任务")
            
            return task_ids
            
        except Exception as e:
            logger.error(f"批量提交文件处理任务失败: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[ProcessingResult]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            处理结果
        """
        try:
            task = await self.task_manager.get_task(task_id)
            if not task:
                return None
            
            return ProcessingResult(
                task_id=task.task_id,
                file_path=task.file_path,
                file_type=task.file_type,
                status=task.status,
                markdown_content=task.result.get("markdown_content", "") if task.result else "",
                metadata=task.metadata,
                error_message=task.error_message or "",
                processing_time=task.processing_time,
                retry_count=task.retry_count,
                created_at=task.created_at,
                completed_at=task.completed_at
            )
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        try:
            task = await self.task_manager.get_task(task_id)
            if not task:
                return False
            
            if task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                logger.warning(f"任务已完成，无法取消: {task_id}")
                return False
            
            # 更新任务状态
            task.status = ProcessingStatus.CANCELLED
            task.completed_at = datetime.now()
            await self.task_manager.update_task(task)
            
            # 清理回调函数
            self.progress_callbacks.pop(task_id, None)
            self.completion_callbacks.pop(task_id, None)
            
            logger.info(f"任务已取消: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False

    async def _worker(self, worker_name: str) -> None:
        """
        工作器协程，处理任务队列中的任务

        Args:
            worker_name: 工作器名称
        """
        logger.info(f"工作器 {worker_name} 已启动")
        self.stats["active_workers"] += 1

        try:
            while self.running:
                try:
                    # 从队列获取任务（按优先级排序）
                    priority, task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=self.config.queue_timeout
                    )

                    self.stats["queue_size"] = self.task_queue.qsize()

                    # 处理任务
                    await self._process_task(task, worker_name)

                    # 标记任务完成
                    self.task_queue.task_done()

                except asyncio.TimeoutError:
                    # 队列超时，继续等待
                    continue
                except asyncio.CancelledError:
                    # 工作器被取消
                    break
                except Exception as e:
                    logger.error(f"工作器 {worker_name} 处理任务时发生错误: {e}")
                    continue

        finally:
            self.stats["active_workers"] -= 1
            logger.info(f"工作器 {worker_name} 已停止")

    async def _process_task(self, task: ProcessingTask, worker_name: str) -> None:
        """
        处理单个任务

        Args:
            task: 处理任务
            worker_name: 工作器名称
        """
        start_time = time.time()

        try:
            logger.info(f"工作器 {worker_name} 开始处理任务: {task.task_id}")

            # 更新任务状态
            task.status = ProcessingStatus.PROCESSING
            task.started_at = datetime.now()
            await self.task_manager.update_task(task)

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 0, "开始处理文件...")

            # 根据文件类型选择处理方法
            conversion_method = self.config.get_conversion_method(task.file_type)

            if conversion_method == ConversionMethod.MULTIMODAL_LLM:
                # 图片处理
                result = await self._process_image_file(task)
            else:
                # 文档处理
                result = await self._process_document_file(task, conversion_method)

            # 更新任务结果
            task.result = result
            task.status = ProcessingStatus.COMPLETED
            task.completed_at = datetime.now()
            task.processing_time = time.time() - start_time

            await self.task_manager.update_task(task)

            # 调用完成回调
            await self._call_completion_callback(task.task_id, result)

            self.stats["completed_tasks"] += 1

            # 更新平均处理时间
            self._update_average_processing_time(task.processing_time)

            logger.info(f"任务处理完成: {task.task_id}, 耗时: {task.processing_time:.2f}秒")

        except Exception as e:
            # 处理失败
            task.status = ProcessingStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            task.processing_time = time.time() - start_time

            await self.task_manager.update_task(task)

            # 检查是否需要重试
            if task.retry_count < self.config.max_retries:
                await self._schedule_retry(task)
            else:
                self.stats["failed_tasks"] += 1
                logger.error(f"任务处理失败（已达最大重试次数）: {task.task_id}, 错误: {e}")

                # 调用完成回调（失败）
                await self._call_completion_callback(task.task_id, {"error": str(e)})

    async def _process_document_file(
        self,
        task: ProcessingTask,
        conversion_method: ConversionMethod
    ) -> Dict[str, Any]:
        """
        处理文档文件

        Args:
            task: 处理任务
            conversion_method: 转换方法

        Returns:
            处理结果
        """
        try:
            # 调用进度回调
            await self._call_progress_callback(task.task_id, 20, "解析文档内容...")

            # 使用文档转换器处理
            result = await self.document_converter.convert_to_markdown(
                file_path=task.file_path,
                file_type=task.file_type,
                conversion_method=conversion_method,
                metadata=task.metadata
            )

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 80, "生成Markdown内容...")

            if not result.get("success", False):
                raise Exception(result.get("error", "文档转换失败"))

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 100, "处理完成")

            return {
                "success": True,
                "markdown_content": result.get("content", ""),
                "metadata": result.get("metadata", {}),
                "conversion_method": conversion_method.value
            }

        except Exception as e:
            logger.error(f"文档处理失败: {task.file_path}, 错误: {e}")
            raise

    async def _process_image_file(self, task: ProcessingTask) -> Dict[str, Any]:
        """
        处理图片文件

        Args:
            task: 处理任务

        Returns:
            处理结果
        """
        try:
            # 调用进度回调
            await self._call_progress_callback(task.task_id, 20, "读取图片文件...")

            # 读取图片文件
            with open(task.file_path, 'rb') as f:
                image_data = f.read()

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 40, "分析图片内容...")

            # 使用多模态处理器分析图片
            analysis_result = await self.multimodal_processor.analyze_image(
                image_data=image_data,
                filename=Path(task.file_path).name,
                metadata=task.metadata
            )

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 80, "生成Markdown描述...")

            if not analysis_result.get("success", False):
                raise Exception(analysis_result.get("error", "图片分析失败"))

            # 生成Markdown内容
            description = analysis_result.get("description", "")
            image_name = Path(task.file_path).name

            markdown_content = f"""# 图片分析结果

## 图片信息
- **文件名**: {image_name}
- **文件路径**: {task.file_path}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 内容描述
{description}

## 图片引用
![{image_name}]({task.file_path})
"""

            # 调用进度回调
            await self._call_progress_callback(task.task_id, 100, "处理完成")

            return {
                "success": True,
                "markdown_content": markdown_content,
                "metadata": {
                    "image_analysis": analysis_result,
                    "file_info": {
                        "name": image_name,
                        "size": len(image_data),
                        "type": task.file_type.value
                    }
                },
                "conversion_method": ConversionMethod.MULTIMODAL_LLM.value
            }

        except Exception as e:
            logger.error(f"图片处理失败: {task.file_path}, 错误: {e}")
            raise

    async def _schedule_retry(self, task: ProcessingTask) -> None:
        """
        安排任务重试

        Args:
            task: 处理任务
        """
        try:
            task.retry_count += 1
            task.status = ProcessingStatus.RETRYING

            # 计算重试延迟
            if self.config.exponential_backoff:
                delay = self.config.retry_delay * (2 ** (task.retry_count - 1))
            else:
                delay = self.config.retry_delay

            logger.info(f"安排任务重试: {task.task_id}, 第{task.retry_count}次重试, 延迟{delay}秒")

            # 延迟后重新加入队列
            await asyncio.sleep(delay)
            await self.task_queue.put((0, task))  # 重试任务优先级设为0

        except Exception as e:
            logger.error(f"安排任务重试失败: {task.task_id}, 错误: {e}")

    async def _call_progress_callback(self, task_id: str, progress: int, message: str) -> None:
        """
        调用进度回调函数

        Args:
            task_id: 任务ID
            progress: 进度百分比
            message: 进度消息
        """
        try:
            callback = self.progress_callbacks.get(task_id)
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, progress, message)
                else:
                    callback(task_id, progress, message)
        except Exception as e:
            logger.error(f"调用进度回调失败: {task_id}, 错误: {e}")

    async def _call_completion_callback(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        调用完成回调函数

        Args:
            task_id: 任务ID
            result: 处理结果
        """
        try:
            callback = self.completion_callbacks.get(task_id)
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, result)
                else:
                    callback(task_id, result)

                # 清理回调函数
                self.completion_callbacks.pop(task_id, None)
                self.progress_callbacks.pop(task_id, None)
        except Exception as e:
            logger.error(f"调用完成回调失败: {task_id}, 错误: {e}")

    async def _result_processor(self) -> None:
        """结果处理器，处理完成的任务结果"""
        logger.info("结果处理器已启动")

        try:
            while self.running:
                try:
                    # 从结果队列获取结果
                    result = await asyncio.wait_for(
                        self.result_queue.get(),
                        timeout=self.config.queue_timeout
                    )

                    # 处理结果（如保存到数据库、发送通知等）
                    await self._handle_result(result)

                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"结果处理器发生错误: {e}")
                    continue

        finally:
            logger.info("结果处理器已停止")

    async def _status_updater(self) -> None:
        """状态更新器，定期更新任务状态到数据库"""
        logger.info("状态更新器已启动")

        try:
            while self.running:
                try:
                    # 批量更新任务状态
                    await self.task_manager.batch_update_status()

                    # 等待下次更新
                    await asyncio.sleep(self.config.database_config["update_interval"])

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"状态更新器发生错误: {e}")
                    await asyncio.sleep(5)  # 错误时等待5秒

        finally:
            logger.info("状态更新器已停止")

    async def _handle_result(self, result: Dict[str, Any]) -> None:
        """
        处理任务结果

        Args:
            result: 任务结果
        """
        try:
            # 这里可以实现结果的后续处理
            # 如保存到数据库、发送通知、清理临时文件等
            pass
        except Exception as e:
            logger.error(f"处理任务结果失败: {e}")

    def _update_average_processing_time(self, processing_time: float) -> None:
        """
        更新平均处理时间

        Args:
            processing_time: 处理时间
        """
        if self.stats["completed_tasks"] == 1:
            self.stats["average_processing_time"] = processing_time
        else:
            # 计算移动平均
            current_avg = self.stats["average_processing_time"]
            count = self.stats["completed_tasks"]
            self.stats["average_processing_time"] = (current_avg * (count - 1) + processing_time) / count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取处理器统计信息

        Returns:
            统计信息
        """
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "queue_size": self.task_queue.qsize(),
            "running": self.running,
            "config": self.config.to_dict()
        }

    async def wait_for_completion(self, timeout: Optional[float] = None) -> None:
        """
        等待所有任务完成

        Args:
            timeout: 超时时间（秒）
        """
        try:
            await asyncio.wait_for(self.task_queue.join(), timeout=timeout)
            logger.info("所有任务已完成")
        except asyncio.TimeoutError:
            logger.warning(f"等待任务完成超时: {timeout}秒")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()
