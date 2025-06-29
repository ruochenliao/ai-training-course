"""
高级搜索API端点
"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app import (
    advanced_search_service,
    SearchConfig,
    SearchType
)
from app.core import SearchException
from app.core import get_current_user
from app.models import User

router = APIRouter()


class AdvancedSearchRequest(BaseModel):
    """高级搜索请求"""
    query: str = Field(..., description="搜索查询")
    knowledge_base_id: int = Field(..., description="知识库ID")
    search_type: SearchType = Field(SearchType.HYBRID, description="搜索类型")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数量")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="分数阈值")
    enable_rerank: bool = Field(True, description="是否启用重排序")
    rerank_top_k: int = Field(20, ge=1, le=100, description="重排序候选数量")
    vector_weight: float = Field(0.7, ge=0.0, le=1.0, description="向量搜索权重")
    graph_weight: float = Field(0.3, ge=0.0, le=1.0, description="图搜索权重")
    keyword_weight: float = Field(0.2, ge=0.0, le=1.0, description="关键词搜索权重")
    enable_expansion: bool = Field(True, description="是否启用查询扩展")
    expansion_terms: int = Field(3, ge=1, le=10, description="扩展词数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class SearchResultResponse(BaseModel):
    """搜索结果响应"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str
    chunk_index: int = 0
    document_id: str = ""


class AdvancedSearchResponse(BaseModel):
    """高级搜索响应"""
    results: List[SearchResultResponse]
    total: int
    query: str
    search_type: str
    execution_time: float


@router.post("/search", response_model=AdvancedSearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行高级搜索
    """
    try:
        import time
        start_time = time.time()
        
        # 构建搜索配置
        config = SearchConfig(
            search_type=request.search_type,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            enable_rerank=request.enable_rerank,
            rerank_top_k=request.rerank_top_k,
            vector_weight=request.vector_weight,
            graph_weight=request.graph_weight,
            keyword_weight=request.keyword_weight,
            enable_expansion=request.enable_expansion,
            expansion_terms=request.expansion_terms,
            filters=request.filters or {}
        )
        
        # 执行搜索
        results = await advanced_search_service.search(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            config=config
        )
        
        execution_time = time.time() - start_time
        
        # 转换结果格式
        search_results = [
            SearchResultResponse(
                id=result.id,
                content=result.content,
                score=result.score,
                metadata=result.metadata,
                source=result.source,
                chunk_index=result.chunk_index,
                document_id=result.document_id
            )
            for result in results
        ]
        
        return AdvancedSearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            search_type=request.search_type.value,
            execution_time=execution_time
        )
        
    except SearchException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/search-types")
async def get_search_types():
    """
    获取支持的搜索类型
    """
    return {
        "search_types": [
            {
                "value": search_type.value,
                "name": search_type.name,
                "description": _get_search_type_description(search_type)
            }
            for search_type in SearchType
        ]
    }


@router.post("/search/vector", response_model=AdvancedSearchResponse)
async def vector_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行向量搜索
    """
    request.search_type = SearchType.VECTOR
    return await advanced_search(request, current_user)


@router.post("/search/graph", response_model=AdvancedSearchResponse)
async def graph_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行图搜索
    """
    request.search_type = SearchType.GRAPH
    return await advanced_search(request, current_user)


@router.post("/search/hybrid", response_model=AdvancedSearchResponse)
async def hybrid_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行混合搜索
    """
    request.search_type = SearchType.HYBRID
    return await advanced_search(request, current_user)


@router.post("/search/semantic", response_model=AdvancedSearchResponse)
async def semantic_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行语义搜索
    """
    request.search_type = SearchType.SEMANTIC
    return await advanced_search(request, current_user)


@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="部分查询"),
    knowledge_base_id: int = Query(..., description="知识库ID"),
    limit: int = Query(5, ge=1, le=20, description="建议数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取搜索建议
    """
    try:
        # 这里可以实现搜索建议逻辑
        # 目前返回简单的模拟数据
        suggestions = [
            f"{query} 相关内容",
            f"{query} 详细信息",
            f"{query} 使用方法",
            f"{query} 最佳实践",
            f"{query} 常见问题"
        ][:limit]
        
        return {
            "suggestions": suggestions,
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")


def _get_search_type_description(search_type: SearchType) -> str:
    """获取搜索类型描述"""
    descriptions = {
        SearchType.VECTOR: "基于向量相似度的语义搜索",
        SearchType.GRAPH: "基于知识图谱的关系搜索",
        SearchType.HYBRID: "结合向量和图谱的混合搜索",
        SearchType.SEMANTIC: "增强的语义搜索，支持查询扩展",
        SearchType.KEYWORD: "基于关键词的全文搜索",
        SearchType.FUZZY: "支持模糊匹配的搜索"
    }
    return descriptions.get(search_type, "未知搜索类型")
