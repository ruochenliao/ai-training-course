"""
文档处理流水线服务 - 企业级RAG系统
严格按照技术栈要求：文档解析 → 智能分块 → Qwen2.5向量化 → Milvus存储 → Neo4j图谱构建
"""
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from app import entity_extraction_service
from app import intelligent_chunker, ChunkStrategy
from app import marker_service
from app import milvus_service
from app import neo4j_service
from app import qwen_embedding_service
from app.core import get_db_session
from app.models import Document, DocumentChunk, ParseStatus, ChunkType


class DocumentProcessingPipeline:
    """文档处理流水线"""
    
    def __init__(self):
        self.default_chunk_strategy = ChunkStrategy.RECURSIVE
        self.default_chunk_size = 1000
        self.default_overlap = 200
        self.batch_size = 50  # 批处理大小
    
    async def process_document(
        self,
        document_id: int,
        knowledge_base_id: int,
        file_path: Path,
        metadata: Dict[str, Any],
        chunk_strategy: ChunkStrategy = None,
        chunk_size: int = None,
        overlap: int = None
    ) -> Dict[str, Any]:
        """处理单个文档的完整流水线"""
        try:
            logger.info(f"开始处理文档: {document_id}")
            
            # 更新文档状态为处理中
            await self._update_document_status(document_id, ParseStatus.PROCESSING)
            
            # 第一步：文档解析
            parse_result = await self._parse_document(file_path, metadata)
            if not parse_result["success"]:
                await self._update_document_status(document_id, ParseStatus.FAILED, parse_result.get("error"))
                return {"success": False, "error": parse_result.get("error")}
            
            # 第二步：智能分块
            chunks_result = await self._chunk_document(
                parse_result["content"],
                chunk_strategy or self.default_chunk_strategy,
                chunk_size or self.default_chunk_size,
                overlap or self.default_overlap
            )
            
            # 第三步：批量处理分块
            processing_results = await self._process_chunks_batch(
                document_id, knowledge_base_id, chunks_result
            )
            
            # 第四步：创建文档图谱节点
            await self._create_document_graph_node(document_id, knowledge_base_id, metadata)
            
            # 更新文档状态为完成
            await self._update_document_status(
                document_id, 
                ParseStatus.COMPLETED,
                result={
                    "total_chunks": len(chunks_result),
                    "successful_chunks": processing_results["successful_chunks"],
                    "failed_chunks": processing_results["failed_chunks"],
                    "total_entities": processing_results["total_entities"],
                    "total_relations": processing_results["total_relations"]
                }
            )
            
            logger.info(f"文档处理完成: {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": len(chunks_result),
                "processing_results": processing_results
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {document_id}, 错误: {e}")
            await self._update_document_status(document_id, ParseStatus.FAILED, str(e))
            return {"success": False, "error": str(e)}
    
    async def _parse_document(self, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """解析文档"""
        try:
            file_ext = file_path.suffix.lower().lstrip('.')
            result = await marker_service.parse_document(file_path, file_ext)
            
            logger.info(f"文档解析完成: {file_path}, 成功: {result['success']}")
            return result
            
        except Exception as e:
            logger.error(f"文档解析失败: {file_path}, 错误: {e}")
            return {"success": False, "error": str(e)}
    
    async def _chunk_document(
        self,
        content: str,
        strategy: ChunkStrategy,
        chunk_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """智能分块文档"""
        try:
            chunks = intelligent_chunker.chunk_text(
                content=content,
                strategy=strategy,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
            # 优化分块结果
            optimized_chunks = intelligent_chunker.optimize_chunks(chunks)
            
            logger.info(f"文档分块完成，共生成 {len(optimized_chunks)} 个分块")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"文档分块失败: {e}")
            return []
    
    async def _process_chunks_batch(
        self,
        document_id: int,
        knowledge_base_id: int,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量处理分块"""
        try:
            successful_chunks = 0
            failed_chunks = 0
            total_entities = 0
            total_relations = 0
            
            # 分批处理
            for i in range(0, len(chunks), self.batch_size):
                batch_chunks = chunks[i:i + self.batch_size]
                
                # 并行处理批次中的分块
                batch_tasks = [
                    self._process_single_chunk(document_id, knowledge_base_id, chunk)
                    for chunk in batch_chunks
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 统计结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_chunks += 1
                        logger.error(f"分块处理异常: {result}")
                    elif result["success"]:
                        successful_chunks += 1
                        total_entities += result.get("entities_count", 0)
                        total_relations += result.get("relations_count", 0)
                    else:
                        failed_chunks += 1
                
                logger.info(f"批次处理完成: {i//self.batch_size + 1}/{(len(chunks)-1)//self.batch_size + 1}")
            
            return {
                "successful_chunks": successful_chunks,
                "failed_chunks": failed_chunks,
                "total_entities": total_entities,
                "total_relations": total_relations
            }
            
        except Exception as e:
            logger.error(f"批量处理分块失败: {e}")
            return {
                "successful_chunks": 0,
                "failed_chunks": len(chunks),
                "total_entities": 0,
                "total_relations": 0
            }
    
    async def _process_single_chunk(
        self,
        document_id: int,
        knowledge_base_id: int,
        chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理单个分块"""
        try:
            chunk_id = str(uuid.uuid4())
            content = chunk["content"]
            
            # 1. 保存分块到数据库
            await self._save_chunk_to_db(document_id, chunk_id, chunk)
            
            # 2. 生成向量并存储到Milvus
            vector_result = await self._process_chunk_vector(
                knowledge_base_id, document_id, chunk_id, content, chunk
            )
            
            # 3. 提取实体和关系，构建图谱
            graph_result = await self._process_chunk_graph(
                document_id, chunk_id, content, chunk
            )
            
            # 4. 更新分块状态
            await self._update_chunk_status(
                document_id, chunk["index"], 
                vector_result["success"], graph_result["success"]
            )
            
            return {
                "success": vector_result["success"] and graph_result["success"],
                "chunk_id": chunk_id,
                "entities_count": len(graph_result.get("entities", [])),
                "relations_count": len(graph_result.get("relations", []))
            }
            
        except Exception as e:
            logger.error(f"单个分块处理失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_chunk_to_db(
        self,
        document_id: int,
        chunk_id: str,
        chunk: Dict[str, Any]
    ):
        """保存分块到数据库"""
        try:
            async with get_db_session() as session:
                db_chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk["index"],
                    content=chunk["content"],
                    content_hash=chunk["content_hash"],
                    chunk_type=ChunkType(chunk["chunk_type"]),
                    start_position=chunk["metadata"].get("start_position"),
                    end_position=chunk["metadata"].get("end_position"),
                    vector_status=ParseStatus.PENDING,
                    graph_status=ParseStatus.PENDING
                )
                
                session.add(db_chunk)
                await session.commit()
                
        except Exception as e:
            logger.error(f"保存分块到数据库失败: {e}")
            raise
    
    async def _process_chunk_vector(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunk_id: str,
        content: str,
        chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理分块向量化"""
        try:
            # 准备向量数据
            vector_data = {
                "document_id": document_id,
                "chunk_index": chunk["index"],
                "content": content,
                "content_hash": chunk["content_hash"],
                "metadata": {
                    "chunk_type": chunk["chunk_type"],
                    "quality_score": chunk["quality"]["quality_score"],
                    "char_count": chunk["quality"]["char_count"],
                    "word_count": chunk["quality"]["word_count"]
                }
            }
            
            # 插入向量到Milvus
            collection_name = f"kb_{knowledge_base_id}"
            vector_ids = await milvus_service.insert_vectors(collection_name, [vector_data])
            
            if vector_ids:
                # 更新数据库中的Milvus ID
                await self._update_chunk_milvus_id(document_id, chunk["index"], vector_ids[0])
                return {"success": True, "vector_id": vector_ids[0]}
            else:
                return {"success": False, "error": "向量插入失败"}
                
        except Exception as e:
            logger.error(f"分块向量化失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_chunk_graph(
        self,
        document_id: int,
        chunk_id: str,
        content: str,
        chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理分块图谱构建"""
        try:
            # 提取实体和关系
            extraction_result = await entity_extraction_service.process_chunk(content)
            
            entities = extraction_result.get("entities", [])
            relations = extraction_result.get("relations", [])
            
            # 创建分块节点
            chunk_created = await neo4j_service.create_chunk_node(
                chunk_id, document_id, chunk["index"], content, {
                    "content_hash": chunk["content_hash"],
                    "chunk_type": chunk["chunk_type"],
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if not chunk_created:
                return {"success": False, "error": "分块节点创建失败"}
            
            # 创建实体节点
            if entities:
                entity_ids = await neo4j_service.create_entity_nodes(chunk_id, entities)
                logger.debug(f"创建实体节点: {len(entity_ids)}")
            
            # 创建关系
            if relations:
                relation_count = await neo4j_service.create_relations(relations)
                logger.debug(f"创建关系: {relation_count}")
            
            # 更新数据库中的实体和关系信息
            await self._update_chunk_entities_relations(
                document_id, chunk["index"], entities, relations
            )
            
            return {
                "success": True,
                "entities": entities,
                "relations": relations
            }
            
        except Exception as e:
            logger.error(f"分块图谱构建失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_document_graph_node(
        self,
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ):
        """创建文档图谱节点"""
        try:
            await neo4j_service.create_document_node(
                document_id, knowledge_base_id, metadata
            )
        except Exception as e:
            logger.error(f"创建文档图谱节点失败: {e}")
    
    async def _update_document_status(
        self,
        document_id: int,
        status: ParseStatus,
        error: str = None,
        result: Dict[str, Any] = None
    ):
        """更新文档状态"""
        try:
            async with get_db_session() as session:
                # 这里需要实现具体的数据库更新逻辑
                # 由于使用SQLAlchemy，需要查询和更新Document记录
                pass
        except Exception as e:
            logger.error(f"更新文档状态失败: {e}")
    
    async def _update_chunk_status(
        self,
        document_id: int,
        chunk_index: int,
        vector_success: bool,
        graph_success: bool
    ):
        """更新分块状态"""
        try:
            async with get_db_session() as session:
                # 实现分块状态更新逻辑
                pass
        except Exception as e:
            logger.error(f"更新分块状态失败: {e}")
    
    async def _update_chunk_milvus_id(
        self,
        document_id: int,
        chunk_index: int,
        milvus_id: str
    ):
        """更新分块的Milvus ID"""
        try:
            async with get_db_session() as session:
                # 实现Milvus ID更新逻辑
                pass
        except Exception as e:
            logger.error(f"更新Milvus ID失败: {e}")
    
    async def _update_chunk_entities_relations(
        self,
        document_id: int,
        chunk_index: int,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ):
        """更新分块的实体和关系信息"""
        try:
            async with get_db_session() as session:
                # 实现实体关系信息更新逻辑
                pass
        except Exception as e:
            logger.error(f"更新实体关系信息失败: {e}")
    
    async def delete_document_data(self, document_id: int, knowledge_base_id: int) -> bool:
        """删除文档相关的所有数据"""
        try:
            # 删除Milvus向量数据
            collection_name = f"kb_{knowledge_base_id}"
            await milvus_service.delete_vectors(collection_name, f"document_id == {document_id}")
            
            # 删除Neo4j图谱数据
            await neo4j_service.delete_document_graph(document_id)
            
            # 删除数据库记录
            async with get_db_session() as session:
                # 实现数据库记录删除逻辑
                pass
            
            logger.info(f"文档数据删除完成: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档数据失败: {e}")
            return False
    
    async def get_processing_stats(self, knowledge_base_id: int) -> Dict[str, Any]:
        """获取处理统计信息"""
        try:
            # 获取Milvus统计
            collection_name = f"kb_{knowledge_base_id}"
            milvus_stats = await milvus_service.get_collection_stats(collection_name)
            
            # 获取Neo4j统计
            graph_stats = await neo4j_service.get_graph_stats(knowledge_base_id)
            
            return {
                "knowledge_base_id": knowledge_base_id,
                "vector_stats": milvus_stats,
                "graph_stats": graph_stats,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取处理统计失败: {e}")
            return {}


# 全局文档处理流水线实例
document_pipeline = DocumentProcessingPipeline()


# 便捷函数
async def process_document_complete(
    document_id: int,
    knowledge_base_id: int,
    file_path: Path,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """处理文档的便捷函数"""
    return await document_pipeline.process_document(
        document_id, knowledge_base_id, file_path, metadata
    )


async def delete_document_complete(document_id: int, knowledge_base_id: int) -> bool:
    """删除文档的便捷函数"""
    return await document_pipeline.delete_document_data(document_id, knowledge_base_id)
