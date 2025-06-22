"""
实时通知系统
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

import redis.asyncio as redis
from app.core.config import settings
from fastapi import WebSocket
from loguru import logger

from app.core.exceptions import NotificationException


class NotificationType(Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"
    CHAT_MESSAGE = "chat_message"
    SECURITY_ALERT = "security_alert"
    MAINTENANCE = "maintenance"


class NotificationChannel(Enum):
    """通知渠道"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationTemplate:
    """通知模板"""
    id: str
    name: str
    type: NotificationType
    title_template: str
    content_template: str
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    enabled: bool = True


@dataclass
class Notification:
    """通知消息"""
    id: str
    type: NotificationType
    title: str
    content: str
    recipient_id: Optional[int] = None
    recipient_type: str = "user"  # user, group, all
    channels: List[NotificationChannel] = field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    read: bool = False
    sent: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.channels:
            self.channels = [NotificationChannel.IN_APP]


@dataclass
class WebSocketConnection:
    """WebSocket连接"""
    websocket: WebSocket
    user_id: int
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)


class NotificationService:
    """实时通知服务类"""
    
    def __init__(self):
        """初始化通知服务"""
        self.redis_client = None
        self.websocket_connections: Dict[int, List[WebSocketConnection]] = {}
        self.notification_templates: Dict[str, NotificationTemplate] = {}
        
        # 初始化通知模板
        self._init_notification_templates()
        
        logger.info("实时通知服务初始化完成")
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=4,  # 使用专门的数据库
                decode_responses=True
            )
            
            await self.redis_client.ping()
            logger.info("通知服务Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"通知服务Redis连接初始化失败: {e}")
            raise NotificationException(f"通知服务初始化失败: {e}")
    
    def _init_notification_templates(self):
        """初始化通知模板"""
        templates = [
            NotificationTemplate(
                id="document_processed",
                name="文档处理完成",
                type=NotificationType.DOCUMENT_PROCESSED,
                title_template="文档处理完成",
                content_template="文档 {document_name} 已成功处理完成",
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP],
                priority=NotificationPriority.NORMAL
            ),
            NotificationTemplate(
                id="document_failed",
                name="文档处理失败",
                type=NotificationType.DOCUMENT_FAILED,
                title_template="文档处理失败",
                content_template="文档 {document_name} 处理失败: {error_message}",
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                priority=NotificationPriority.HIGH
            ),
            NotificationTemplate(
                id="security_alert",
                name="安全告警",
                type=NotificationType.SECURITY_ALERT,
                title_template="安全告警",
                content_template="检测到安全威胁: {threat_type} 来源: {source_ip}",
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL],
                priority=NotificationPriority.URGENT
            ),
            NotificationTemplate(
                id="system_maintenance",
                name="系统维护",
                type=NotificationType.MAINTENANCE,
                title_template="系统维护通知",
                content_template="系统将于 {maintenance_time} 进行维护，预计持续 {duration}",
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                priority=NotificationPriority.HIGH
            ),
            NotificationTemplate(
                id="chat_message",
                name="聊天消息",
                type=NotificationType.CHAT_MESSAGE,
                title_template="新消息",
                content_template="您有新的聊天消息",
                channels=[NotificationChannel.WEBSOCKET],
                priority=NotificationPriority.NORMAL
            )
        ]
        
        for template in templates:
            self.notification_templates[template.id] = template
    
    async def send_notification(
        self,
        notification: Notification,
        immediate: bool = True
    ) -> bool:
        """发送通知"""
        try:
            # 保存通知到数据库/Redis
            await self._save_notification(notification)
            
            # 根据渠道发送通知
            success = True
            for channel in notification.channels:
                try:
                    if channel == NotificationChannel.WEBSOCKET:
                        await self._send_websocket_notification(notification)
                    elif channel == NotificationChannel.EMAIL:
                        await self._send_email_notification(notification)
                    elif channel == NotificationChannel.SMS:
                        await self._send_sms_notification(notification)
                    elif channel == NotificationChannel.WEBHOOK:
                        await self._send_webhook_notification(notification)
                    elif channel == NotificationChannel.IN_APP:
                        await self._save_in_app_notification(notification)
                        
                except Exception as e:
                    logger.error(f"通过 {channel.value} 发送通知失败: {e}")
                    success = False
            
            # 更新发送状态
            notification.sent = success
            await self._update_notification_status(notification)
            
            return success
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    async def send_notification_from_template(
        self,
        template_id: str,
        recipient_id: Optional[int] = None,
        recipient_type: str = "user",
        data: Dict[str, Any] = None,
        channels: List[NotificationChannel] = None
    ) -> bool:
        """从模板发送通知"""
        try:
            template = self.notification_templates.get(template_id)
            if not template or not template.enabled:
                logger.warning(f"通知模板 {template_id} 不存在或已禁用")
                return False
            
            if data is None:
                data = {}
            
            # 渲染模板
            title = template.title_template.format(**data)
            content = template.content_template.format(**data)
            
            # 创建通知
            notification = Notification(
                id=str(uuid.uuid4()),
                type=template.type,
                title=title,
                content=content,
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                channels=channels or template.channels,
                priority=template.priority,
                data=data
            )
            
            return await self.send_notification(notification)
            
        except Exception as e:
            logger.error(f"从模板发送通知失败: {e}")
            return False
    
    async def connect_websocket(self, websocket: WebSocket, user_id: int):
        """连接WebSocket"""
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id
            )
            
            if user_id not in self.websocket_connections:
                self.websocket_connections[user_id] = []
            
            self.websocket_connections[user_id].append(connection)
            
            logger.info(f"用户 {user_id} WebSocket连接已建立")
            
            # 发送未读通知
            await self._send_unread_notifications(user_id)
            
            # 保持连接
            await self._handle_websocket_connection(connection)
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
        finally:
            await self.disconnect_websocket(user_id, websocket)
    
    async def disconnect_websocket(self, user_id: int, websocket: WebSocket):
        """断开WebSocket连接"""
        try:
            if user_id in self.websocket_connections:
                self.websocket_connections[user_id] = [
                    conn for conn in self.websocket_connections[user_id]
                    if conn.websocket != websocket
                ]
                
                if not self.websocket_connections[user_id]:
                    del self.websocket_connections[user_id]
            
            logger.info(f"用户 {user_id} WebSocket连接已断开")
            
        except Exception as e:
            logger.error(f"断开WebSocket连接失败: {e}")
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """获取用户通知"""
        try:
            # 从Redis获取通知
            pattern = f"notification:user:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            notifications = []
            for key in keys:
                notification_data = await self.redis_client.hgetall(key)
                if notification_data:
                    notification = self._deserialize_notification(notification_data)
                    if not unread_only or not notification.read:
                        notifications.append(notification)
            
            # 按时间排序
            notifications.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            return notifications[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"获取用户通知失败: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """标记通知为已读"""
        try:
            key = f"notification:user:{user_id}:{notification_id}"
            await self.redis_client.hset(key, "read", "true")
            
            return True
            
        except Exception as e:
            logger.error(f"标记通知已读失败: {e}")
            return False
    
    async def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数量"""
        try:
            pattern = f"notification:user:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            unread_count = 0
            for key in keys:
                read_status = await self.redis_client.hget(key, "read")
                if read_status != "true":
                    unread_count += 1
            
            return unread_count
            
        except Exception as e:
            logger.error(f"获取未读通知数量失败: {e}")
            return 0
    
    async def broadcast_notification(
        self,
        notification: Notification,
        user_ids: List[int] = None
    ) -> bool:
        """广播通知"""
        try:
            if user_ids is None:
                # 广播给所有在线用户
                user_ids = list(self.websocket_connections.keys())
            
            success_count = 0
            for user_id in user_ids:
                notification.recipient_id = user_id
                notification.id = str(uuid.uuid4())  # 为每个用户生成新的ID
                
                if await self.send_notification(notification):
                    success_count += 1
            
            logger.info(f"广播通知完成，成功发送给 {success_count}/{len(user_ids)} 个用户")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"广播通知失败: {e}")
            return False
    
    # 私有方法
    async def _save_notification(self, notification: Notification):
        """保存通知"""
        try:
            if notification.recipient_id:
                key = f"notification:user:{notification.recipient_id}:{notification.id}"
            else:
                key = f"notification:global:{notification.id}"
            
            notification_data = self._serialize_notification(notification)
            await self.redis_client.hset(key, mapping=notification_data)
            
            # 设置过期时间
            if notification.expires_at:
                expire_seconds = int((notification.expires_at - datetime.now()).total_seconds())
                await self.redis_client.expire(key, expire_seconds)
            else:
                # 默认保留30天
                await self.redis_client.expire(key, 86400 * 30)
                
        except Exception as e:
            logger.error(f"保存通知失败: {e}")
    
    async def _send_websocket_notification(self, notification: Notification):
        """发送WebSocket通知"""
        try:
            if notification.recipient_id:
                # 发送给特定用户
                user_connections = self.websocket_connections.get(notification.recipient_id, [])
                for connection in user_connections:
                    try:
                        await connection.websocket.send_text(json.dumps({
                            "type": "notification",
                            "data": self._serialize_notification(notification)
                        }, ensure_ascii=False))
                    except Exception as e:
                        logger.error(f"发送WebSocket消息失败: {e}")
                        # 移除失效连接
                        await self.disconnect_websocket(notification.recipient_id, connection.websocket)
            else:
                # 广播给所有用户
                for user_id, connections in self.websocket_connections.items():
                    for connection in connections:
                        try:
                            await connection.websocket.send_text(json.dumps({
                                "type": "notification",
                                "data": self._serialize_notification(notification)
                            }, ensure_ascii=False))
                        except Exception as e:
                            logger.error(f"广播WebSocket消息失败: {e}")
                            await self.disconnect_websocket(user_id, connection.websocket)
                            
        except Exception as e:
            logger.error(f"发送WebSocket通知失败: {e}")
    
    async def _send_email_notification(self, notification: Notification):
        """发送邮件通知"""
        try:
            # 这里应该集成邮件服务
            logger.info(f"发送邮件通知: {notification.title} -> 用户 {notification.recipient_id}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
    
    async def _send_sms_notification(self, notification: Notification):
        """发送短信通知"""
        try:
            # 这里应该集成短信服务
            logger.info(f"发送短信通知: {notification.title} -> 用户 {notification.recipient_id}")
            
        except Exception as e:
            logger.error(f"发送短信通知失败: {e}")
    
    async def _send_webhook_notification(self, notification: Notification):
        """发送Webhook通知"""
        try:
            # 这里应该发送HTTP请求到配置的Webhook URL
            logger.info(f"发送Webhook通知: {notification.title}")
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
    
    async def _save_in_app_notification(self, notification: Notification):
        """保存应用内通知"""
        try:
            # 应用内通知已经在_save_notification中处理
            pass
            
        except Exception as e:
            logger.error(f"保存应用内通知失败: {e}")
    
    async def _update_notification_status(self, notification: Notification):
        """更新通知状态"""
        try:
            if notification.recipient_id:
                key = f"notification:user:{notification.recipient_id}:{notification.id}"
            else:
                key = f"notification:global:{notification.id}"
            
            await self.redis_client.hset(key, "sent", str(notification.sent).lower())
            
        except Exception as e:
            logger.error(f"更新通知状态失败: {e}")
    
    async def _send_unread_notifications(self, user_id: int):
        """发送未读通知"""
        try:
            unread_notifications = await self.get_user_notifications(user_id, unread_only=True, limit=10)
            
            for notification in unread_notifications:
                await self._send_websocket_notification(notification)
                
        except Exception as e:
            logger.error(f"发送未读通知失败: {e}")
    
    async def _handle_websocket_connection(self, connection: WebSocketConnection):
        """处理WebSocket连接"""
        try:
            while True:
                # 等待消息或心跳
                message = await asyncio.wait_for(
                    connection.websocket.receive_text(),
                    timeout=30.0
                )
                
                # 处理心跳
                if message == "ping":
                    await connection.websocket.send_text("pong")
                    connection.last_ping = datetime.now()
                
        except asyncio.TimeoutError:
            # 连接超时
            logger.info(f"WebSocket连接超时: 用户 {connection.user_id}")
        except Exception as e:
            logger.error(f"WebSocket连接处理失败: {e}")
    
    def _serialize_notification(self, notification: Notification) -> Dict[str, str]:
        """序列化通知"""
        return {
            "id": notification.id,
            "type": notification.type.value,
            "title": notification.title,
            "content": notification.content,
            "recipient_id": str(notification.recipient_id) if notification.recipient_id else "",
            "recipient_type": notification.recipient_type,
            "channels": json.dumps([c.value for c in notification.channels]),
            "priority": notification.priority.value,
            "data": json.dumps(notification.data),
            "created_at": notification.created_at.isoformat(),
            "expires_at": notification.expires_at.isoformat() if notification.expires_at else "",
            "read": str(notification.read).lower(),
            "sent": str(notification.sent).lower()
        }
    
    def _deserialize_notification(self, data: Dict[str, str]) -> Notification:
        """反序列化通知"""
        return Notification(
            id=data["id"],
            type=NotificationType(data["type"]),
            title=data["title"],
            content=data["content"],
            recipient_id=int(data["recipient_id"]) if data["recipient_id"] else None,
            recipient_type=data["recipient_type"],
            channels=[NotificationChannel(c) for c in json.loads(data["channels"])],
            priority=NotificationPriority(data["priority"]),
            data=json.loads(data["data"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            read=data["read"].lower() == "true",
            sent=data["sent"].lower() == "true"
        )


# 全局通知服务实例
notification_service = NotificationService()
