"""
对话管理API端点
"""

from typing import Any, List, Optional

from app.core.security import get_current_user
from app.models.conversation import Conversation, Message
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

router = APIRouter()


class ConversationResponse(BaseModel):
    """对话响应"""
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    size: int


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    created_at: str
    metadata: dict = {}


@router.get("/", response_model=ConversationListResponse, summary="获取对话列表")
async def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取对话列表
    """
    # 计算偏移量
    offset = (page - 1) * size

    # 获取对话列表
    conversations = await Conversation.filter(
        user_id=current_user.id,
        is_deleted=False
    ).order_by("-updated_at").offset(offset).limit(size)

    # 获取总数
    total = await Conversation.filter(
        user_id=current_user.id,
        is_deleted=False
    ).count()

    # 构建响应
    conversation_list = []
    for conv in conversations:
        # 获取消息数量
        message_count = await Message.filter(conversation_id=conv.id).count()

        conversation_list.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=message_count
        ))

    return ConversationListResponse(
        conversations=conversation_list,
        total=total,
        page=page,
        size=size
    )


@router.get("/{conversation_id}", summary="获取对话详情")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取对话详情
    """
    conversation = await Conversation.get_or_none(
        id=conversation_id,
        user_id=current_user.id,
        is_deleted=False
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 获取消息列表
    messages = await Message.filter(
        conversation_id=conversation_id
    ).order_by("created_at")

    message_list = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
            metadata=msg.metadata or {}
        )
        for msg in messages
    ]

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": message_list
    }


@router.post("/", summary="创建对话")
async def create_conversation(
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建对话
    """
    conversation = await Conversation.create(
        user_id=current_user.id,
        title=title or "新对话"
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "message_count": 0
    }


@router.delete("/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除对话
    """
    conversation = await Conversation.get_or_none(
        id=conversation_id,
        user_id=current_user.id,
        is_deleted=False
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 软删除
    conversation.is_deleted = True
    await conversation.save()

    return {"message": "对话删除成功"}
