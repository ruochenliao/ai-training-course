"""
聊天相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ChatMessageBase(BaseModel):
    """聊天消息基础模型"""
    content: str = Field(..., description="消息内容", example="您好，我想咨询一下产品价格")
    sender: str = Field(..., description="发送者类型", example="user")
    message_type: str = Field("text", description="消息类型", example="text")


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息"""
    conversation_id: Optional[str] = Field(None, description="对话ID")


class ChatMessageResponse(BaseModel):
    """聊天消息响应"""
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="对话ID")
    content: str = Field(..., description="消息内容")
    sender: str = Field(..., description="发送者类型")
    message_type: str = Field(..., description="消息类型")
    timestamp: datetime = Field(..., description="创建时间")
    tokens_used: Optional[int] = Field(0, description="使用的token数量")
    response_time: Optional[int] = Field(0, description="响应时间(毫秒)")


class ChatConversationBase(BaseModel):
    """对话基础模型"""
    title: str = Field("", description="对话标题", example="产品咨询")


class ChatConversationCreate(ChatConversationBase):
    """创建对话"""
    pass


class ChatConversationResponse(BaseModel):
    """对话响应"""
    id: str = Field(..., description="对话ID")
    conversation_id: str = Field(..., description="对话唯一标识")
    user_id: int = Field(..., description="用户ID")
    title: str = Field(..., description="对话标题")
    is_active: bool = Field(..., description="是否活跃")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ChatHistoryResponse(BaseModel):
    """聊天历史响应"""
    conversation: ChatConversationResponse
    messages: List[ChatMessageResponse]


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., description="消息内容", example="您好，我想了解一下产品功能")
    conversation_id: Optional[str] = Field(None, description="对话ID，如果为空则创建新对话")


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    user_message: ChatMessageResponse = Field(..., description="用户消息")
    assistant_message: ChatMessageResponse = Field(..., description="助手回复")
    conversation_id: str = Field(..., description="对话ID")


class StreamMessageChunk(BaseModel):
    """流式消息块"""
    conversation_id: str = Field(..., description="对话ID")
    message_id: str = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容片段")
    is_complete: bool = Field(False, description="是否完成")
    timestamp: datetime = Field(..., description="时间戳")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ChatConversationResponse]
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")


class ChatStatsResponse(BaseModel):
    """聊天统计响应"""
    total_conversations: int = Field(..., description="总对话数")
    total_messages: int = Field(..., description="总消息数")
    total_tokens_used: int = Field(..., description="总token使用量")
    avg_response_time: float = Field(..., description="平均响应时间(毫秒)")


class UpdateConversationRequest(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(None, description="对话标题")
    is_active: Optional[bool] = Field(None, description="是否活跃")


class DeleteConversationRequest(BaseModel):
    """删除对话请求"""
    conversation_id: str = Field(..., description="对话ID")


class ChatConfigResponse(BaseModel):
    """聊天配置响应"""
    model_name: str = Field(..., description="模型名称")
    max_tokens: int = Field(..., description="最大token数")
    temperature: float = Field(0.7, description="温度参数")
    stream_enabled: bool = Field(True, description="是否启用流式输出")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    error_code: str = Field(..., description="错误代码")
    timestamp: datetime = Field(..., description="错误时间")


# 常用的响应状态
class ChatStatus:
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    TIMEOUT = "timeout"


# 消息类型枚举
class MessageType:
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


# 发送者类型枚举
class SenderType:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
