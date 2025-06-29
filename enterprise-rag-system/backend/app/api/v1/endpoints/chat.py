"""
聊天API端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import QueryContext
from app import (
    workflow_orchestrator,
    WorkflowConfig,
    WorkflowType
)
from app.core import get_current_user
from app.models import Conversation, Message
from app.models import User

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user, assistant, system
    content: str
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[int] = None
    knowledge_base_ids: Optional[List[int]] = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2000


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    conversation_id: int
    message_id: int
    sources: List[dict] = []
    metadata: dict = {}


@router.post("/", response_model=ChatResponse, summary="发送消息")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    发送消息
    """
    try:
        # 1. 获取或创建对话
        if request.conversation_id:
            conversation = await Conversation.get_or_none(
                id=request.conversation_id,
                user_id=current_user.id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="对话不存在"
                )
        else:
            # 创建新对话
            conversation = await Conversation.create(
                user_id=current_user.id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )

        # 2. 保存用户消息
        user_message = await Message.create(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            metadata=request.metadata or {}
        )

        # 3. 获取对话历史
        conversation_history = await Message.filter(
            conversation_id=conversation.id
        ).order_by("-created_at").limit(10)

        history_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(conversation_history)
        ]

        # 4. 构建查询上下文
        context = QueryContext(
            query=request.message,
            user_id=current_user.id,
            knowledge_base_ids=request.knowledge_base_ids or [],
            conversation_history=history_messages,
            metadata={"conversation_id": conversation.id}
        )

        # 5. 配置工作流
        config = WorkflowConfig(
            workflow_type=WorkflowType.MULTI_SOURCE,
            enable_vector_search=True,
            enable_graph_search=True,
            enable_result_fusion=True
        )

        # 6. 执行工作流
        workflow_result = await workflow_orchestrator.execute_workflow(
            context, config
        )

        # 7. 保存助手回复
        assistant_message = await Message.create(
            conversation_id=conversation.id,
            role="assistant",
            content=workflow_result.answer,
            metadata={
                "sources": workflow_result.sources,
                "confidence_score": workflow_result.confidence_score,
                "processing_time": workflow_result.processing_time
            }
        )

        # 8. 更新对话的最后活动时间
        await conversation.update_last_activity()

        return ChatResponse(
            message=workflow_result.answer,
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            sources=workflow_result.sources,
            metadata=workflow_result.metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )


@router.post("/stream", summary="流式聊天")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    流式聊天
    """
    async def generate_stream():
        try:
            # 1. 获取或创建对话
            if request.conversation_id:
                conversation = await Conversation.get_or_none(
                    id=request.conversation_id,
                    user_id=current_user.id
                )
                if not conversation:
                    yield f"data: {{'error': '对话不存在'}}\n\n"
                    return
            else:
                # 创建新对话
                conversation = await Conversation.create(
                    user_id=current_user.id,
                    title=request.message[:50] + "..." if len(request.message) > 50 else request.message
                )

            # 2. 保存用户消息
            user_message = await Message.create(
                conversation_id=conversation.id,
                role="user",
                content=request.message,
                metadata=request.metadata or {}
            )

            # 3. 获取对话历史
            conversation_history = await Message.filter(
                conversation_id=conversation.id
            ).order_by("-created_at").limit(10)

            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(conversation_history)
            ]

            # 4. 构建查询上下文
            context = QueryContext(
                query=request.message,
                user_id=current_user.id,
                knowledge_base_ids=request.knowledge_base_ids or [],
                conversation_history=history_messages,
                metadata={"conversation_id": conversation.id}
            )

            # 5. 配置工作流
            config = WorkflowConfig(
                workflow_type=WorkflowType.MULTI_SOURCE,
                enable_vector_search=True,
                enable_graph_search=True,
                enable_result_fusion=True
            )

            # 6. 流式执行工作流
            answer_chunks = []
            async for event in workflow_orchestrator.execute_workflow_stream(context, config):
                if event["type"] == "answer_chunk":
                    chunk = event["data"]["chunk"]
                    answer_chunks.append(chunk)
                    yield f"data: {{'type': 'chunk', 'content': '{chunk}'}}\n\n"
                elif event["type"] == "workflow_complete":
                    # 保存完整的助手回复
                    full_answer = "".join(answer_chunks)
                    assistant_message = await Message.create(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_answer,
                        metadata={
                            "sources": event["data"]["sources"],
                            "confidence_score": event["data"]["confidence_score"]
                        }
                    )

                    # 发送完成事件
                    yield f"data: {{'type': 'complete', 'conversation_id': {conversation.id}, 'message_id': {assistant_message.id}}}\n\n"
                elif event["type"] == "workflow_error":
                    yield f"data: {{'type': 'error', 'error': '{event['data']['error']}'}}\n\n"
                else:
                    # 发送其他事件
                    import json
                    yield f"data: {json.dumps(event)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {{'type': 'error', 'error': '{str(e)}'}}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )
