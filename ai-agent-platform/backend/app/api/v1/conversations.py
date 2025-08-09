"""
# Copyright (c) 2025 左岚. All rights reserved.

对话管理API
"""

# # Standard library imports
import asyncio
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

# # Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# # Local application imports
from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.agent import Agent
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新对话
    """
    # 验证智能体是否存在
    agent = db.query(Agent).filter(Agent.id == conversation_data.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 创建对话
    conversation = Conversation(
        title=conversation_data.title or f"与{agent.name}的对话",
        user_id=current_user.id,
        agent_id=conversation_data.agent_id,
        status="active"
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 20,
    agent_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的对话列表
    """
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if agent_id:
        query = query.filter(Conversation.agent_id == agent_id)
    
    conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定对话详情
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新对话信息
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 更新对话信息
    update_data = conversation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除对话
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "对话删除成功"}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取对话消息列表
    """
    # 验证对话权限
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息
    """
    # 验证对话权限
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        content=message_data.content,
        role="user",
        message_type=message_data.message_type or "text"
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 更新对话的最后活动时间
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return user_message


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息并获取流式响应
    """
    # 验证对话权限
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        content=message_data.content,
        role="user",
        message_type=message_data.message_type or "text"
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    async def generate_response():
        """生成流式响应"""
        # 这里应该调用实际的AI模型
        # 目前先返回模拟响应
        response_text = f"这是对消息'{message_data.content}'的回复。"
        
        # 创建助手消息
        assistant_message = Message(
            conversation_id=conversation_id,
            content="",
            role="assistant",
            message_type="text"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # 模拟流式输出
        for i, char in enumerate(response_text):
            await asyncio.sleep(0.05)  # 模拟延迟
            assistant_message.content += char
            
            yield f"data: {json.dumps({'content': char, 'message_id': assistant_message.id})}\n\n"
        
        # 保存完整的助手消息
        db.commit()
        
        # 更新对话时间
        conversation.updated_at = datetime.utcnow()
        db.commit()
        
        yield f"data: {json.dumps({'done': True, 'message_id': assistant_message.id})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


# WebSocket功能已移除，使用SSE (Server-Sent Events) 替代
# 相关实现请参考 app/sse/ 模块


# WebSocket端点已移除
# 实时通信功能已迁移到SSE (Server-Sent Events)
# 请使用 /api/v1/conversations/{conversation_id}/stream 端点
