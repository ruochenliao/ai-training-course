"""
# Copyright (c) 2025 左岚. All rights reserved.

聊天相关的Pydantic模型
"""

# # Standard library imports
from datetime import datetime
from typing import Any, Dict, Optional

# # Third-party imports
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求"""
    agent_id: int = Field(..., description="智能体ID")
    message: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    session_id: Optional[int] = Field(None, description="会话ID，如果为空则创建新会话")
    message_type: Optional[str] = Field("text", description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: int = Field(..., description="会话ID")
    message_id: int = Field(..., description="消息ID")
    content: str = Field(..., description="回复内容")
    agent_name: str = Field(..., description="智能体名称")
    timestamp: str = Field(..., description="时间戳")


class StreamChatEvent(BaseModel):
    """流式聊天事件"""
    type: str = Field(..., description="事件类型: start, content, done, error")
    session_id: Optional[int] = Field(None, description="会话ID")
    message_id: Optional[int] = Field(None, description="消息ID")
    content: Optional[str] = Field(None, description="内容片段")
    index: Optional[int] = Field(None, description="内容索引")
    error: Optional[str] = Field(None, description="错误信息")


class SessionInfo(BaseModel):
    """会话信息"""
    id: int = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    agent_name: str = Field(..., description="智能体名称")
    agent_id: int = Field(..., description="智能体ID")
    last_message: str = Field(..., description="最后一条消息")
    last_message_time: str = Field(..., description="最后消息时间")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class MessageInfo(BaseModel):
    """消息信息"""
    id: int = Field(..., description="消息ID")
    role: str = Field(..., description="角色: user, assistant, system")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型")
    timestamp: str = Field(..., description="时间戳")


# WebSocket消息模式已移除
# 实时通信功能已迁移到SSE，使用标准的消息模式
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
