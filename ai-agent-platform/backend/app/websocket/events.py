"""
WebSocket事件定义

定义WebSocket通信中使用的事件类型和数据结构。
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class EventType(Enum):
    """事件类型"""
    # 连接事件
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CLOSED = "connection_closed"
    
    # 聊天事件
    CHAT_MESSAGE = "chat_message"
    CHAT_RESPONSE = "chat_response"
    CHAT_TYPING = "chat_typing"
    CHAT_HISTORY = "chat_history"
    
    # 智能体事件
    AGENT_SELECTED = "agent_selected"
    AGENT_STATUS = "agent_status"
    AGENT_THINKING = "agent_thinking"
    
    # 工作流事件
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    
    # 知识库事件
    KNOWLEDGE_UPLOAD = "knowledge_upload"
    KNOWLEDGE_SEARCH = "knowledge_search"
    
    # 系统事件
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class WebSocketEvent(BaseModel):
    """WebSocket事件"""
    type: EventType
    data: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id
        }


class ChatMessage(BaseModel):
    """聊天消息"""
    message_id: str
    content: str
    sender: str  # user 或 agent
    agent_type: Optional[str] = None
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """聊天响应"""
    message_id: str
    response_to: str  # 回复的消息ID
    content: str
    agent_type: str
    confidence: float = 0.0
    sources: list = []
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class AgentStatus(BaseModel):
    """智能体状态"""
    agent_name: str
    status: str  # idle, thinking, responding, error
    current_task: Optional[str] = None
    progress: float = 0.0
    timestamp: datetime = datetime.now()


class WorkflowProgress(BaseModel):
    """工作流进度"""
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    completed_steps: int = 0
    total_steps: int = 0
    progress_percentage: float = 0.0
    estimated_remaining_time: Optional[int] = None
    timestamp: datetime = datetime.now()


class KnowledgeUpload(BaseModel):
    """知识库上传"""
    upload_id: str
    filename: str
    status: str  # uploading, processing, completed, failed
    progress: float = 0.0
    processed_chunks: int = 0
    total_chunks: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()


class SystemNotification(BaseModel):
    """系统通知"""
    notification_id: str
    title: str
    message: str
    level: str  # info, warning, error, success
    action_url: Optional[str] = None
    timestamp: datetime = datetime.now()


# 事件工厂函数
def create_chat_message_event(message: ChatMessage, user_id: str, session_id: str = None) -> WebSocketEvent:
    """创建聊天消息事件"""
    return WebSocketEvent(
        type=EventType.CHAT_MESSAGE,
        data=message.dict(),
        user_id=user_id,
        session_id=session_id
    )


def create_chat_response_event(response: ChatResponse, user_id: str, session_id: str = None) -> WebSocketEvent:
    """创建聊天响应事件"""
    return WebSocketEvent(
        type=EventType.CHAT_RESPONSE,
        data=response.dict(),
        user_id=user_id,
        session_id=session_id
    )


def create_agent_status_event(status: AgentStatus, user_id: str) -> WebSocketEvent:
    """创建智能体状态事件"""
    return WebSocketEvent(
        type=EventType.AGENT_STATUS,
        data=status.dict(),
        user_id=user_id
    )


def create_workflow_progress_event(progress: WorkflowProgress, user_id: str) -> WebSocketEvent:
    """创建工作流进度事件"""
    return WebSocketEvent(
        type=EventType.WORKFLOW_PROGRESS,
        data=progress.dict(),
        user_id=user_id
    )


def create_knowledge_upload_event(upload: KnowledgeUpload, user_id: str) -> WebSocketEvent:
    """创建知识库上传事件"""
    return WebSocketEvent(
        type=EventType.KNOWLEDGE_UPLOAD,
        data=upload.dict(),
        user_id=user_id
    )


def create_system_notification_event(notification: SystemNotification, user_id: str = None) -> WebSocketEvent:
    """创建系统通知事件"""
    return WebSocketEvent(
        type=EventType.SYSTEM_NOTIFICATION,
        data=notification.dict(),
        user_id=user_id
    )


def create_error_event(error_message: str, error_code: str = "GENERAL_ERROR", 
                      user_id: str = None) -> WebSocketEvent:
    """创建错误事件"""
    return WebSocketEvent(
        type=EventType.ERROR,
        data={
            "error_code": error_code,
            "message": error_message
        },
        user_id=user_id
    )


def create_heartbeat_event() -> WebSocketEvent:
    """创建心跳事件"""
    return WebSocketEvent(
        type=EventType.HEARTBEAT,
        data={"timestamp": datetime.now().isoformat()}
    )
