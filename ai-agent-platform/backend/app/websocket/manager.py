"""
WebSocket连接管理器

管理WebSocket连接、消息路由和事件分发。
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """连接类型"""
    CHAT = "chat"
    WORKFLOW = "workflow"
    ADMIN = "admin"


class WebSocketConnection:
    """WebSocket连接"""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_type: ConnectionType):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_type = connection_type
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        try:
            await self.websocket.send_text(json.dumps(message, ensure_ascii=False))
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            raise
    
    async def send_error(self, error_message: str, error_code: str = "GENERAL_ERROR"):
        """发送错误消息"""
        await self.send_message({
            "type": "error",
            "error_code": error_code,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def subscribe(self, channel: str):
        """订阅频道"""
        self.subscriptions.add(channel)
    
    def unsubscribe(self, channel: str):
        """取消订阅频道"""
        self.subscriptions.discard(channel)
    
    def is_subscribed(self, channel: str) -> bool:
        """检查是否订阅了频道"""
        return channel in self.subscriptions


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接 {connection_id: WebSocketConnection}
        self.active_connections: Dict[str, WebSocketConnection] = {}
        
        # 用户连接映射 {user_id: [connection_id]}
        self.user_connections: Dict[str, List[str]] = {}
        
        # 频道订阅 {channel: [connection_id]}
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
        # 连接统计
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket, user_id: str, 
                     connection_type: ConnectionType = ConnectionType.CHAT) -> str:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            # 生成连接ID
            connection_id = f"{user_id}_{connection_type.value}_{datetime.now().timestamp()}"
            
            # 创建连接对象
            connection = WebSocketConnection(websocket, user_id, connection_type)
            
            # 存储连接
            self.active_connections[connection_id] = connection
            
            # 更新用户连接映射
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
            # 更新统计
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)
            
            logger.info(f"WebSocket连接建立: {connection_id}, 用户: {user_id}")
            
            # 发送连接成功消息
            await connection.send_message({
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_id,
                "connection_type": connection_type.value,
                "timestamp": datetime.now().isoformat()
            })
            
            return connection_id
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                user_id = connection.user_id
                
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
                
                logger.info(f"WebSocket连接断开: {connection_id}")
                
        except Exception as e:
            logger.error(f"WebSocket断开失败: {e}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """发送消息到指定连接"""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                await connection.send_message(message)
                self.stats["messages_sent"] += 1
                return True
            return False
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.stats["errors"] += 1
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """发送消息到用户的所有连接"""
        sent_count = 0
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> int:
        """广播消息到频道"""
        sent_count = 0
        if channel in self.channel_subscriptions:
            for connection_id in self.channel_subscriptions[channel].copy():
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """广播消息到所有连接"""
        sent_count = 0
        for connection_id in list(self.active_connections.keys()):
            if await self.send_to_connection(connection_id, message):
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
    
    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """获取连接"""
        return self.active_connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """获取用户的所有连接"""
        connections = []
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    connections.append(self.active_connections[connection_id])
        return connections
    
    def get_channel_subscribers(self, channel: str) -> List[WebSocketConnection]:
        """获取频道订阅者"""
        connections = []
        if channel in self.channel_subscriptions:
            for connection_id in self.channel_subscriptions[channel]:
                if connection_id in self.active_connections:
                    connections.append(self.active_connections[connection_id])
        return connections
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """清理不活跃的连接"""
        try:
            current_time = datetime.now()
            inactive_connections = []
            
            for connection_id, connection in self.active_connections.items():
                inactive_time = (current_time - connection.last_activity).total_seconds() / 60
                if inactive_time > timeout_minutes:
                    inactive_connections.append(connection_id)
            
            for connection_id in inactive_connections:
                await self.disconnect(connection_id)
            
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


# 全局连接管理器
connection_manager = ConnectionManager()
