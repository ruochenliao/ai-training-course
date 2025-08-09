# Copyright (c) 2025 左岚. All rights reserved.
"""
SSE事件定义

定义SSE通信中使用的各种事件类型和数据结构。
"""

# # Standard library imports
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """事件类型"""
    CHAT_MESSAGE = "chat_message"
    CHAT_RESPONSE = "chat_response"
    AGENT_THINKING = "agent_thinking"
    AGENT_SELECTED = "agent_selected"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class SSEEvent:
    """SSE事件 - 简化版本"""
    type: str
    data: Dict[str, Any]
    user_id: str = None
    session_id: str = None

    def to_sse_format(self) -> str:
        """转换为SSE格式"""
        event_data = {
            "type": self.type,
            "data": self.data,
            "timestamp": datetime.now().isoformat()
        }
        if self.user_id:
            event_data["user_id"] = self.user_id
        if self.session_id:
            event_data["session_id"] = self.session_id

        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@dataclass
class ChatMessage:
    """聊天消息"""
    message_id: str
    content: str
    sender: str  # user, agent
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatResponse:
    """聊天响应"""
    message_id: str
    response_to: str
    content: str
    agent_type: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowProgress:
    """工作流进度"""
    workflow_id: str
    status: str  # started, running, completed, failed
    current_step: str
    completed_steps: int
    total_steps: int
    progress_percentage: float
    estimated_remaining_time: int = 0  # 秒
    error_message: str = None


@dataclass
class SystemStatus:
    """系统状态"""
    cpu_usage: float
    memory_usage: float
    active_connections: int
    active_sessions: int
    uptime: int


# 简化的事件创建函数
def chat_message_event(message: ChatMessage, user_id: str, session_id: str) -> SSEEvent:
    return SSEEvent("chat_message", asdict(message), user_id, session_id)

def chat_response_event(response: ChatResponse, user_id: str, session_id: str) -> SSEEvent:
    return SSEEvent("chat_response", asdict(response), user_id, session_id)

def agent_thinking_event(agent_type: str, user_id: str, session_id: str) -> SSEEvent:
    return SSEEvent("agent_thinking", {
        "agent_type": agent_type,
        "message": f"{get_agent_name(agent_type)}正在思考中..."
    }, user_id, session_id)

def workflow_progress_event(progress: WorkflowProgress, user_id: str) -> SSEEvent:
    return SSEEvent("workflow_progress", asdict(progress), user_id)

def error_event(message: str, code: str = "ERROR", user_id: str = None, session_id: str = None) -> SSEEvent:
    return SSEEvent("error", {"code": code, "message": message}, user_id, session_id)

def heartbeat_event(user_id: str = None) -> SSEEvent:
    return SSEEvent("heartbeat", {"status": "alive"}, user_id)


def get_agent_name(agent_type: str) -> str:
    """获取智能体名称"""
    names = {
        "customer_service": "客服",
        "text2sql": "数据分析",
        "knowledge_qa": "知识问答",
        "content_creation": "内容创作"
    }
    return names.get(agent_type, "智能")
