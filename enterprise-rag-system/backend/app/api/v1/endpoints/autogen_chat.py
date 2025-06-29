"""
AutoGen多智能体聊天API端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services import autogen_agent_service as autogen_service
from app.core import get_current_user
from app.models import User

router = APIRouter()


class AutoGenChatRequest(BaseModel):
    """AutoGen聊天请求"""
    query: str
    knowledge_base_ids: Optional[List[int]] = None
    conversation_id: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class AutoGenChatResponse(BaseModel):
    """AutoGen聊天响应"""
    query: str
    answer: str
    sources: List[dict] = []
    confidence: float
    processing_time: float
    conversation_id: Optional[int] = None
    agent_results: dict = {}
    metadata: dict = {}


@router.post("/chat", response_model=AutoGenChatResponse, summary="AutoGen多智能体聊天")
async def autogen_chat(
    request: AutoGenChatRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    使用AutoGen多智能体协作处理用户查询
    """
    try:
        # 调用AutoGen服务
        result = await autogen_service.process_query(
            query=request.query,
            knowledge_base_ids=request.knowledge_base_ids,
            user_id=current_user.id,
            conversation_context=None  # 可以从conversation_id获取历史对话
        )
        
        return AutoGenChatResponse(
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            processing_time=result["processing_time"],
            conversation_id=request.conversation_id,
            agent_results=result.get("agent_results", {}),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AutoGen聊天处理失败: {str(e)}"
        )


@router.get("/agents/status", summary="获取智能体状态")
async def get_agents_status(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取AutoGen智能体的状态信息
    """
    try:
        # 检查智能体是否已初始化
        if not autogen_service._initialized:
            await autogen_service.initialize()
        
        return {
            "initialized": autogen_service._initialized,
            "agents": [
                {
                    "name": "RetrievalExpert",
                    "description": "检索专家，负责从知识库中检索相关信息",
                    "status": "active"
                },
                {
                    "name": "AnalysisExpert", 
                    "description": "分析专家，负责分析和整合检索到的信息",
                    "status": "active"
                },
                {
                    "name": "AnswerGenerator",
                    "description": "回答生成专家，负责生成高质量的回答",
                    "status": "active"
                },
                {
                    "name": "QualityController",
                    "description": "质量控制专家，负责评估和改进回答质量",
                    "status": "active"
                }
            ],
            "llm_config": {
                "model": autogen_service.llm_config.get("model"),
                "temperature": autogen_service.llm_config.get("temperature"),
                "max_tokens": autogen_service.llm_config.get("max_tokens")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体状态失败: {str(e)}"
        )
