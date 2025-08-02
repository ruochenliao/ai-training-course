"""
对话管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.agent import Agent
from app.schemas.conversation import (
    ConversationCreate, 
    ConversationResponse, 
    MessageCreate, 
    MessageResponse,
    ConversationUpdate
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


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket

        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)

        logger.info(f"WebSocket连接建立: {connection_id}, 用户: {user_id}")

    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"WebSocket连接断开: {connection_id}, 用户: {user_id}")

    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_personal_message(message, connection_id)


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket实时聊天
    """
    connection_id = f"ws_{conversation_id}_{datetime.utcnow().timestamp()}"

    try:
        # 这里应该验证用户权限，简化处理
        user_id = "temp_user"  # 实际应该从token中获取

        await manager.connect(websocket, connection_id, user_id)

        # 验证对话是否存在
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            await websocket.send_json({
                "type": "error",
                "message": "对话不存在"
            })
            return

        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "conversation_id": conversation_id,
            "message": "WebSocket连接成功"
        })

        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "message":
                content = data.get("content", "")
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "消息内容不能为空"
                    })
                    continue

                # 保存用户消息
                user_message = Message(
                    conversation_id=conversation_id,
                    content=content,
                    role="user",
                    message_type="text"
                )
                db.add(user_message)
                db.commit()
                db.refresh(user_message)

                # 发送用户消息确认
                await websocket.send_json({
                    "type": "user_message",
                    "message_id": user_message.id,
                    "content": content,
                    "timestamp": user_message.created_at.isoformat()
                })

                # 发送正在输入状态
                await websocket.send_json({
                    "type": "typing",
                    "message": "AI正在思考..."
                })

                # 模拟AI回复
                await asyncio.sleep(1)
                ai_response = f"这是对消息'{content}'的AI回复。"

                # 保存AI消息
                ai_message = Message(
                    conversation_id=conversation_id,
                    content=ai_response,
                    role="assistant",
                    message_type="text"
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)

                # 发送AI回复
                await websocket.send_json({
                    "type": "assistant_message",
                    "message_id": ai_message.id,
                    "content": ai_response,
                    "timestamp": ai_message.created_at.isoformat()
                })

                # 更新对话时间
                conversation.updated_at = datetime.utcnow()
                db.commit()

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"服务器错误: {str(e)}"
            })
        except:
            pass
        manager.disconnect(connection_id, user_id)
