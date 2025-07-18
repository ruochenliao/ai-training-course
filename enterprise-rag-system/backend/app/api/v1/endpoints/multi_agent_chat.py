"""
多智能体协作聊天API端点 - 第二阶段核心功能
支持多模式检索选择和智能体协作答案融合
"""

import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from loguru import logger

from app.core.response import success_response, error_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.multi_agent_coordinator import (
    MultiAgentCoordinator, 
    SearchRequest, 
    SearchMode,
    multi_agent_coordinator
)

router = APIRouter(prefix="/multi-agent", tags=["多智能体协作"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str = Field(..., description="用户查询")
    search_modes: List[str] = Field(
        default=["semantic"], 
        description="检索模式: semantic, hybrid, graph, all"
    )
    top_k: int = Field(default=10, ge=1, le=50, description="返回结果数量")
    knowledge_base_ids: Optional[List[int]] = Field(default=None, description="知识库ID列表")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    stream: bool = Field(default=False, description="是否流式返回")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    query: str
    answer: str
    search_results: List[Dict[str, Any]]
    quality_assessment: Dict[str, Any]
    processing_time: float
    modes_used: List[str]
    metadata: Dict[str, Any]


class SearchModeInfo(BaseModel):
    """检索模式信息"""
    mode: str
    name: str
    description: str
    enabled: bool = True


@router.post("/chat", response_model=ChatResponse, summary="多智能体协作问答")
async def multi_agent_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    多智能体协作问答
    
    支持的检索模式：
    - semantic: 语义检索（基于向量相似度）
    - hybrid: 混合检索（语义+关键词）
    - graph: 图谱检索（基于实体关系）
    - all: 使用所有检索模式
    """
    try:
        # 验证检索模式
        valid_modes = {"semantic", "hybrid", "graph", "all"}
        invalid_modes = set(request.search_modes) - valid_modes
        if invalid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"无效的检索模式: {invalid_modes}. 支持的模式: {valid_modes}"
            )
        
        # 转换检索模式
        search_modes = []
        for mode_str in request.search_modes:
            try:
                search_modes.append(SearchMode(mode_str))
            except ValueError:
                logger.warning(f"无效的检索模式: {mode_str}")
        
        if not search_modes:
            search_modes = [SearchMode.SEMANTIC]  # 默认使用语义检索
        
        # 构建检索请求
        search_request = SearchRequest(
            query=request.query,
            modes=search_modes,
            top_k=request.top_k,
            knowledge_base_ids=request.knowledge_base_ids,
            user_id=current_user.id,
            session_id=request.session_id,
            metadata={"user_agent": "web", "timestamp": "now"}
        )
        
        # 执行多智能体协作
        result = await multi_agent_coordinator.process_request(search_request)
        
        # 转换搜索结果格式
        search_results = []
        for sr in result["search_results"]:
            search_results.append({
                "content": sr.content,
                "source": sr.source,
                "score": sr.score,
                "search_type": sr.search_type,
                "confidence": sr.confidence,
                "relevance_explanation": sr.relevance_explanation,
                "metadata": sr.metadata
            })
        
        response = ChatResponse(
            query=result["query"],
            answer=result["answer"],
            search_results=search_results,
            quality_assessment=result["quality_assessment"],
            processing_time=result["processing_time"],
            modes_used=result["modes_used"],
            metadata=result["metadata"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"多智能体聊天失败: {e}")
        raise HTTPException(status_code=500, detail=f"多智能体聊天失败: {str(e)}")


@router.get("/search-modes", summary="获取支持的检索模式")
async def get_search_modes(
    current_user: User = Depends(get_current_user)
):
    """获取支持的检索模式列表"""
    try:
        modes = [
            SearchModeInfo(
                mode="semantic",
                name="语义检索",
                description="基于Qwen3-8B嵌入模型的向量相似度搜索，适合理解查询的语义意图",
                enabled=True
            ),
            SearchModeInfo(
                mode="hybrid",
                name="混合检索",
                description="结合语义检索和关键词检索，使用RRF算法融合结果，提供更全面的检索",
                enabled=True
            ),
            SearchModeInfo(
                mode="graph",
                name="图谱检索",
                description="基于Neo4j知识图谱的实体关系搜索，适合复杂的关系推理查询",
                enabled=True
            ),
            SearchModeInfo(
                mode="all",
                name="全模式检索",
                description="同时使用所有检索模式，通过智能体协作融合最佳答案",
                enabled=True
            )
        ]
        
        return success_response(
            data={"search_modes": [mode.dict() for mode in modes]},
            message="检索模式获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取检索模式失败: {e}")
        return error_response(message=f"获取检索模式失败: {str(e)}")


@router.get("/stats", summary="获取多智能体协作统计")
async def get_multi_agent_stats(
    current_user: User = Depends(get_current_user)
):
    """获取多智能体协作统计信息"""
    try:
        stats = multi_agent_coordinator.get_stats()
        
        return success_response(
            data={
                "coordinator_stats": stats,
                "agent_info": {
                    "total_agents": 5,
                    "active_agents": ["semantic_searcher", "hybrid_searcher", "graph_searcher", "answer_fusion", "quality_assessor"],
                    "agent_roles": {
                        "semantic_searcher": "语义检索智能体",
                        "hybrid_searcher": "混合检索智能体", 
                        "graph_searcher": "图谱检索智能体",
                        "answer_fusion": "答案融合智能体",
                        "quality_assessor": "质量评估智能体"
                    }
                },
                "performance_metrics": {
                    "avg_response_time": stats.get("avg_response_time", 0.0),
                    "total_requests": stats.get("total_requests", 0),
                    "mode_usage": stats.get("mode_usage", {})
                }
            },
            message="多智能体统计获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取多智能体统计失败: {e}")
        return error_response(message=f"获取多智能体统计失败: {str(e)}")


@router.post("/test-agents", summary="测试智能体协作")
async def test_agent_collaboration(
    query: str = "人工智能的发展历程",
    current_user: User = Depends(get_current_user)
):
    """测试智能体协作功能"""
    try:
        # 测试所有检索模式
        test_request = SearchRequest(
            query=query,
            modes=[SearchMode.ALL],
            top_k=5,
            user_id=current_user.id,
            session_id="test_session"
        )
        
        # 执行测试
        result = await multi_agent_coordinator.process_request(test_request)
        
        return success_response(
            data={
                "test_query": query,
                "test_result": {
                    "answer_generated": bool(result["answer"]),
                    "search_results_count": len(result["search_results"]),
                    "processing_time": result["processing_time"],
                    "quality_score": result["quality_assessment"].get("confidence", 0.0),
                    "modes_tested": result["modes_used"]
                },
                "detailed_result": result
            },
            message="智能体协作测试完成"
        )
        
    except Exception as e:
        logger.error(f"智能体协作测试失败: {e}")
        return error_response(message=f"智能体协作测试失败: {str(e)}")


# WebSocket支持流式对话
@router.websocket("/chat-stream")
async def multi_agent_chat_stream(
    websocket: WebSocket,
    token: str = None
):
    """多智能体协作流式对话"""
    await websocket.accept()
    
    try:
        # 这里应该验证token，简化处理
        logger.info("WebSocket连接建立")
        
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            query = data.get("query", "")
            search_modes = data.get("search_modes", ["semantic"])
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "查询不能为空"
                })
                continue
            
            # 发送处理开始消息
            await websocket.send_json({
                "type": "status",
                "message": "开始多智能体协作处理...",
                "stage": "start"
            })
            
            try:
                # 转换检索模式
                modes = []
                for mode_str in search_modes:
                    try:
                        modes.append(SearchMode(mode_str))
                    except ValueError:
                        pass
                
                if not modes:
                    modes = [SearchMode.SEMANTIC]
                
                # 构建请求
                search_request = SearchRequest(
                    query=query,
                    modes=modes,
                    top_k=10,
                    session_id="websocket_session"
                )
                
                # 发送检索阶段消息
                await websocket.send_json({
                    "type": "status",
                    "message": f"执行{len(modes)}种检索模式...",
                    "stage": "searching"
                })
                
                # 执行协作
                result = await multi_agent_coordinator.process_request(search_request)
                
                # 发送答案融合消息
                await websocket.send_json({
                    "type": "status",
                    "message": "智能体协作融合答案...",
                    "stage": "fusion"
                })
                
                # 发送最终结果
                await websocket.send_json({
                    "type": "result",
                    "data": {
                        "query": result["query"],
                        "answer": result["answer"],
                        "search_results_count": len(result["search_results"]),
                        "processing_time": result["processing_time"],
                        "quality_score": result["quality_assessment"].get("confidence", 0.0),
                        "modes_used": result["modes_used"]
                    }
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理失败: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket处理异常: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"连接异常: {str(e)}"
            })
        except:
            pass
