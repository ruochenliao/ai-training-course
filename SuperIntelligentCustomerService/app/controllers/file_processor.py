"""
文件处理服务
异步处理上传的文件，提取内容并生成嵌入向量
"""
import asyncio
import logging
import os
from datetime import datetime

from .memory import MemoryServiceFactory
from ..models.enums import EmbeddingStatus, FileType
from ..models.knowledge import KnowledgeFile, KnowledgeBase

logger = logging.getLogger(__name__)


class FileProcessor:
    """文件处理器"""
    
    def __init__(self):
        self.memory_factory = MemoryServiceFactory()
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        self.worker_tasks = []
    
    async def start(self, num_workers: int = 2):
        """启动文件处理服务"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 启动工作进程
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"文件处理服务已启动，工作进程数: {num_workers}")
    
    async def stop(self):
        """停止文件处理服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消所有工作任务
        for task in self.worker_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("文件处理服务已停止")
    
    async def queue_file(self, file_id: int):
        """将文件加入处理队列"""
        await self.processing_queue.put(file_id)
        logger.info(f"文件 {file_id} 已加入处理队列")
    
    async def _worker(self, worker_name: str):
        """工作进程"""
        logger.info(f"工作进程 {worker_name} 已启动")
        
        while self.is_running:
            try:
                # 从队列获取文件ID
                file_id = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                logger.info(f"{worker_name} 开始处理文件: {file_id}")
                
                # 处理文件
                await self._process_file(file_id)
                
                # 标记任务完成
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                # 队列为空，继续等待
                continue
            except asyncio.CancelledError:
                # 任务被取消
                break
            except Exception as e:
                logger.error(f"{worker_name} 处理文件时发生错误: {e}")
        
        logger.info(f"工作进程 {worker_name} 已停止")
    
    async def _process_file(self, file_id: int):
        """处理单个文件"""
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
                await self._process_document(knowledge_file)
            elif knowledge_file.is_image:
                await self._process_image(knowledge_file)
            else:
                await knowledge_file.mark_failed(f"不支持的文件类型: {knowledge_file.file_type}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_id} 失败: {e}")
            try:
                knowledge_file = await KnowledgeFile.get(id=file_id)
                await knowledge_file.mark_failed(str(e))
            except:
                pass
    
    async def _process_document(self, knowledge_file: KnowledgeFile):
        """处理文档文件"""
        try:
            # 提取文本内容
            content = await self._extract_text_content(knowledge_file)
            
            if not content:
                await knowledge_file.mark_failed("无法提取文本内容")
                return
            
            # 更新内容预览
            preview = content[:500] + "..." if len(content) > 500 else content
            knowledge_file.content_preview = preview
            knowledge_file.word_count = len(content)
            
            # 获取知识库配置
            kb = await knowledge_file.knowledge_base
            
            # 文本分块
            chunks = await self._split_text(
                content, 
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap
            )
            
            # 存储到向量数据库
            chunk_count = await self._store_chunks(knowledge_file, chunks, kb)
            
            # 标记处理完成
            await knowledge_file.mark_completed(
                chunk_count=chunk_count,
                embedding_model=kb.embedding_model
            )
            
            logger.info(f"文档处理完成: {knowledge_file.id}, 分块数: {chunk_count}")
            
        except Exception as e:
            await knowledge_file.mark_failed(f"文档处理失败: {str(e)}")
            raise
    
    async def _process_image(self, knowledge_file: KnowledgeFile):
        """处理图片文件"""
        try:
            # 图片描述生成（需要多模态模型）
            description = await self._generate_image_description(knowledge_file)
            
            if not description:
                await knowledge_file.mark_failed("无法生成图片描述")
                return
            
            # 更新内容预览
            knowledge_file.content_preview = description
            knowledge_file.word_count = len(description)
            
            # 获取知识库配置
            kb = await knowledge_file.knowledge_base
            
            # 存储图片描述到向量数据库
            chunk_count = await self._store_chunks(
                knowledge_file, 
                [description], 
                kb
            )
            
            # 标记处理完成
            await knowledge_file.mark_completed(
                chunk_count=chunk_count,
                embedding_model=kb.embedding_model
            )
            
            logger.info(f"图片处理完成: {knowledge_file.id}")
            
        except Exception as e:
            await knowledge_file.mark_failed(f"图片处理失败: {str(e)}")
            raise
    
    async def _extract_text_content(self, knowledge_file: KnowledgeFile) -> str:
        """提取文本内容"""
        try:
            file_path = knowledge_file.file_path
            file_type = knowledge_file.file_type
            
            if file_type == FileType.TXT:
                # 纯文本文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_type == FileType.MD:
                # Markdown文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_type == FileType.HTML:
                # HTML文件
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    return soup.get_text()
            
            elif file_type == FileType.PDF:
                # PDF文件
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    logger.warning("PyPDF2未安装，无法处理PDF文件")
                    return ""
            
            elif file_type in [FileType.DOCX, FileType.DOC]:
                # Word文档
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
    
    async def _generate_image_description(self, knowledge_file: KnowledgeFile) -> str:
        """生成图片描述"""
        try:
            # TODO: 集成多模态模型生成图片描述
            # 这里先返回基本信息
            return f"图片文件: {knowledge_file.original_name}, 大小: {knowledge_file.get_display_size()}"
        except Exception as e:
            logger.error(f"生成图片描述失败: {e}")
            return ""
    
    async def _split_text(self, text: str, chunk_size: int = 1024, chunk_overlap: int = 100) -> list[str]:
        """文本分块"""
        try:
            # 简单的文本分块实现
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                
                # 如果不是最后一块，尝试在句号处分割
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
            return [text]  # 返回原文本作为单个块
    
    async def _store_chunks(self, knowledge_file: KnowledgeFile, chunks: list[str], kb: KnowledgeBase) -> int:
        """存储文本块到向量数据库"""
        try:
            # 获取私有记忆服务
            private_memory = self.memory_factory.get_private_memory_service(str(kb.owner_id))
            
            stored_count = 0
            for i, chunk in enumerate(chunks):
                # 构建元数据
                metadata = {
                    "knowledge_base_id": kb.id,
                    "knowledge_base_name": kb.name,
                    "file_id": knowledge_file.id,
                    "file_name": knowledge_file.original_name,
                    "file_type": knowledge_file.file_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": datetime.now().isoformat()
                }
                
                # 添加到向量数据库
                await private_memory.add(chunk, metadata)
                stored_count += 1
            
            logger.info(f"存储文本块完成: {stored_count} 个块")
            return stored_count
            
        except Exception as e:
            logger.error(f"存储文本块失败: {e}")
            return 0


# 全局文件处理器实例
file_processor = FileProcessor()
