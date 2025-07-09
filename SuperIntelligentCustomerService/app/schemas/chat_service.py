"""
聊天服务相关数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    images: Optional[List[str]] = Field(default=None, description="图片URL列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="时间戳")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    images: Optional[List[str]] = Field(default=None, description="图片URL列表")
    stream: bool = Field(default=True, description="是否流式响应")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")
    system_prompt: Optional[str] = Field(default=None, description="自定义系统提示")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="请求元数据")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str = Field(..., description="会话ID")
    message: ChatMessage = Field(..., description="AI回复消息")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="使用统计")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="响应元数据")


class StreamChunk(BaseModel):
    """流式响应块"""
    chunk_id: str = Field(..., description="块ID")
    session_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="内容片段")
    is_final: bool = Field(default=False, description="是否为最后一块")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="块元数据")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    message_count: int = Field(default=0, description="消息数量")
    status: str = Field(default="active", description="会话状态")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="会话元数据")


class SessionStats(BaseModel):
    """会话统计"""
    total_sessions: int = Field(default=0, description="总会话数")
    active_sessions: int = Field(default=0, description="活跃会话数")
    total_messages: int = Field(default=0, description="总消息数")
    average_session_length: float = Field(default=0.0, description="平均会话长度")
    memory_usage: Dict[str, Any] = Field(default_factory=dict, description="记忆使用情况")


class MemoryContext(BaseModel):
    """记忆上下文"""
    chat_history: List[ChatMessage] = Field(default_factory=list, description="聊天历史")
    private_memories: List[str] = Field(default_factory=list, description="私有记忆")
    public_memories: List[str] = Field(default_factory=list, description="公共记忆")
    context_summary: Optional[str] = Field(default=None, description="上下文摘要")


class ChatServiceConfig(BaseModel):
    """聊天服务配置"""
    max_sessions_per_user: int = Field(default=10, description="每用户最大会话数")
    session_timeout_minutes: int = Field(default=60, description="会话超时时间(分钟)")
    max_messages_per_session: int = Field(default=100, description="每会话最大消息数")
    memory_context_limit: int = Field(default=10, description="记忆上下文限制")
    enable_streaming: bool = Field(default=True, description="启用流式响应")
    enable_multimodal: bool = Field(default=True, description="启用多模态")
    default_model: str = Field(default="deepseek-chat", description="默认模型")
    system_prompt: str = Field(
        default="你是超级智能客服，专业、友好、乐于助人。请用中文回复用户的问题。",
        description="默认系统提示"
    )
