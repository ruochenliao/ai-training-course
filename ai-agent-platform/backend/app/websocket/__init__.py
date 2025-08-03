"""
WebSocket模块

提供实时通信功能，支持智能体对话、工作流状态更新等。
"""

from .manager import ConnectionManager
from .handlers import ChatHandler, WorkflowHandler
from .events import WebSocketEvent, EventType

__all__ = [
    "ConnectionManager",
    "ChatHandler", 
    "WorkflowHandler",
    "WebSocketEvent",
    "EventType"
]
