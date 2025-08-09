# Copyright (c) 2025 左岚. All rights reserved.
"""
SSE连接管理器

管理SSE连接、消息推送和事件分发。
"""

# # Standard library imports
import asyncio
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

# # Third-party imports
from fastapi import Request
from fastapi.responses import StreamingResponse

# # Local folder imports
from .events import SSEEvent, heartbeat_event

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """连接类型"""
    CHAT = "chat"
    WORKFLOW = "workflow"
    ADMIN = "admin"


class SSEConnection:
    """SSE连接"""
    
    def __init__(self, user_id: str, connection_type: ConnectionType, request: Request):
        self.user_id = user_id
        self.connection_type = connection_type
        self.request = request
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_active = True
    
    async def send_event(self, event: SSEEvent):
        """发送事件"""
        try:
            if self.is_active:
                await self.queue.put(event)
                self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"发送SSE事件失败: {e}")
            self.is_active = False
    
    async def send_error(self, error_message: str, error_code: str = "GENERAL_ERROR"):
        """发送错误事件"""
        # # Local folder imports
        from .events import create_error_event
        error_event = create_error_event(error_message, error_code, self.user_id)
        await self.send_event(error_event)
    
    def subscribe(self, channel: str):
        """订阅频道"""
        self.subscriptions.add(channel)
    
    def unsubscribe(self, channel: str):
        """取消订阅频道"""
        self.subscriptions.discard(channel)
    
    def is_subscribed(self, channel: str) -> bool:
        """检查是否订阅了频道"""
        return channel in self.subscriptions
    
    def disconnect(self):
        """断开连接"""
        self.is_active = False


class SSEManager:
    """SSE连接管理器"""
    
    def __init__(self):
        # 活跃连接 {connection_id: SSEConnection}
        self.active_connections: Dict[str, SSEConnection] = {}
        
        # 用户连接映射 {user_id: [connection_id]}
        self.user_connections: Dict[str, List[str]] = {}
        
        # 频道订阅 {channel: [connection_id]}
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
        # 连接统计
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "events_sent": 0,
            "errors": 0
        }
        
        # 清理任务将在需要时启动
        self._cleanup_task_started = False
    
    def create_connection(self, user_id: str, connection_type: ConnectionType, 
                         request: Request) -> str:
        """创建SSE连接"""
        try:
            # 生成连接ID
            connection_id = f"{user_id}_{connection_type.value}_{datetime.now().timestamp()}"
            
            # 创建连接对象
            connection = SSEConnection(user_id, connection_type, request)
            
            # 存储连接
            self.active_connections[connection_id] = connection
            
            # 更新用户连接映射
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
            # 更新统计
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"SSE连接创建: {connection_id}, 用户: {user_id}")
            
            return connection_id
            
        except Exception as e:
            logger.error(f"SSE连接创建失败: {e}")
            raise
    
    def disconnect(self, connection_id: str):
        """断开SSE连接"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                user_id = connection.user_id
                
                # 断开连接
                connection.disconnect()
                
                # 移除连接
                del self.active_connections[connection_id]
                
                # 更新用户连接映射
                if user_id in self.user_connections:
                    self.user_connections[user_id].remove(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # 移除频道订阅
                for channel, subscribers in self.channel_subscriptions.items():
                    subscribers.discard(connection_id)
                
                # 更新统计
                self.stats["active_connections"] = len(self.active_connections)
                
                logger.info(f"SSE连接断开: {connection_id}")
                
        except Exception as e:
            logger.error(f"SSE断开失败: {e}")
    
    async def send_to_connection(self, connection_id: str, event: SSEEvent) -> bool:
        """发送事件到指定连接"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                await connection.send_event(event)
                self.stats["events_sent"] += 1
                return True
            return False
        except Exception as e:
            logger.error(f"发送事件失败: {e}")
            self.stats["errors"] += 1
            return False
    
    async def send_to_user(self, user_id: str, event: SSEEvent) -> int:
        """发送事件到用户的所有连接"""
        sent_count = 0
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if await self.send_to_connection(connection_id, event):
                    sent_count += 1
        return sent_count
    
    async def broadcast_to_channel(self, channel: str, event: SSEEvent) -> int:
        """广播事件到频道"""
        sent_count = 0
        if channel in self.channel_subscriptions:
            for connection_id in self.channel_subscriptions[channel].copy():
                if await self.send_to_connection(connection_id, event):
                    sent_count += 1
        return sent_count
    
    async def broadcast_to_all(self, event: SSEEvent) -> int:
        """广播事件到所有连接"""
        sent_count = 0
        for connection_id in list(self.active_connections.keys()):
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        return sent_count

    def subscribe_to_channel(self, connection_id: str, channel: str) -> bool:
        """订阅频道"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                connection.subscribe(channel)

                if channel not in self.channel_subscriptions:
                    self.channel_subscriptions[channel] = set()
                self.channel_subscriptions[channel].add(connection_id)

                logger.info(f"连接 {connection_id} 订阅频道 {channel}")
                return True
            return False
        except Exception as e:
            logger.error(f"订阅频道失败: {e}")
            return False

    def unsubscribe_from_channel(self, connection_id: str, channel: str) -> bool:
        """取消订阅频道"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                connection.unsubscribe(channel)

                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(connection_id)

                logger.info(f"连接 {connection_id} 取消订阅频道 {channel}")
                return True
            return False
        except Exception as e:
            logger.error(f"取消订阅频道失败: {e}")
            return False

    def get_connection(self, connection_id: str) -> Optional[SSEConnection]:
        """获取连接"""
        return self.active_connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[SSEConnection]:
        """获取用户的所有连接"""
        connections = []
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    connections.append(self.active_connections[connection_id])
        return connections

    async def create_event_stream(self, connection_id: str) -> AsyncGenerator[str, None]:
        """创建事件流"""
        connection = self.get_connection(connection_id)
        if not connection:
            return

        try:
            # 发送连接建立事件
            connection_event = SSEEvent(
                type="connection_established",
                data={
                    "connection_id": connection_id,
                    "user_id": connection.user_id,
                    "connection_type": connection.connection_type.value
                },
                user_id=connection.user_id
            )
            yield connection_event.to_sse_format()

            # 持续发送事件
            while connection.is_active:
                try:
                    # 等待事件，设置超时以便定期发送心跳
                    event = await asyncio.wait_for(connection.queue.get(), timeout=30.0)
                    yield event.to_sse_format()
                except asyncio.TimeoutError:
                    # 发送心跳
                    heartbeat = heartbeat_event(connection.user_id)
                    yield heartbeat.to_sse_format()
                except Exception as e:
                    logger.error(f"SSE事件流错误: {e}")
                    break

        except Exception as e:
            logger.error(f"SSE事件流异常: {e}")
        finally:
            # 清理连接
            self.disconnect(connection_id)

    async def _cleanup_task(self):
        """清理任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._cleanup_inactive_connections()
            except Exception as e:
                logger.error(f"清理任务异常: {e}")

    async def _cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """清理不活跃的连接"""
        try:
            current_time = datetime.now()
            inactive_connections = []

            for connection_id, connection in self.active_connections.items():
                inactive_time = (current_time - connection.last_activity).total_seconds() / 60
                if inactive_time > timeout_minutes:
                    inactive_connections.append(connection_id)

            for connection_id in inactive_connections:
                self.disconnect(connection_id)

            if inactive_connections:
                logger.info(f"清理了 {len(inactive_connections)} 个不活跃连接")

        except Exception as e:
            logger.error(f"清理不活跃连接失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        return {
            **self.stats,
            "active_connections_by_type": {
                connection_type.value: len([
                    c for c in self.active_connections.values()
                    if c.connection_type == connection_type
                ])
                for connection_type in ConnectionType
            },
            "channels": list(self.channel_subscriptions.keys()),
            "total_channels": len(self.channel_subscriptions)
        }


# 全局SSE管理器
sse_manager = SSEManager()
