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
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """
    创建对话模式
    """
    agent_id: int


class ConversationUpdate(BaseModel):
    """
    更新对话模式
    """
    title: Optional[str] = None
    status: Optional[str] = None


class ConversationResponse(ConversationBase):
    """
    对话响应模式
    """
    id: int
    user_id: str
    agent_id: Optional[int] = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """
    消息基础模式
    """
    content: str
    message_type: Optional[str] = "text"


class MessageCreate(MessageBase):
    """
    创建消息模式
    """
    pass


class MessageResponse(MessageBase):
    """
    消息响应模式
    """
    id: int
    conversation_id: int
    role: str
    tokens: Optional[int] = None
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
