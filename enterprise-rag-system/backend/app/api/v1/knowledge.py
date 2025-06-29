"""
知识库管理API端点 - 企业级RAG系统
严格按照技术栈要求：/api/v1/knowledge/ 知识库处理流水线
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import document_processing_pipeline as document_pipeline
from app.services import milvus_service
from app.services import neo4j_graph_service as neo4j_service
from app.core import get_current_user
from app.core import get_db_session
from app.models import KnowledgeBase, User, Document

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Pydantic 模型
class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = False
    settings: Optional[Dict[str, Any]] = None


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_public: bool
    settings: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # 统计信息
    total_documents: Optional[int] = 0
    total_chunks: Optional[int] = 0
    total_vectors: Optional[int] = 0
    total_entities: Optional[int] = 0
    total_relations: Optional[int] = 0


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1)
    search_type: str = Field(default="hybrid", regex="^(semantic|hybrid|graph)$")
    top_k: int = Field(default=20, ge=1, le=100)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    document_filter: Optional[int] = None
    entity_types: Optional[List[str]] = None


class SearchResult(BaseModel):
    """搜索结果"""
    id: str
    content: str
    score: float
    document_id: int
    chunk_index: int
    metadata: Dict[str, Any]
    source_type: str  # vector, graph, hybrid


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    search_type: str
    total_results: int
    results: List[SearchResult]
    processing_time_ms: float


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建知识库"""
    try:
        # 创建知识库记录
        knowledge_base = KnowledgeBase(
            name=request.name,
            description=request.description,
            owner_id=current_user.id,
            is_public=request.is_public,
            settings=request.settings or {}
        )
        
        db.add(knowledge_base)
        await db.commit()
        await db.refresh(knowledge_base)
        
        # 创建对应的Milvus集合
        try:
            collection_name = await milvus_service.create_knowledge_base_collection(knowledge_base.id)
            logger.info(f"知识库向量集合创建成功: {collection_name}")
        except Exception as e:
            logger.error(f"创建向量集合失败: {e}")
            # 不影响知识库创建，但记录错误
        
        return KnowledgeBaseResponse(
            id=knowledge_base.id,
            name=knowledge_base.name,
            description=knowledge_base.description,
            owner_id=knowledge_base.owner_id,
            is_public=knowledge_base.is_public,
            settings=knowledge_base.settings,
            created_at=knowledge_base.created_at,
            updated_at=knowledge_base.updated_at
        )
        
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库列表"""
    try:
        # TODO: 实现知识库列表查询逻辑
        # 1. 查询用户有权限访问的知识库
        # 2. 支持搜索过滤
        # 3. 分页处理
        # 4. 获取统计信息
        
        # 模拟返回数据
        return [
            KnowledgeBaseResponse(
                id=1,
                name="示例知识库",
                description="这是一个示例知识库",
                owner_id=current_user.id,
                is_public=False,
                settings={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                total_documents=5,
                total_chunks=50,
                total_vectors=50,
                total_entities=100,
                total_relations=80
            )
        ]
        
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取知识库详情"""
    try:
        # TODO: 实现知识库详情查询逻辑
        # 1. 查询知识库基本信息
        # 2. 检查用户权限
        # 3. 获取统计信息
        
        # 获取处理统计信息
        stats = await document_pipeline.get_processing_stats(knowledge_base_id)
        
        return KnowledgeBaseResponse(
            id=knowledge_base_id,
            name="示例知识库",
            description="这是一个示例知识库",
            owner_id=current_user.id,
            is_public=False,
            settings={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_documents=stats.get("vector_stats", {}).get("row_count", 0),
            total_chunks=stats.get("vector_stats", {}).get("row_count", 0),
            total_vectors=stats.get("vector_stats", {}).get("row_count", 0),
            total_entities=stats.get("graph_stats", {}).get("entity_count", 0),
            total_relations=stats.get("graph_stats", {}).get("relation_count", 0)
        )
        
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库详情失败: {str(e)}")


@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: int,
    request: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新知识库"""
    try:
        # TODO: 实现知识库更新逻辑
        # 1. 查询知识库
        # 2. 检查权限
        # 3. 更新字段
        
        return KnowledgeBaseResponse(
            id=knowledge_base_id,
            name=request.name or "示例知识库",
            description=request.description,
            owner_id=current_user.id,
            is_public=request.is_public or False,
            settings=request.settings or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新知识库失败: {str(e)}")


@router.delete("/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除知识库"""
    try:
        # TODO: 实现知识库删除逻辑
        # 1. 检查权限
        # 2. 删除所有文档数据
        # 3. 删除向量集合
        # 4. 删除图谱数据
        # 5. 删除数据库记录
        
        return {
            "success": True,
            "message": "知识库删除成功",
            "knowledge_base_id": knowledge_base_id
        }
        
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")


@router.post("/{knowledge_base_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    knowledge_base_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """搜索知识库"""
    try:
        start_time = datetime.now()
        
        if request.search_type == "semantic":
            # 语义检索
            results = await _semantic_search(knowledge_base_id, request)
        elif request.search_type == "graph":
            # 图谱检索
            results = await _graph_search(knowledge_base_id, request)
        elif request.search_type == "hybrid":
            # 混合检索
            results = await _hybrid_search(knowledge_base_id, request)
        else:
            raise HTTPException(status_code=400, detail="不支持的搜索类型")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            total_results=len(results),
            results=results,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{knowledge_base_id}/entities")
async def search_entities(
    knowledge_base_id: int,
    query: str = Query(..., min_length=1),
    entity_types: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """搜索实体"""
    try:
        entities = await neo4j_service.search_entities(
            knowledge_base_id, query, entity_types, limit
        )
        
        return {
            "query": query,
            "total_results": len(entities),
            "entities": entities
        }
        
    except Exception as e:
        logger.error(f"搜索实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


@router.get("/{knowledge_base_id}/entities/{entity_name}/relations")
async def get_entity_relations(
    knowledge_base_id: int,
    entity_name: str,
    max_hops: int = Query(2, ge=1, le=3),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """获取实体关系"""
    try:
        related_entities = await neo4j_service.find_related_entities(
            entity_name, knowledge_base_id, max_hops, limit
        )
        
        return {
            "entity_name": entity_name,
            "max_hops": max_hops,
            "total_results": len(related_entities),
            "related_entities": related_entities
        }
        
    except Exception as e:
        logger.error(f"获取实体关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {str(e)}")


@router.get("/{knowledge_base_id}/stats")
async def get_knowledge_base_stats(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取知识库统计信息"""
    try:
        stats = await document_pipeline.get_processing_stats(knowledge_base_id)
        
        return {
            "knowledge_base_id": knowledge_base_id,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 内部搜索函数
async def _semantic_search(knowledge_base_id: int, request: SearchRequest) -> List[SearchResult]:
    """语义检索"""
    try:
        # 使用Milvus进行语义检索
        milvus_results = await milvus_service.search_vectors(
            f"kb_{knowledge_base_id}",
            request.query,
            request.top_k,
            f"document_id == {request.document_filter}" if request.document_filter else None
        )
        
        results = []
        for result in milvus_results:
            if result["score"] >= request.threshold:
                results.append(SearchResult(
                    id=result["id"],
                    content=result["content"],
                    score=result["score"],
                    document_id=result["document_id"],
                    chunk_index=result["chunk_index"],
                    metadata=result["metadata"],
                    source_type="vector"
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"语义检索失败: {e}")
        return []


async def _graph_search(knowledge_base_id: int, request: SearchRequest) -> List[SearchResult]:
    """图谱检索"""
    try:
        # 搜索相关实体
        entities = await neo4j_service.search_entities(
            knowledge_base_id, request.query, request.entity_types, request.top_k
        )
        
        results = []
        for entity in entities:
            # 获取实体上下文
            contexts = await neo4j_service.get_entity_context(
                entity["name"], knowledge_base_id, 5
            )
            
            for context in contexts:
                results.append(SearchResult(
                    id=context["chunk_id"],
                    content=context["content"],
                    score=entity["confidence"],
                    document_id=context["document_id"],
                    chunk_index=context["chunk_index"],
                    metadata={"entity": entity["name"], "entity_type": entity["type"]},
                    source_type="graph"
                ))
        
        return results[:request.top_k]
        
    except Exception as e:
        logger.error(f"图谱检索失败: {e}")
        return []


async def _hybrid_search(knowledge_base_id: int, request: SearchRequest) -> List[SearchResult]:
    """混合检索"""
    try:
        # 并行执行语义检索和图谱检索
        semantic_results, graph_results = await asyncio.gather(
            _semantic_search(knowledge_base_id, request),
            _graph_search(knowledge_base_id, request)
        )
        
        # 合并结果并去重
        all_results = {}
        
        # 添加语义检索结果
        for result in semantic_results:
            all_results[result.id] = result
        
        # 添加图谱检索结果
        for result in graph_results:
            if result.id in all_results:
                # 融合分数
                existing = all_results[result.id]
                existing.score = (existing.score + result.score) / 2
                existing.source_type = "hybrid"
                existing.metadata.update(result.metadata)
            else:
                result.source_type = "graph"
                all_results[result.id] = result
        
        # 按分数排序
        sorted_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        
        return sorted_results[:request.top_k]
        
    except Exception as e:
        logger.error(f"混合检索失败: {e}")
        return []
