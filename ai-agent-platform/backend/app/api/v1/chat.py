"""
# Copyright (c) 2025 左岚. All rights reserved.

聊天API - 简化的聊天接口
"""

# # Standard library imports
import asyncio
from datetime import datetime
import json
from typing import Optional

# # Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# # Local application imports
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.agent import Agent
from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送聊天消息（简化版）
    """
    # 验证智能体是否存在
    agent = db.query(Agent).filter(Agent.id == chat_request.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 获取或创建对话
    conversation = None
    if chat_request.session_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.session_id,
            Conversation.user_id == int(current_user.id)
        ).first()
    
    if not conversation:
        # 创建新对话
        conversation = Conversation(
            title=f"与{agent.name}的对话",
            user_id=int(current_user.id),
            agent_id=chat_request.agent_id,
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation.id,
        content=chat_request.message,
        role="user",
        message_type="text"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 生成AI回复（模拟）
    ai_response = f"我是{agent.name}，我收到了您的消息：'{chat_request.message}'。这是一个模拟回复。"
    
    # 创建AI消息
    ai_message = Message(
        conversation_id=conversation.id,
        content=ai_response,
        role="assistant",
        message_type="text"
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # 更新对话时间
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "session_id": conversation.id,
        "message_id": ai_message.id,
        "content": ai_response,
        "agent_name": agent.name,
        "timestamp": ai_message.created_at.isoformat()
    }


@router.post("/stream")
async def stream_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式聊天消息
    """
    # 验证智能体是否存在
    agent = db.query(Agent).filter(Agent.id == chat_request.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 获取或创建对话
    conversation = None
    if chat_request.session_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.session_id,
            Conversation.user_id == int(current_user.id)
        ).first()
    
    if not conversation:
        # 创建新对话
        conversation = Conversation(
            title=f"与{agent.name}的对话",
            user_id=int(current_user.id),
            agent_id=chat_request.agent_id,
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation.id,
        content=chat_request.message,
        role="user",
        message_type="text"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    async def generate_stream():
        """生成流式响应"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'session_id': conversation.id})}\n\n"
            
            # 模拟AI回复
            response_text = f"我是{agent.name}，我收到了您的消息：'{chat_request.message}'。让我为您详细回答..."
            
            # 创建AI消息
            ai_message = Message(
                conversation_id=conversation.id,
                content="",
                role="assistant",
                message_type="text"
            )
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            
            # 发送消息ID
            yield f"data: {json.dumps({'type': 'message_id', 'message_id': ai_message.id})}\n\n"
            
            # 逐字符流式输出
            for i, char in enumerate(response_text):
                await asyncio.sleep(0.03)  # 模拟延迟
                ai_message.content += char
                
                yield f"data: {json.dumps({'type': 'content', 'content': char, 'index': i})}\n\n"
            
            # 保存完整消息
            db.commit()
            
            # 更新对话时间
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'message_id': ai_message.id, 'session_id': conversation.id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


@router.get("/sessions")
async def get_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取聊天会话列表
    """
    sessions = db.query(Conversation).filter(
        Conversation.user_id == int(current_user.id)
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for session in sessions:
        # 获取智能体信息
        agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
        
        # 获取最后一条消息
        last_message = db.query(Message).filter(
            Message.conversation_id == session.id
        ).order_by(Message.created_at.desc()).first()
        
        result.append({
            "id": session.id,
            "title": session.title,
            "agent_name": agent.name if agent else "未知智能体",
            "agent_id": session.agent_id,
            "last_message": last_message.content if last_message else "",
            "last_message_time": last_message.created_at.isoformat() if last_message else session.created_at.isoformat(),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        })
    
    return result


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取会话消息列表
    """
    # 验证会话权限
    conversation = db.query(Conversation).filter(
        Conversation.id == session_id,
        Conversation.user_id == int(current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == session_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "message_type": msg.message_type,
            "timestamp": msg.created_at.isoformat()
        }
        for msg in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除聊天会话
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == session_id,
        Conversation.user_id == int(current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 删除会话及其消息（级联删除）
    db.delete(conversation)
    db.commit()
    
    return {"message": "会话删除成功"}
