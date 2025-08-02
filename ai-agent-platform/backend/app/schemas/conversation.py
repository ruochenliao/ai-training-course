"""
对话相关的Pydantic模式
"""

from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.chat import MessageRole
from app.models.agent import AgentType
import enum


class FeedbackType(str, enum.Enum):
    """反馈类型枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"


class ConversationBase(BaseModel):
    """
    对话基础模式
    """
    agent_type: AgentType
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """
    创建对话模式
    """
    pass


class ConversationResponse(ConversationBase):
    """
    对话响应模式
    """
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """
    消息基础模式
    """
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class MessageCreate(MessageBase):
    """
    创建消息模式
    """
    conversation_id: int


class MessageResponse(MessageBase):
    """
    消息响应模式
    """
    id: int
    conversation_id: int
    feedback: Optional[FeedbackType] = None
    feedback_comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageFeedback(BaseModel):
    """
    消息反馈模式
    """
    feedback: FeedbackType
    comment: Optional[str] = None


class ConversationList(BaseModel):
    """
    对话列表响应模式
    """
    conversations: List[ConversationResponse]
    total: int
    page: int
    size: int
