"""
文档处理相关的Celery任务
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from celery import current_task
from loguru import logger

from app import celery_app
from app import chunker_service
from app import embedding_service
from app import file_storage
from app import graph_service
from app import marker_service
from app import milvus_service
from app.core import DocumentProcessingException
from app.models import Document, DocumentChunk


@celery_app.task(bind=True, name='app.tasks.document_tasks.process_document_task')
def process_document_task(
    self,
    document_id: int,
    file_path: str,
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any] = None
):
    """
    处理单个文档的任务
    
    Args:
        document_id: 文档ID
        file_path: 文件路径
        knowledge_base_id: 知识库ID
        user_id: 用户ID
        options: 处理选项
    """
    try:
        logger.info(f"开始处理文档: {document_id}")
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': '开始处理文档...'}
        )
        
        # 运行异步处理函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _process_document_async(
                    self,
                    document_id,
                    file_path,
                    knowledge_base_id,
                    user_id,
                    options or {}
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"文档处理任务失败 {document_id}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'document_id': document_id}
        )
        raise


async def _process_document_async(
    task,
    document_id: int,
    file_path: str,
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any]
):
    """异步处理文档"""
    try:
        # 1. 获取文档记录
        document = await Document.get(id=document_id)
        if not document:
            raise DocumentProcessingException(f"文档不存在: {document_id}")
        
        # 更新进度
        task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '解析文档内容...'}
        )
        
        # 2. 使用Marker解析文档
        parsed_result = await marker_service.parse_document(
            file_path=file_path,
            file_name=document.filename,
            extract_images=options.get('extract_images', True),
            extract_tables=options.get('extract_tables', True)
        )
        
        # 更新文档信息
        document.content = parsed_result['content']
        document.metadata = parsed_result['metadata']
        document.page_count = parsed_result['page_count']
        document.word_count = parsed_result['word_count']
        document.status = 'parsed'
        await document.save()
        
        # 更新进度
        task.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': '智能分块处理...'}
        )
        
        # 3. 智能分块
        chunks = await chunker_service.chunk_document(
            content=parsed_result['content'],
            document_id=document_id,
            chunk_size=options.get('chunk_size', 1000),
            chunk_overlap=options.get('chunk_overlap', 200)
        )
        
        # 保存分块到数据库
        chunk_records = []
        for i, chunk in enumerate(chunks):
            chunk_record = DocumentChunk(
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
                chunk_index=i,
                content=chunk['content'],
                metadata=chunk.get('metadata', {}),
                token_count=chunk.get('token_count', 0)
            )
            await chunk_record.save()
            chunk_records.append(chunk_record)
        
        # 更新进度
        task.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': '生成向量嵌入...'}
        )
        
        # 4. 生成向量嵌入
        embeddings = []
        for chunk_record in chunk_records:
            embedding = await embedding_service.embed_text(chunk_record.content)
            embeddings.append({
                'id': str(chunk_record.id),
                'vector': embedding,
                'content': chunk_record.content,
                'metadata': {
                    'document_id': document_id,
                    'knowledge_base_id': knowledge_base_id,
                    'chunk_index': chunk_record.chunk_index,
                    **chunk_record.metadata
                }
            })
        
        # 更新进度
        task.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': '存储向量索引...'}
        )
        
        # 5. 存储到向量数据库
        await milvus_service.insert_vectors(
            collection_name=f"kb_{knowledge_base_id}",
            vectors=embeddings
        )
        
        # 更新进度
        task.update_state(
            state='PROGRESS',
            meta={'current': 85, 'total': 100, 'status': '抽取知识图谱...'}
        )
        
        # 6. 抽取知识图谱（如果启用）
        if options.get('extract_graph', True):
            try:
                await graph_service.extract_and_store_entities(
                    content=parsed_result['content'],
                    document_id=document_id,
                    knowledge_base_id=knowledge_base_id
                )
            except Exception as e:
                logger.warning(f"图谱抽取失败，但不影响文档处理: {e}")
        
        # 7. 更新文档状态
        document.status = 'processed'
        document.processed_at = datetime.now()
        await document.save()
        
        # 完成
        task.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': '文档处理完成'}
        )
        
        result = {
            'document_id': document_id,
            'chunks_count': len(chunk_records),
            'vectors_count': len(embeddings),
            'processing_time': (datetime.now() - document.created_at).total_seconds(),
            'status': 'success'
        }
        
        logger.info(f"文档处理完成: {document_id}, 分块数: {len(chunk_records)}")
        return result
        
    except Exception as e:
        # 更新文档状态为失败
        try:
            document = await Document.get(id=document_id)
            document.status = 'failed'
            document.error_message = str(e)
            await document.save()
        except Exception:
            pass
        
        logger.error(f"文档处理失败 {document_id}: {e}")
        raise DocumentProcessingException(f"文档处理失败: {e}")


@celery_app.task(bind=True, name='app.tasks.document_tasks.batch_process_documents_task')
def batch_process_documents_task(
    self,
    document_ids: List[int],
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any] = None
):
    """
    批量处理文档的任务
    
    Args:
        document_ids: 文档ID列表
        knowledge_base_id: 知识库ID
        user_id: 用户ID
        options: 处理选项
    """
    try:
        logger.info(f"开始批量处理文档: {len(document_ids)} 个文档")
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(document_ids), 'status': '开始批量处理...'}
        )
        
        # 运行异步处理函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _batch_process_documents_async(
                    self,
                    document_ids,
                    knowledge_base_id,
                    user_id,
                    options or {}
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"批量文档处理任务失败: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'document_ids': document_ids}
        )
        raise


async def _batch_process_documents_async(
    task,
    document_ids: List[int],
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any]
):
    """异步批量处理文档"""
    try:
        results = []
        failed_documents = []
        
        for i, document_id in enumerate(document_ids):
            try:
                # 更新进度
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(document_ids),
                        'status': f'处理文档 {document_id}...'
                    }
                )
                
                # 获取文档信息
                document = await Document.get(id=document_id)
                if not document:
                    failed_documents.append({
                        'document_id': document_id,
                        'error': '文档不存在'
                    })
                    continue
                
                # 获取文件路径
                file_path = document.file_path
                if not file_path:
                    failed_documents.append({
                        'document_id': document_id,
                        'error': '文件路径不存在'
                    })
                    continue
                
                # 处理单个文档
                result = await _process_document_async(
                    task,
                    document_id,
                    file_path,
                    knowledge_base_id,
                    user_id,
                    options
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理文档失败 {document_id}: {e}")
                failed_documents.append({
                    'document_id': document_id,
                    'error': str(e)
                })
        
        # 完成
        task.update_state(
            state='SUCCESS',
            meta={
                'current': len(document_ids),
                'total': len(document_ids),
                'status': '批量处理完成'
            }
        )
        
        final_result = {
            'total_documents': len(document_ids),
            'successful_documents': len(results),
            'failed_documents': len(failed_documents),
            'results': results,
            'failures': failed_documents,
            'status': 'completed'
        }
        
        logger.info(f"批量文档处理完成: 成功 {len(results)}, 失败 {len(failed_documents)}")
        return final_result
        
    except Exception as e:
        logger.error(f"批量文档处理失败: {e}")
        raise DocumentProcessingException(f"批量文档处理失败: {e}")


@celery_app.task(bind=True, name='app.tasks.document_tasks.reprocess_document_task')
def reprocess_document_task(
    self,
    document_id: int,
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any] = None
):
    """
    重新处理文档的任务
    
    Args:
        document_id: 文档ID
        knowledge_base_id: 知识库ID
        user_id: 用户ID
        options: 处理选项
    """
    try:
        logger.info(f"开始重新处理文档: {document_id}")
        
        # 运行异步处理函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _reprocess_document_async(
                    self,
                    document_id,
                    knowledge_base_id,
                    user_id,
                    options or {}
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"重新处理文档任务失败 {document_id}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'document_id': document_id}
        )
        raise


async def _reprocess_document_async(
    task,
    document_id: int,
    knowledge_base_id: int,
    user_id: int,
    options: Dict[str, Any]
):
    """异步重新处理文档"""
    try:
        # 1. 清理旧数据
        task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '清理旧数据...'}
        )
        
        # 删除旧的分块记录
        old_chunks = await DocumentChunk.filter(document_id=document_id).all()
        for chunk in old_chunks:
            # 从向量数据库删除
            try:
                await milvus_service.delete_vectors(
                    collection_name=f"kb_{knowledge_base_id}",
                    ids=[str(chunk.id)]
                )
            except Exception as e:
                logger.warning(f"删除向量失败: {e}")
            
            # 删除数据库记录
            await chunk.delete()
        
        # 2. 重新处理文档
        document = await Document.get(id=document_id)
        file_path = document.file_path
        
        result = await _process_document_async(
            task,
            document_id,
            file_path,
            knowledge_base_id,
            user_id,
            options
        )
        
        logger.info(f"文档重新处理完成: {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"重新处理文档失败 {document_id}: {e}")
        raise DocumentProcessingException(f"重新处理文档失败: {e}")
