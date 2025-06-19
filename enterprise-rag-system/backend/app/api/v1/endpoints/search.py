"""
搜索API端点
"""

import asyncio
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import User
from app.services.agent_service import QueryContext
from app.services.workflow_service import (
    workflow_orchestrator,
    WorkflowConfig,
    WorkflowType
)

router = APIRouter()


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    knowledge_base_ids: Optional[List[int]] = None
    top_k: int = 10
    score_threshold: Optional[float] = None
    search_type: str = "hybrid"  # vector, graph, hybrid


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[dict]
    total: int
    search_type: str
    processing_time: float


@router.post("/vector", response_model=SearchResponse, summary="向量搜索")
async def vector_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    向量搜索
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # 构建查询上下文
        context = QueryContext(
            query=request.query,
            user_id=current_user.id,
            knowledge_base_ids=request.knowledge_base_ids or [],
            metadata={"search_type": "vector"}
        )

        # 配置只使用向量搜索的工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.SIMPLE_QA,
            enable_vector_search=True,
            enable_graph_search=False,
            enable_result_fusion=False
        )

        # 执行工作流
        workflow_result = await workflow_orchestrator.execute_workflow(
            context, config
        )

        # 构建搜索结果
        results = []
        for source in workflow_result.sources:
            result = {
                "id": source["id"],
                "content": source["content_preview"],
                "score": source["score"],
                "source_type": source["source_type"],
                "metadata": source["metadata"]
            }
            results.append(result)

        processing_time = asyncio.get_event_loop().time() - start_time

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            search_type="vector",
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"向量搜索失败: {str(e)}"
        )


@router.post("/graph", response_model=SearchResponse, summary="图谱搜索")
async def graph_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    图谱搜索
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # 构建查询上下文
        context = QueryContext(
            query=request.query,
            user_id=current_user.id,
            knowledge_base_ids=request.knowledge_base_ids or [],
            metadata={"search_type": "graph"}
        )

        # 配置只使用图谱搜索的工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.REASONING,
            enable_vector_search=False,
            enable_graph_search=True,
            enable_result_fusion=False
        )

        # 执行工作流
        workflow_result = await workflow_orchestrator.execute_workflow(
            context, config
        )

        # 构建搜索结果
        results = []
        for source in workflow_result.sources:
            result = {
                "id": source["id"],
                "content": source["content_preview"],
                "score": source["score"],
                "source_type": source["source_type"],
                "metadata": source["metadata"]
            }
            results.append(result)

        processing_time = asyncio.get_event_loop().time() - start_time

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            search_type="graph",
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图谱搜索失败: {str(e)}"
        )


@router.post("/hybrid", response_model=SearchResponse, summary="混合搜索")
async def hybrid_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    混合搜索 - 使用完整的RAG工作流
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # 构建查询上下文
        context = QueryContext(
            query=request.query,
            user_id=current_user.id,
            knowledge_base_ids=request.knowledge_base_ids or [],
            metadata={"search_type": "hybrid"}
        )

        # 配置混合搜索工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.MULTI_SOURCE,
            enable_vector_search=True,
            enable_graph_search=True,
            enable_result_fusion=True
        )

        # 执行工作流
        workflow_result = await workflow_orchestrator.execute_workflow(
            context, config
        )

        # 构建搜索结果
        results = []
        for source in workflow_result.sources:
            result = {
                "id": source["id"],
                "content": source["content_preview"],
                "score": source["score"],
                "source_type": source["source_type"],
                "metadata": source["metadata"]
            }
            results.append(result)

        processing_time = asyncio.get_event_loop().time() - start_time

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            search_type="hybrid",
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"混合搜索失败: {str(e)}"
        )
