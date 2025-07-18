"""
第一阶段功能测试API端点
测试Marker文档解析、Qwen3-8B嵌入、Milvus向量存储、Neo4j知识图谱等核心功能
"""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from loguru import logger

from app.core.response import success_response, error_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.marker_service import marker_service
from app.services.qwen_embedding_service import QwenEmbeddingService
from app.services.milvus_service import milvus_service
from app.services.neo4j_graph_service import Neo4jGraphService
from app.services.enhanced_chunker import EnhancedChunker, EnhancedChunkConfig
from app.services.document_processing_pipeline import DocumentProcessingPipeline

router = APIRouter(prefix="/stage1-test", tags=["第一阶段测试"])


@router.post("/test-marker", summary="测试Marker文档解析")
async def test_marker_parsing(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """测试Marker文档解析功能"""
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        start_time = time.time()
        
        # 使用Marker解析文档
        result = await marker_service.parse_document(
            file_path=tmp_file_path,
            file_name=file.filename,
            extract_images=True,
            extract_tables=True
        )
        
        processing_time = time.time() - start_time
        
        # 清理临时文件
        Path(tmp_file_path).unlink(missing_ok=True)
        
        return success_response(
            data={
                "filename": file.filename,
                "processing_time": processing_time,
                "success": result.get("success", False),
                "content_length": len(result.get("content", "")),
                "word_count": result.get("word_count", 0),
                "page_count": result.get("page_count", 0),
                "images_count": len(result.get("images", [])),
                "tables_count": len(result.get("tables", [])),
                "quality_score": result.get("quality_score", 0.0),
                "metadata": result.get("metadata", {}),
                "content_preview": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", "")
            },
            message="Marker文档解析测试完成"
        )
        
    except Exception as e:
        logger.error(f"Marker解析测试失败: {e}")
        return error_response(message=f"Marker解析测试失败: {str(e)}")


@router.post("/test-embedding", summary="测试Qwen3-8B嵌入")
async def test_qwen_embedding(
    text: str = Form(..., description="要嵌入的文本"),
    current_user: User = Depends(get_current_user)
):
    """测试Qwen3-8B嵌入功能"""
    try:
        embedding_service = QwenEmbeddingService()
        
        start_time = time.time()
        
        # 生成嵌入向量
        embedding = await embedding_service.encode_single(text)
        
        processing_time = time.time() - start_time
        
        return success_response(
            data={
                "text": text,
                "text_length": len(text),
                "embedding_dimension": len(embedding),
                "embedding_preview": embedding[:10].tolist(),  # 显示前10个维度
                "processing_time": processing_time,
                "model_info": {
                    "model_name": embedding_service.model_name,
                    "device": embedding_service.device,
                    "max_length": embedding_service.max_length
                }
            },
            message="Qwen3-8B嵌入测试完成"
        )
        
    except Exception as e:
        logger.error(f"嵌入测试失败: {e}")
        return error_response(message=f"嵌入测试失败: {str(e)}")


@router.post("/test-chunking", summary="测试智能分块")
async def test_intelligent_chunking(
    text: str = Form(..., description="要分块的文本"),
    chunk_size: int = Form(800, description="分块大小"),
    chunk_overlap: int = Form(200, description="重叠大小"),
    strategy: str = Form("adaptive", description="分块策略"),
    current_user: User = Depends(get_current_user)
):
    """测试智能分块功能"""
    try:
        chunker = EnhancedChunker()
        
        config = EnhancedChunkConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy,
            preserve_structure=True
        )
        
        start_time = time.time()
        
        # 执行分块
        chunks = await chunker.chunk_document(
            content=text,
            metadata={"source": "test"},
            config=config
        )
        
        processing_time = time.time() - start_time
        
        # 构建响应数据
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "index": i,
                "content": chunk.content,
                "content_type": chunk.content_type,
                "quality_score": chunk.quality_score,
                "semantic_coherence": chunk.semantic_coherence,
                "structure_integrity": chunk.structure_integrity,
                "readability_score": chunk.readability_score,
                "overall_score": chunk.overall_score(),
                "char_count": len(chunk.content),
                "metadata": chunk.metadata
            })
        
        return success_response(
            data={
                "original_text_length": len(text),
                "total_chunks": len(chunks),
                "processing_time": processing_time,
                "config": config.__dict__,
                "chunks": chunk_data,
                "average_quality": sum(chunk.quality_score for chunk in chunks) / len(chunks) if chunks else 0
            },
            message="智能分块测试完成"
        )
        
    except Exception as e:
        logger.error(f"分块测试失败: {e}")
        return error_response(message=f"分块测试失败: {str(e)}")


@router.post("/test-milvus", summary="测试Milvus向量存储和检索")
async def test_milvus_operations(
    current_user: User = Depends(get_current_user)
):
    """测试Milvus向量数据库操作"""
    try:
        # 连接Milvus
        await milvus_service.connect()
        
        # 生成测试数据
        test_texts = [
            "这是一个测试文档，用于验证Milvus向量存储功能。",
            "人工智能技术正在快速发展，改变着我们的生活方式。",
            "企业级RAG系统需要高效的向量检索能力。"
        ]
        
        embedding_service = QwenEmbeddingService()
        embeddings = await embedding_service.encode_batch(test_texts)
        
        # 准备向量数据
        vector_data = []
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            vector_data.append({
                "id": 1000 + i,  # 使用测试ID
                "document_id": 999,
                "knowledge_base_id": 1,
                "chunk_index": i,
                "content": text,
                "vector": embedding.tolist()
            })
        
        start_time = time.time()
        
        # 插入向量
        await milvus_service.insert_vectors(vector_data)
        
        # 执行搜索
        search_results = await milvus_service.search_vectors(
            vector=embeddings[0].tolist(),
            top_k=5,
            score_threshold=0.5
        )
        
        processing_time = time.time() - start_time
        
        # 获取集合统计
        stats = await milvus_service.get_collection_stats()
        
        return success_response(
            data={
                "inserted_vectors": len(vector_data),
                "search_results_count": len(search_results),
                "processing_time": processing_time,
                "collection_stats": stats,
                "search_results": search_results[:3],  # 显示前3个结果
                "test_query": test_texts[0]
            },
            message="Milvus向量存储和检索测试完成"
        )
        
    except Exception as e:
        logger.error(f"Milvus测试失败: {e}")
        return error_response(message=f"Milvus测试失败: {str(e)}")


@router.post("/test-neo4j", summary="测试Neo4j知识图谱")
async def test_neo4j_operations(
    current_user: User = Depends(get_current_user)
):
    """测试Neo4j知识图谱操作"""
    try:
        graph_service = Neo4jGraphService()
        await graph_service.connect()
        
        start_time = time.time()
        
        # 创建测试文档节点
        doc_success = await graph_service.create_document_node(
            document_id=999,
            knowledge_base_id=1,
            metadata={
                "filename": "test_document.pdf",
                "file_type": ".pdf",
                "file_size": 1024,
                "total_chunks": 3,
                "created_at": time.time()
            }
        )
        
        # 创建测试分块节点
        chunk_success = await graph_service.create_chunk_node(
            chunk_id="999_0",
            document_id=999,
            chunk_index=0,
            content="这是一个测试分块，包含人工智能相关内容。",
            metadata={
                "content_hash": "test_hash",
                "chunk_type": "text",
                "char_count": 25,
                "created_at": time.time()
            }
        )
        
        # 创建测试实体节点
        entity_success = await graph_service.create_entity_node(
            name="人工智能",
            entity_type="CONCEPT",
            metadata={
                "confidence": 0.95,
                "source_chunk": "999_0",
                "context": "人工智能技术"
            }
        )
        
        processing_time = time.time() - start_time
        
        return success_response(
            data={
                "document_node_created": doc_success,
                "chunk_node_created": chunk_success,
                "entity_node_created": entity_success,
                "processing_time": processing_time,
                "test_data": {
                    "document_id": 999,
                    "chunk_id": "999_0",
                    "entity_name": "人工智能"
                }
            },
            message="Neo4j知识图谱测试完成"
        )
        
    except Exception as e:
        logger.error(f"Neo4j测试失败: {e}")
        return error_response(message=f"Neo4j测试失败: {str(e)}")


@router.post("/test-full-pipeline", summary="测试完整处理管道")
async def test_full_pipeline(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """测试完整的文档处理管道"""
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 初始化处理管道
        pipeline = DocumentProcessingPipeline()
        await pipeline.initialize()
        
        start_time = time.time()
        
        # 执行完整处理流程
        result = await pipeline.process_document(
            file_path=tmp_file_path,
            filename=file.filename,
            document_id=998,  # 测试文档ID
            knowledge_base_id=1
        )
        
        processing_time = time.time() - start_time
        
        # 清理临时文件
        Path(tmp_file_path).unlink(missing_ok=True)
        
        return success_response(
            data={
                "filename": file.filename,
                "processing_success": result.success,
                "total_chunks": result.total_chunks,
                "total_entities": result.total_entities,
                "total_relations": result.total_relations,
                "processing_time": processing_time,
                "pipeline_time": result.processing_time,
                "error_message": result.error_message,
                "metadata": result.metadata
            },
            message="完整处理管道测试完成"
        )
        
    except Exception as e:
        logger.error(f"完整管道测试失败: {e}")
        return error_response(message=f"完整管道测试失败: {str(e)}")


@router.get("/status", summary="获取第一阶段组件状态")
async def get_stage1_status(
    current_user: User = Depends(get_current_user)
):
    """获取第一阶段各组件的状态"""
    try:
        status_data = {
            "marker_service": {
                "available": marker_service.marker_enabled,
                "models_loaded": marker_service.marker_models is not None
            },
            "embedding_service": {
                "initialized": False,
                "model_name": "Qwen/Qwen3-8B",
                "device": "cpu"
            },
            "milvus_service": {
                "connected": milvus_service._connected,
                "collection_name": milvus_service.collection_name
            },
            "neo4j_service": {
                "connected": False,
                "uri": "neo4j://localhost:7687"
            }
        }
        
        # 检查嵌入服务状态
        try:
            embedding_service = QwenEmbeddingService()
            status_data["embedding_service"]["initialized"] = embedding_service._initialized
            status_data["embedding_service"]["device"] = embedding_service.device
        except:
            pass
        
        # 检查Neo4j状态
        try:
            graph_service = Neo4jGraphService()
            status_data["neo4j_service"]["connected"] = graph_service._connected
            status_data["neo4j_service"]["uri"] = graph_service.uri
        except:
            pass
        
        return success_response(
            data=status_data,
            message="第一阶段组件状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return error_response(message=f"获取状态失败: {str(e)}")
