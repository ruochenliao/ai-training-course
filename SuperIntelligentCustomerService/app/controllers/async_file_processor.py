"""
异步文件处理器
优化的高性能文件处理服务，支持并发处理和批量操作
"""
import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from typing import List, Dict, Any

from .memory.factory import MemoryServiceFactory
from ..models.enums import EmbeddingStatus, FileType
from ..models.knowledge import KnowledgeFile, KnowledgeBase

logger = logging.getLogger(__name__)


class AsyncFileProcessor:
    """异步文件处理器 - 高性能版本"""
    
    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        self.memory_factory = MemoryServiceFactory()
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        # 处理队列和状态
        self.processing_queue = asyncio.Queue(maxsize=100)
        self.is_running = False
        self.worker_tasks = []
        
        # 线程池和进程池
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers // 2)
        
        # 统计信息
        self.stats = {
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "start_time": None,
            "processing_times": []
        }
    
    async def start(self):
        """启动异步文件处理服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        # 启动工作进程
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"async-worker-{i}"))
            self.worker_tasks.append(task)
        
        # 启动批处理器
        batch_task = asyncio.create_task(self._batch_processor())
        self.worker_tasks.append(batch_task)
        
        logger.info(f"异步文件处理服务已启动，工作进程数: {self.max_workers}")
    
    async def stop(self):
        """停止异步文件处理服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消所有工作任务
        for task in self.worker_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # 关闭线程池和进程池
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        
        logger.info("异步文件处理服务已停止")
    
    async def queue_file(self, file_id: int, priority: int = 0):
        """将文件加入处理队列"""
        try:
            await self.processing_queue.put((file_id, priority, datetime.now()))
            logger.info(f"文件 {file_id} 已加入异步处理队列，优先级: {priority}")
        except asyncio.QueueFull:
            logger.warning(f"处理队列已满，文件 {file_id} 加入失败")
            raise
    
    async def process_file(self, file_id: int):
        """直接处理文件（高优先级）"""
        logger.info(f"开始直接异步处理文件: {file_id}")
        await self._process_single_file(file_id)
    
    async def _worker(self, worker_name: str):
        """异步工作进程"""
        logger.info(f"异步工作进程 {worker_name} 已启动")
        
        while self.is_running:
            try:
                # 从队列获取文件
                file_id, priority, queued_time = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                wait_time = (datetime.now() - queued_time).total_seconds()
                logger.info(f"{worker_name} 开始处理文件: {file_id}，等待时间: {wait_time:.2f}s")
                
                # 处理文件
                start_time = time.time()
                await self._process_single_file(file_id)
                process_time = time.time() - start_time
                
                # 更新统计
                self.stats["processing_times"].append(process_time)
                self.stats["processed_files"] += 1
                
                # 标记任务完成
                self.processing_queue.task_done()
                
                logger.info(f"{worker_name} 完成文件处理: {file_id}，耗时: {process_time:.2f}s")
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} 处理文件时发生错误: {e}")
                self.stats["failed_files"] += 1
        
        logger.info(f"异步工作进程 {worker_name} 已停止")
    
    async def _batch_processor(self):
        """批处理器 - 处理批量操作"""
        logger.info("批处理器已启动")
        
        while self.is_running:
            try:
                # 每30秒执行一次批处理任务
                await asyncio.sleep(30)
                
                # 批量清理失败的文件
                await self._cleanup_failed_files()
                
                # 批量更新统计信息
                await self._update_batch_statistics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"批处理器执行错误: {e}")
        
        logger.info("批处理器已停止")
    
    async def _process_single_file(self, file_id: int):
        """处理单个文件 - 优化版本"""
        try:
            # 获取文件信息
            knowledge_file = await KnowledgeFile.get(id=file_id).prefetch_related("knowledge_base")
            
            # 检查文件状态
            if knowledge_file.embedding_status != EmbeddingStatus.PENDING:
                logger.warning(f"文件 {file_id} 状态不是PENDING，跳过处理")
                return
            
            # 标记为处理中
            await knowledge_file.mark_processing()
            
            # 检查文件是否存在
            if not os.path.exists(knowledge_file.file_path):
                await knowledge_file.mark_failed("文件不存在")
                return
            
            # 根据文件类型处理
            if knowledge_file.is_document:
                await self._process_document_async(knowledge_file)
            elif knowledge_file.is_image:
                await self._process_image_async(knowledge_file)
            else:
                await knowledge_file.mark_failed(f"不支持的文件类型: {knowledge_file.file_type}")
            
        except Exception as e:
            logger.error(f"异步处理文件 {file_id} 失败: {e}")
            try:
                knowledge_file = await KnowledgeFile.get(id=file_id)
                error_msg = str(e)
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                await knowledge_file.mark_failed(error_msg)
            except Exception as mark_error:
                logger.error(f"标记文件失败状态时出错: {mark_error}")
    
    async def _process_document_async(self, knowledge_file: KnowledgeFile):
        """异步处理文档文件"""
        try:
            # 在线程池中提取文本内容
            content = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor,
                self._extract_text_content_sync,
                knowledge_file
            )
            
            if not content:
                await knowledge_file.mark_failed("无法提取文本内容")
                return
            
            # 更新内容预览
            preview = content[:500] + "..." if len(content) > 500 else content
            knowledge_file.content_preview = preview
            knowledge_file.word_count = len(content)
            
            # 获取知识库配置
            kb = await knowledge_file.knowledge_base
            
            # 异步文本分块
            chunks = await self._split_text_async(
                content, 
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap
            )
            
            # 批量存储到向量数据库
            chunk_count = await self._store_chunks_batch(knowledge_file, chunks, kb)
            
            # 标记处理完成
            await knowledge_file.mark_completed(
                chunk_count=chunk_count,
                embedding_model=kb.embedding_model
            )
            
            self.stats["total_chunks"] += chunk_count
            logger.info(f"异步文档处理完成: {knowledge_file.id}, 分块数: {chunk_count}")
            
        except Exception as e:
            await knowledge_file.mark_failed(f"异步文档处理失败: {str(e)}")
            raise
    
    async def _process_image_async(self, knowledge_file: KnowledgeFile):
        """异步处理图片文件"""
        try:
            # 在线程池中生成图片描述
            description = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor,
                self._generate_image_description_sync,
                knowledge_file
            )
            
            if not description:
                await knowledge_file.mark_failed("无法生成图片描述")
                return
            
            # 更新内容预览
            knowledge_file.content_preview = description
            knowledge_file.word_count = len(description)
            
            # 获取知识库配置
            kb = await knowledge_file.knowledge_base
            
            # 存储图片描述到向量数据库
            chunk_count = await self._store_chunks_batch(
                knowledge_file, 
                [description], 
                kb
            )
            
            # 标记处理完成
            await knowledge_file.mark_completed(
                chunk_count=chunk_count,
                embedding_model=kb.embedding_model
            )
            
            logger.info(f"异步图片处理完成: {knowledge_file.id}")
            
        except Exception as e:
            await knowledge_file.mark_failed(f"异步图片处理失败: {str(e)}")
            raise

    def _extract_text_content_sync(self, knowledge_file: KnowledgeFile) -> str:
        """同步提取文本内容（在线程池中运行）"""
        try:
            file_path = knowledge_file.file_path
            file_type = knowledge_file.file_type

            if file_type == FileType.TXT:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_type == FileType.MD:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_type == FileType.HTML:
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    return soup.get_text()

            elif file_type == FileType.PDF:
                return self._extract_pdf_content_sync(file_path)

            elif file_type in [FileType.DOCX, FileType.DOC]:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.warning("python-docx未安装，无法处理Word文档")
                    return ""

            else:
                logger.warning(f"不支持的文档类型: {file_type}")
                return ""

        except Exception as e:
            logger.error(f"提取文本内容失败: {e}")
            return ""

    def _extract_pdf_content_sync(self, file_path: str) -> str:
        """同步提取PDF内容"""
        try:
            import PyPDF2
            logger.info(f"使用PyPDF2处理PDF文件: {file_path}")

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""

                if reader.is_encrypted:
                    if not reader.decrypt(""):
                        raise Exception("PDF文件已加密且无法解密")

                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n\n--- 第 {page_num + 1} 页 ---\n\n"
                            text += page_text
                    except Exception as e:
                        logger.warning(f"提取第{page_num + 1}页内容失败: {e}")
                        continue

                if text.strip():
                    logger.info(f"PyPDF2成功提取PDF内容，总页数: {len(reader.pages)}")
                    return text.strip()
                else:
                    raise Exception("未能提取到有效文本内容")

        except Exception as e:
            logger.error(f"PDF内容提取失败: {e}")
            raise Exception(f"PDF文件处理失败: {str(e)}")

    def _generate_image_description_sync(self, knowledge_file: KnowledgeFile) -> str:
        """同步生成图片描述（在线程池中运行）"""
        try:
            # TODO: 集成多模态模型生成图片描述
            return f"图片文件: {knowledge_file.original_name}, 大小: {knowledge_file.file_size} 字节"
        except Exception as e:
            logger.error(f"生成图片描述失败: {e}")
            return ""

    async def _split_text_async(self, text: str, chunk_size: int = 1024, chunk_overlap: int = 100) -> List[str]:
        """异步文本分块"""
        try:
            # 在线程池中执行分块操作
            chunks = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor,
                self._split_text_sync,
                text, chunk_size, chunk_overlap
            )
            return chunks

        except Exception as e:
            logger.error(f"异步文本分块失败: {e}")
            return [text]

    def _split_text_sync(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """同步文本分块"""
        try:
            chunks = []
            start = 0

            while start < len(text):
                end = start + chunk_size

                if end < len(text):
                    # 向后查找句号
                    for i in range(end, min(end + 100, len(text))):
                        if text[i] in '。！？.!?':
                            end = i + 1
                            break

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                start = end - chunk_overlap
                if start >= len(text):
                    break

            return chunks

        except Exception as e:
            logger.error(f"文本分块失败: {e}")
            return [text]

    async def _store_chunks_batch(self, knowledge_file: KnowledgeFile, chunks: List[str], kb: KnowledgeBase) -> int:
        """批量存储文本块到向量数据库"""
        try:
            # 获取私有记忆服务
            private_memory = self.memory_factory.get_private_memory_service(str(kb.owner_id))

            # 批量处理chunks
            stored_count = 0
            batch_size = self.batch_size

            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_metadata = []

                # 准备批量元数据
                for j, chunk in enumerate(batch_chunks):
                    metadata = {
                        "knowledge_base_id": kb.id,
                        "knowledge_base_name": kb.name,
                        "file_id": knowledge_file.id,
                        "file_name": knowledge_file.original_name,
                        "file_type": knowledge_file.file_type,
                        "chunk_index": i + j,
                        "total_chunks": len(chunks),
                        "created_at": datetime.now().isoformat()
                    }
                    batch_metadata.append(metadata)

                # 批量添加到向量数据库
                try:
                    for chunk, metadata in zip(batch_chunks, batch_metadata):
                        await private_memory.add_memory(chunk, metadata)
                        stored_count += 1
                except Exception as e:
                    logger.error(f"批量存储第{i//batch_size + 1}批失败: {e}")
                    # 继续处理下一批
                    continue

            logger.info(f"批量存储文本块完成: {stored_count} 个块")
            return stored_count

        except Exception as e:
            logger.error(f"批量存储文本块失败: {e}")
            return 0

    async def _cleanup_failed_files(self):
        """批量清理失败的文件"""
        try:
            # 查找长时间处理中的文件
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=1)

            stuck_files = await KnowledgeFile.filter(
                embedding_status=EmbeddingStatus.PROCESSING,
                updated_at__lt=cutoff_time
            ).all()

            for file in stuck_files:
                await file.mark_failed("处理超时")
                logger.warning(f"清理超时文件: {file.id}")

        except Exception as e:
            logger.error(f"清理失败文件时出错: {e}")

    async def _update_batch_statistics(self):
        """批量更新统计信息"""
        try:
            if self.stats["processing_times"]:
                avg_time = sum(self.stats["processing_times"]) / len(self.stats["processing_times"])
                logger.info(f"处理统计 - 已处理: {self.stats['processed_files']}, "
                          f"失败: {self.stats['failed_files']}, "
                          f"平均耗时: {avg_time:.2f}s, "
                          f"总分块: {self.stats['total_chunks']}")

                # 清理旧的处理时间记录，保持最近100条
                if len(self.stats["processing_times"]) > 100:
                    self.stats["processing_times"] = self.stats["processing_times"][-100:]

        except Exception as e:
            logger.error(f"更新统计信息时出错: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.stats.copy()
        if stats["start_time"]:
            stats["uptime"] = (datetime.now() - stats["start_time"]).total_seconds()
        if stats["processing_times"]:
            stats["avg_processing_time"] = sum(stats["processing_times"]) / len(stats["processing_times"])
        stats["queue_size"] = self.processing_queue.qsize()
        return stats


# 全局异步文件处理器实例
async_file_processor = AsyncFileProcessor()
