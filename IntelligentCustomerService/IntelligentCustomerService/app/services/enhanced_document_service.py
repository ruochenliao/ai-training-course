"""
增强文档处理服务
集成Marker解析器，提供高质量文档处理能力
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import DocumentProcessingException
from app.models.document import Document, DocumentChunk
from app.services.marker_document_parser import marker_parser, DocumentParseResult
from app.services.vector_service import vector_service
from app.services.embedding_service import embedding_service
from app.utils.text_splitter import intelligent_text_splitter


class EnhancedDocumentService:
    """增强文档处理服务"""
    
    def __init__(self):
        """初始化服务"""
        self.supported_formats = marker_parser.supported_formats.keys()
        logger.info("增强文档处理服务初始化完成")
    
    async def process_document(
        self,
        file_path: str,
        file_name: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        extract_images: bool = True,
        extract_tables: bool = True,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        处理文档
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            user_id: 用户ID
            conversation_id: 对话ID（可选）
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            
        Returns:
            处理结果
        """
        try:
            # 1. 解析文档
            logger.info(f"开始处理文档: {file_name}")
            parse_result = await marker_parser.parse_document(
                file_path=file_path,
                file_name=file_name,
                extract_images=extract_images,
                extract_tables=extract_tables
            )
            
            # 2. 创建文档记录
            document_id = str(uuid.uuid4())
            async with get_async_session() as session:
                document = Document(
                    id=document_id,
                    filename=file_name,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    file_type=Path(file_name).suffix.lower(),
                    user_id=user_id,
                    conversation_id=conversation_id,
                    status='processing',
                    extracted_text=parse_result.content,
                    metadata={
                        'parse_result': {
                            'parser': parse_result.metadata.get('parser', 'unknown'),
                            'page_count': parse_result.page_count,
                            'word_count': parse_result.word_count,
                            'processing_time': parse_result.processing_time,
                            'file_hash': parse_result.file_hash,
                            'has_images': len(parse_result.images) > 0,
                            'has_tables': len(parse_result.tables) > 0,
                            'images_count': len(parse_result.images),
                            'tables_count': len(parse_result.tables)
                        },
                        'extraction_options': {
                            'extract_images': extract_images,
                            'extract_tables': extract_tables
                        }
                    }
                )
                
                session.add(document)
                await session.commit()
                await session.refresh(document)
            
            # 3. 智能分块
            chunks = await self._create_document_chunks(
                parse_result=parse_result,
                document_id=document_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 4. 向量化处理
            await self._vectorize_chunks(chunks)
            
            # 5. 更新文档状态
            async with get_async_session() as session:
                document = await session.get(Document, document_id)
                document.status = 'completed'
                document.chunk_count = len(chunks)
                document.processed_at = datetime.utcnow()
                await session.commit()
            
            logger.info(f"文档处理完成: {file_name}, 生成 {len(chunks)} 个分块")
            
            return {
                'document_id': document_id,
                'file_name': file_name,
                'status': 'completed',
                'parse_result': {
                    'content_length': len(parse_result.content),
                    'page_count': parse_result.page_count,
                    'word_count': parse_result.word_count,
                    'images_count': len(parse_result.images),
                    'tables_count': len(parse_result.tables),
                    'processing_time': parse_result.processing_time
                },
                'chunks_count': len(chunks),
                'images': parse_result.images,
                'tables': parse_result.tables,
                'metadata': parse_result.metadata
            }
            
        except Exception as e:
            logger.error(f"文档处理失败 {file_name}: {e}")
            
            # 更新文档状态为失败
            try:
                async with get_async_session() as session:
                    if 'document_id' in locals():
                        document = await session.get(Document, document_id)
                        if document:
                            document.status = 'failed'
                            document.error_message = str(e)
                            await session.commit()
            except Exception as update_error:
                logger.error(f"更新文档状态失败: {update_error}")
            
            raise DocumentProcessingException(f"文档处理失败: {e}")
    
    async def _create_document_chunks(
        self,
        parse_result: DocumentParseResult,
        document_id: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """创建文档分块"""
        try:
            # 使用智能文本分割器
            text_chunks = intelligent_text_splitter.split_text(
                text=parse_result.content,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            chunks = []
            async with get_async_session() as session:
                for i, chunk_text in enumerate(text_chunks):
                    if chunk_text.strip():
                        chunk = DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            chunk_index=i,
                            content=chunk_text,
                            metadata={
                                'chunk_size': len(chunk_text),
                                'word_count': len(chunk_text.split()),
                                'source': 'marker_parser',
                                'chunk_method': 'intelligent_splitter'
                            }
                        )
                        chunks.append(chunk)
                        session.add(chunk)
                
                await session.commit()
                
                # 刷新所有chunks以获取生成的ID
                for chunk in chunks:
                    await session.refresh(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"创建文档分块失败: {e}")
            raise DocumentProcessingException(f"创建文档分块失败: {e}")
    
    async def _vectorize_chunks(self, chunks: List[DocumentChunk]):
        """向量化文档分块"""
        try:
            # 批量生成嵌入向量
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.embed_texts(texts)
            
            # 存储向量
            for chunk, embedding in zip(chunks, embeddings):
                await vector_service.add_vector(
                    vector_id=chunk.id,
                    vector=embedding,
                    metadata={
                        'document_id': chunk.document_id,
                        'chunk_index': chunk.chunk_index,
                        'content': chunk.content[:500],  # 存储前500字符作为预览
                        'type': 'document_chunk'
                    }
                )
            
            logger.info(f"向量化完成: {len(chunks)} 个分块")
            
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            raise DocumentProcessingException(f"向量化失败: {e}")
    
    async def search_documents(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            user_id: 用户ID
            conversation_id: 对话ID（可选）
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        try:
            # 生成查询向量
            query_embedding = await embedding_service.embed_text(query)
            
            # 向量搜索
            search_results = await vector_service.search_vectors(
                query_vector=query_embedding,
                top_k=top_k * 2,  # 获取更多结果用于过滤
                filter_metadata={'type': 'document_chunk'}
            )
            
            # 过滤和排序结果
            filtered_results = []
            async with get_async_session() as session:
                for result in search_results:
                    if result['score'] >= similarity_threshold:
                        # 获取文档信息
                        chunk = await session.get(DocumentChunk, result['id'])
                        if chunk:
                            document = await session.get(Document, chunk.document_id)
                            if document and document.user_id == user_id:
                                # 如果指定了对话ID，只返回该对话的文档
                                if conversation_id is None or document.conversation_id == conversation_id:
                                    filtered_results.append({
                                        'chunk_id': chunk.id,
                                        'document_id': document.id,
                                        'document_name': document.filename,
                                        'content': chunk.content,
                                        'similarity_score': result['score'],
                                        'chunk_index': chunk.chunk_index,
                                        'metadata': chunk.metadata
                                    })
            
            # 按相似度排序并限制结果数量
            filtered_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            raise DocumentProcessingException(f"文档搜索失败: {e}")
    
    async def get_document_info(self, document_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        try:
            async with get_async_session() as session:
                document = await session.get(Document, document_id)
                if document and document.user_id == user_id:
                    return {
                        'id': document.id,
                        'filename': document.filename,
                        'file_type': document.file_type,
                        'file_size': document.file_size,
                        'status': document.status,
                        'chunk_count': document.chunk_count,
                        'created_at': document.created_at,
                        'processed_at': document.processed_at,
                        'metadata': document.metadata
                    }
                return None
                
        except Exception as e:
            logger.error(f"获取文档信息失败: {e}")
            return None
    
    async def delete_document(self, document_id: str, user_id: int) -> bool:
        """删除文档"""
        try:
            async with get_async_session() as session:
                document = await session.get(Document, document_id)
                if document and document.user_id == user_id:
                    # 删除向量
                    chunks = await session.query(DocumentChunk).filter(
                        DocumentChunk.document_id == document_id
                    ).all()
                    
                    for chunk in chunks:
                        await vector_service.delete_vector(chunk.id)
                        await session.delete(chunk)
                    
                    # 删除文档记录
                    await session.delete(document)
                    await session.commit()
                    
                    # 删除文件
                    if os.path.exists(document.file_path):
                        os.remove(document.file_path)
                    
                    logger.info(f"文档删除成功: {document.filename}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False


# 全局增强文档服务实例
enhanced_document_service = EnhancedDocumentService()
