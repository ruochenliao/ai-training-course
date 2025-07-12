"""
聊天服务相关数据模型
标准化的请求和响应模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


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


class ChatServiceMessage(BaseModel):
    """聊天服务消息模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    images: Optional[List[str]] = Field(default=None, description="图片URL列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ChatServiceRequest(BaseModel):
    """聊天服务请求模型"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, description="会话ID")
    model: Optional[str] = Field(None, description="指定模型名称")
    stream: bool = Field(default=True, description="是否流式响应")
    system_prompt: Optional[str] = Field(None, description="自定义系统提示")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="请求元数据")


class MultimodalChatRequest(BaseModel):
    """多模态聊天请求模型"""
    message: str = Field(..., description="文本消息", min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, description="会话ID")
    model: Optional[str] = Field(None, description="指定模型名称")
    # files 将通过 Form 参数传递，不在这里定义


class SessionCreate(BaseModel):
    """创建会话请求"""
    session_title: str = Field(default="新对话", description="会话标题", max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="会话元数据")


class SessionUpdate(BaseModel):
    """更新会话请求"""
    id: int = Field(..., description="会话ID")
    session_title: Optional[str] = Field(None, description="会话标题", max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="会话元数据")


class SessionValidateRequest(BaseModel):
    """会话验证请求"""
    session_id: Optional[str] = Field(None, description="会话ID")


class SessionInfo(BaseModel):
    """会话信息响应"""
    session_id: str = Field(..., description="会话ID")
    session_title: str = Field(..., description="会话标题")
    user_id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    message_count: int = Field(default=0, description="消息数量")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="会话元数据")


class SessionListResponse(BaseModel):
    """会话列表响应"""
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    updated_at: datetime = Field(..., description="更新时间")


class ChatModelInfo(BaseModel):
    """聊天模型信息"""
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    description: Optional[str] = Field(None, description="模型描述")
    price: Optional[float] = Field(None, description="模型价格")
    model_type: Optional[str] = Field(None, description="模型类型")


class ServiceStats(BaseModel):
    """服务统计信息"""
    total_sessions: int = Field(default=0, description="总会话数")
    total_messages: int = Field(default=0, description="总消息数")
    agent_system: str = Field(default="smart-chat-system", description="智能体系统")
    agents: List[str] = Field(default_factory=list, description="智能体列表")
    features: List[str] = Field(default_factory=list, description="功能特性")


class HealthStatus(BaseModel):
    """健康状态"""
    status: str = Field(..., description="服务状态")
    agent_system: str = Field(..., description="智能体系统")
    agents_status: Dict[str, bool] = Field(..., description="智能体状态")
    features: List[str] = Field(..., description="功能特性")
    service_uptime: str = Field(..., description="服务运行时间")


class ChatServiceError(BaseModel):
    """聊天服务错误"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")


# 常用的响应状态
class ChatServiceStatus:
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    TIMEOUT = "timeout"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"


# 智能体类型枚举
class AgentType(str, Enum):
    TEXT_AGENT = "text_agent"
    VISION_AGENT = "vision_agent"
    MULTIMODAL_AGENT = "multimodal_agent"


class ChatServiceConfig(BaseModel):
    """聊天服务配置"""
    max_sessions_per_user: int = Field(default=10, description="每用户最大会话数")
    session_timeout_minutes: int = Field(default=60, description="会话超时时间(分钟)")
    max_messages_per_session: int = Field(default=100, description="每会话最大消息数")
    memory_context_limit: int = Field(default=10, description="记忆上下文限制")
    enable_streaming: bool = Field(default=True, description="启用流式响应")
    enable_multimodal: bool = Field(default=True, description="启用多模态")
    default_model: str = Field(default="qwen-plus-latest", description="默认模型")
    system_prompt: str = Field(
        default="你是超级智能客服，专业、友好、乐于助人。请用中文回复用户的问题。",
        description="默认系统提示"
    )
