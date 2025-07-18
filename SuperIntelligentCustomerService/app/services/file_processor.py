"""
文件处理服务
支持PDF、DOCX、TXT等文件的文本提取和向量化处理
参考006项目的设计架构
"""
import asyncio
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.models.knowledge import KnowledgeFile, KnowledgeBase
from app.models.enums import EmbeddingStatus
from app.services.file_storage import file_storage
from app.services.knowledge_vector_service import knowledge_vector_manager
from app.services.file_processing_monitor import add_file_to_monitor, update_file_progress, mark_file_completed, mark_file_failed
from app.log import logger


class FileProcessor:
    """文件处理器"""
    
    def __init__(self):
        self.supported_types = {
            '.pdf': self._extract_pdf_text,
            '.docx': self._extract_docx_text,
            '.txt': self._extract_txt_text,
            '.md': self._extract_txt_text,
        }
    
    async def process_file(self, file_id: int) -> bool:
        """
        处理文件

        Args:
            file_id: 文件ID

        Returns:
            处理是否成功
        """
        try:
            # 获取文件信息
            knowledge_file = await KnowledgeFile.get(id=file_id)
            knowledge_base = await knowledge_file.knowledge_base

            logger.info(f"开始处理文件: {knowledge_file.name} (ID: {file_id})")

            # 添加到监控
            await add_file_to_monitor(file_id, knowledge_file.name)

            # 更新状态为处理中
            await knowledge_file.update_embedding_status(EmbeddingStatus.PROCESSING)
            await update_file_progress(file_id, 10, EmbeddingStatus.PROCESSING)
            
            # 读取文件内容
            file_content = file_storage.read_file(knowledge_file.file_path)
            await update_file_progress(file_id, 30)

            # 提取文本
            text_content = await self._extract_text(knowledge_file, file_content)
            await update_file_progress(file_id, 50)

            if not text_content.strip():
                await knowledge_file.update_embedding_status(
                    EmbeddingStatus.FAILED,
                    "文件内容为空或无法提取文本"
                )
                await mark_file_failed(file_id, "文件内容为空或无法提取文本")
                return False
            
            # 分块处理
            chunks = self._split_text(
                text_content,
                chunk_size=knowledge_base.chunk_size,
                chunk_overlap=knowledge_base.chunk_overlap
            )
            await update_file_progress(file_id, 70)

            # 向量化处理
            vector_ids = await self._vectorize_chunks(knowledge_file, chunks)
            await update_file_progress(file_id, 90)

            # 更新文件信息
            knowledge_file.chunk_count = len(chunks)
            knowledge_file.vector_ids = vector_ids
            await knowledge_file.update_embedding_status(EmbeddingStatus.COMPLETED)

            # 更新知识库统计
            await knowledge_base.update_stats()

            # 标记处理完成
            await mark_file_completed(file_id)

            logger.info(f"文件处理完成: {knowledge_file.name}, 分块数: {len(chunks)}")
            return True
            
        except Exception as e:
            logger.error(f"文件处理失败: {str(e)}")
            try:
                knowledge_file = await KnowledgeFile.get(id=file_id)
                await knowledge_file.update_embedding_status(
                    EmbeddingStatus.FAILED,
                    str(e)
                )
                await mark_file_failed(file_id, str(e))
            except:
                pass
            return False
    
    async def _extract_text(self, knowledge_file: KnowledgeFile, file_content: bytes) -> str:
        """
        提取文件文本内容
        
        Args:
            knowledge_file: 知识文件对象
            file_content: 文件内容
            
        Returns:
            提取的文本内容
        """
        file_ext = await knowledge_file.get_file_extension()
        
        if file_ext not in self.supported_types:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        extract_func = self.supported_types[file_ext]
        return await extract_func(file_content)
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """提取PDF文本"""
        try:
            from pypdf import PdfReader
            import io
            
            text = ""
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text
            
        except ImportError:
            raise ImportError("需要安装pypdf库: pip install pypdf")
        except Exception as e:
            raise Exception(f"PDF文本提取失败: {str(e)}")
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """提取DOCX文本"""
        try:
            import docx2txt
            import io
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                text = docx2txt.process(tmp_file_path)
                return text
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
                
        except ImportError:
            raise ImportError("需要安装docx2txt库: pip install docx2txt")
        except Exception as e:
            raise Exception(f"DOCX文本提取失败: {str(e)}")
    
    async def _extract_txt_text(self, file_content: bytes) -> str:
        """提取TXT文本"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用错误处理
            return file_content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            raise Exception(f"文本文件读取失败: {str(e)}")
    
    def _split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        分割文本为块
        
        Args:
            text: 原始文本
            chunk_size: 块大小
            chunk_overlap: 重叠大小
            
        Returns:
            文本块列表
        """
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # 如果不是最后一块，尝试在句号、换行符等处分割
            if end < text_length:
                # 寻找合适的分割点
                for split_char in ['\n\n', '\n', '。', '！', '？', '.', '!', '?']:
                    split_pos = text.rfind(split_char, start, end)
                    if split_pos > start:
                        end = split_pos + len(split_char)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 计算下一个开始位置，考虑重叠
            start = max(start + 1, end - chunk_overlap)
        
        return chunks
    
    async def _vectorize_chunks(self, knowledge_file: KnowledgeFile, chunks: List[str]) -> List[str]:
        """
        向量化文本块

        Args:
            knowledge_file: 知识文件对象
            chunks: 文本块列表

        Returns:
            向量ID列表
        """
        try:
            # 获取知识库信息
            knowledge_base = await knowledge_file.knowledge_base

            # 获取向量服务
            vector_service = knowledge_vector_manager.get_service(knowledge_base.id)

            vector_ids = []

            for i, chunk in enumerate(chunks):
                # 准备元数据
                metadata = {
                    "file_name": knowledge_file.name,
                    "file_type": knowledge_file.file_type,
                    "chunk_count": len(chunks),
                    "original_name": knowledge_file.original_name,
                    "file_size": knowledge_file.file_size
                }

                # 添加到向量数据库
                vector_id = await vector_service.add_chunk(
                    content=chunk,
                    file_id=knowledge_file.id,
                    chunk_index=i,
                    metadata=metadata
                )
                vector_ids.append(vector_id)

            return vector_ids

        except Exception as e:
            logger.error(f"向量化处理失败: {str(e)}")
            # 如果向量化失败，返回空列表但不影响文件处理状态
            return []
    
    async def reprocess_file(self, file_id: int) -> bool:
        """
        重新处理文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            处理是否成功
        """
        try:
            knowledge_file = await KnowledgeFile.get(id=file_id)
            
            # 重置状态
            await knowledge_file.update_embedding_status(EmbeddingStatus.PENDING)
            
            # 重新处理
            return await self.process_file(file_id)
            
        except Exception as e:
            logger.error(f"重新处理文件失败: {str(e)}")
            return False
    
    async def batch_process_files(self, file_ids: List[int]) -> Dict[str, List[int]]:
        """
        批量处理文件
        
        Args:
            file_ids: 文件ID列表
            
        Returns:
            处理结果统计
        """
        results = {
            "success": [],
            "failed": []
        }
        
        for file_id in file_ids:
            try:
                success = await self.process_file(file_id)
                if success:
                    results["success"].append(file_id)
                else:
                    results["failed"].append(file_id)
            except Exception as e:
                logger.error(f"批量处理文件 {file_id} 失败: {str(e)}")
                results["failed"].append(file_id)
        
        return results


# 全局文件处理器实例
file_processor = FileProcessor()


async def process_file_background(file_id: int):
    """
    后台处理文件的异步任务
    
    Args:
        file_id: 文件ID
    """
    try:
        await file_processor.process_file(file_id)
    except Exception as e:
        logger.error(f"后台文件处理失败: {str(e)}")


def start_file_processing(file_id: int):
    """
    启动文件处理任务
    
    Args:
        file_id: 文件ID
    """
    asyncio.create_task(process_file_background(file_id))
