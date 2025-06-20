"""
实时协作服务
提供多用户实时聊天、协作编辑、状态同步等功能
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from fastapi import WebSocket
import redis.asyncio as redis

from ..core.cache_manager import cache_manager
from ..settings.config import settings

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    CHAT = "chat"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"
    CURSOR_MOVE = "cursor_move"
    DOCUMENT_EDIT = "document_edit"
    VOICE_START = "voice_start"
    VOICE_END = "voice_end"
    SYSTEM = "system"
    HEARTBEAT = "heartbeat"


class UserStatus(Enum):
    """用户状态"""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class CollaborationUser:
    """协作用户"""
    user_id: str
    username: str
    avatar: Optional[str] = None
    status: UserStatus = UserStatus.ONLINE
    last_seen: datetime = None
    cursor_position: Optional[Dict[str, Any]] = None
    is_typing: bool = False
    websocket: Optional[WebSocket] = None
    
    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()


@dataclass
class CollaborationMessage:
    """协作消息"""
    message_id: str
    message_type: MessageType
    sender_id: str
    room_id: str
    content: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "room_id": self.room_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class CollaborationRoom:
    """协作房间"""
    room_id: str
    name: str
    description: Optional[str] = None
    created_by: str = None
    created_at: datetime = None
    max_users: int = 50
    is_private: bool = False
    users: Dict[str, CollaborationUser] = None
    message_history: List[CollaborationMessage] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.users is None:
            self.users = {}
        if self.message_history is None:
            self.message_history = []


class CollaborationService:
    """实时协作服务"""
    
    def __init__(self):
        self.rooms: Dict[str, CollaborationRoom] = {}
        self.user_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, Set[str]] = {}  # 用户所在房间
        self.room_subscribers: Dict[str, Set[str]] = {}  # 房间订阅者
        
        # Redis连接（用于分布式部署）
        self.redis_client = None
        self._init_redis()
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.CHAT: self._handle_chat_message,
            MessageType.USER_JOIN: self._handle_user_join,
            MessageType.USER_LEAVE: self._handle_user_leave,
            MessageType.TYPING: self._handle_typing,
            MessageType.STOP_TYPING: self._handle_stop_typing,
            MessageType.CURSOR_MOVE: self._handle_cursor_move,
            MessageType.DOCUMENT_EDIT: self._handle_document_edit,
            MessageType.VOICE_START: self._handle_voice_start,
            MessageType.VOICE_END: self._handle_voice_end,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_task())
        
        logger.info("实时协作服务初始化完成")
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                logger.info("Redis连接初始化成功")
        except Exception as e:
            logger.warning(f"Redis连接初始化失败: {str(e)}")
    
    async def create_room(
        self,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        is_private: bool = False,
        max_users: int = 50
    ) -> str:
        """
        创建协作房间
        
        Args:
            name: 房间名称
            created_by: 创建者ID
            description: 房间描述
            is_private: 是否私有
            max_users: 最大用户数
            
        Returns:
            房间ID
        """
        try:
            room_id = str(uuid.uuid4())
            
            room = CollaborationRoom(
                room_id=room_id,
                name=name,
                description=description,
                created_by=created_by,
                is_private=is_private,
                max_users=max_users
            )
            
            self.rooms[room_id] = room
            self.room_subscribers[room_id] = set()
            
            # 持久化到Redis
            if self.redis_client:
                await self.redis_client.hset(
                    "collaboration_rooms",
                    room_id,
                    json.dumps(asdict(room), default=str)
                )
            
            logger.info(f"创建协作房间: {room_id} - {name}")
            return room_id
            
        except Exception as e:
            logger.error(f"创建房间失败: {str(e)}")
            raise
    
    async def join_room(
        self,
        room_id: str,
        user_id: str,
        username: str,
        websocket: WebSocket,
        avatar: Optional[str] = None
    ) -> bool:
        """
        加入协作房间
        
        Args:
            room_id: 房间ID
            user_id: 用户ID
            username: 用户名
            websocket: WebSocket连接
            avatar: 用户头像
            
        Returns:
            是否成功加入
        """
        try:
            if room_id not in self.rooms:
                logger.warning(f"房间不存在: {room_id}")
                return False
            
            room = self.rooms[room_id]
            
            # 检查房间容量
            if len(room.users) >= room.max_users:
                logger.warning(f"房间已满: {room_id}")
                return False
            
            # 创建用户对象
            user = CollaborationUser(
                user_id=user_id,
                username=username,
                avatar=avatar,
                websocket=websocket
            )
            
            # 添加到房间
            room.users[user_id] = user
            self.user_connections[user_id] = websocket
            
            # 更新用户房间映射
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(room_id)
            
            # 添加到房间订阅者
            self.room_subscribers[room_id].add(user_id)
            
            # 发送用户加入消息
            join_message = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.USER_JOIN,
                sender_id=user_id,
                room_id=room_id,
                content={
                    "user": {
                        "user_id": user_id,
                        "username": username,
                        "avatar": avatar
                    }
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_to_room(room_id, join_message, exclude_user=user_id)
            
            # 发送房间状态给新用户
            await self._send_room_status(room_id, user_id)
            
            logger.info(f"用户 {user_id} 加入房间 {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"加入房间失败: {str(e)}")
            return False
    
    async def leave_room(self, room_id: str, user_id: str) -> bool:
        """
        离开协作房间
        
        Args:
            room_id: 房间ID
            user_id: 用户ID
            
        Returns:
            是否成功离开
        """
        try:
            if room_id not in self.rooms:
                return False
            
            room = self.rooms[room_id]
            
            if user_id not in room.users:
                return False
            
            # 获取用户信息
            user = room.users[user_id]
            
            # 从房间移除用户
            del room.users[user_id]
            
            # 清理连接映射
            if user_id in self.user_connections:
                del self.user_connections[user_id]
            
            # 更新用户房间映射
            if user_id in self.user_rooms:
                self.user_rooms[user_id].discard(room_id)
                if not self.user_rooms[user_id]:
                    del self.user_rooms[user_id]
            
            # 从房间订阅者移除
            self.room_subscribers[room_id].discard(user_id)
            
            # 发送用户离开消息
            leave_message = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.USER_LEAVE,
                sender_id=user_id,
                room_id=room_id,
                content={
                    "user": {
                        "user_id": user_id,
                        "username": user.username
                    }
                },
                timestamp=datetime.now()
            )
            
            await self._broadcast_to_room(room_id, leave_message)
            
            # 如果房间为空，考虑删除房间
            if not room.users and not room.is_private:
                await self._cleanup_empty_room(room_id)
            
            logger.info(f"用户 {user_id} 离开房间 {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"离开房间失败: {str(e)}")
            return False
    
    async def send_message(
        self,
        room_id: str,
        user_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送消息到房间
        
        Args:
            room_id: 房间ID
            user_id: 发送者ID
            message_type: 消息类型
            content: 消息内容
            metadata: 元数据
            
        Returns:
            是否发送成功
        """
        try:
            if room_id not in self.rooms:
                return False
            
            if user_id not in self.rooms[room_id].users:
                return False
            
            # 创建消息
            message = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                message_type=message_type,
                sender_id=user_id,
                room_id=room_id,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            # 添加到历史记录
            self.rooms[room_id].message_history.append(message)
            
            # 限制历史记录长度
            if len(self.rooms[room_id].message_history) > 1000:
                self.rooms[room_id].message_history = self.rooms[room_id].message_history[-500:]
            
            # 处理特定类型的消息
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](message)
            
            # 广播消息
            await self._broadcast_to_room(room_id, message, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    async def _broadcast_to_room(
        self,
        room_id: str,
        message: CollaborationMessage,
        exclude_user: Optional[str] = None
    ):
        """广播消息到房间所有用户"""
        try:
            if room_id not in self.rooms:
                return
            
            room = self.rooms[room_id]
            message_data = message.to_dict()
            
            # 发送给房间内所有用户
            for user_id, user in room.users.items():
                if exclude_user and user_id == exclude_user:
                    continue
                
                if user.websocket:
                    try:
                        await user.websocket.send_text(json.dumps(message_data))
                    except Exception as e:
                        logger.warning(f"发送消息到用户 {user_id} 失败: {str(e)}")
                        # 标记连接为断开
                        await self._handle_disconnection(user_id)
            
        except Exception as e:
            logger.error(f"广播消息失败: {str(e)}")
    
    async def _send_room_status(self, room_id: str, user_id: str):
        """发送房间状态给指定用户"""
        try:
            if room_id not in self.rooms:
                return
            
            room = self.rooms[room_id]
            user = room.users.get(user_id)
            
            if not user or not user.websocket:
                return
            
            # 构建房间状态
            room_status = {
                "room_id": room_id,
                "name": room.name,
                "description": room.description,
                "users": [
                    {
                        "user_id": u.user_id,
                        "username": u.username,
                        "avatar": u.avatar,
                        "status": u.status.value,
                        "is_typing": u.is_typing,
                        "last_seen": u.last_seen.isoformat()
                    }
                    for u in room.users.values()
                ],
                "message_history": [
                    msg.to_dict() for msg in room.message_history[-50:]  # 最近50条消息
                ]
            }
            
            status_message = {
                "message_type": "room_status",
                "content": room_status,
                "timestamp": datetime.now().isoformat()
            }
            
            await user.websocket.send_text(json.dumps(status_message))
            
        except Exception as e:
            logger.error(f"发送房间状态失败: {str(e)}")
    
    async def _handle_chat_message(self, message: CollaborationMessage):
        """处理聊天消息"""
        # 这里可以添加消息过滤、敏感词检测等逻辑
        pass
    
    async def _handle_user_join(self, message: CollaborationMessage):
        """处理用户加入"""
        pass
    
    async def _handle_user_leave(self, message: CollaborationMessage):
        """处理用户离开"""
        pass
    
    async def _handle_typing(self, message: CollaborationMessage):
        """处理打字状态"""
        room_id = message.room_id
        user_id = message.sender_id
        
        if room_id in self.rooms and user_id in self.rooms[room_id].users:
            self.rooms[room_id].users[user_id].is_typing = True
    
    async def _handle_stop_typing(self, message: CollaborationMessage):
        """处理停止打字"""
        room_id = message.room_id
        user_id = message.sender_id
        
        if room_id in self.rooms and user_id in self.rooms[room_id].users:
            self.rooms[room_id].users[user_id].is_typing = False
    
    async def _handle_cursor_move(self, message: CollaborationMessage):
        """处理光标移动"""
        room_id = message.room_id
        user_id = message.sender_id
        
        if room_id in self.rooms and user_id in self.rooms[room_id].users:
            self.rooms[room_id].users[user_id].cursor_position = message.content.get("position")
    
    async def _handle_document_edit(self, message: CollaborationMessage):
        """处理文档编辑"""
        # 这里可以实现协作编辑的冲突解决逻辑
        pass
    
    async def _handle_voice_start(self, message: CollaborationMessage):
        """处理语音开始"""
        pass
    
    async def _handle_voice_end(self, message: CollaborationMessage):
        """处理语音结束"""
        pass
    
    async def _handle_heartbeat(self, message: CollaborationMessage):
        """处理心跳"""
        room_id = message.room_id
        user_id = message.sender_id
        
        if room_id in self.rooms and user_id in self.rooms[room_id].users:
            self.rooms[room_id].users[user_id].last_seen = datetime.now()
    
    async def _handle_disconnection(self, user_id: str):
        """处理用户断开连接"""
        try:
            if user_id in self.user_rooms:
                # 从所有房间移除用户
                rooms_to_leave = list(self.user_rooms[user_id])
                for room_id in rooms_to_leave:
                    await self.leave_room(room_id, user_id)
            
        except Exception as e:
            logger.error(f"处理断开连接失败: {str(e)}")
    
    async def _cleanup_empty_room(self, room_id: str):
        """清理空房间"""
        try:
            if room_id in self.rooms:
                del self.rooms[room_id]
            
            if room_id in self.room_subscribers:
                del self.room_subscribers[room_id]
            
            # 从Redis删除
            if self.redis_client:
                await self.redis_client.hdel("collaboration_rooms", room_id)
            
            logger.info(f"清理空房间: {room_id}")
            
        except Exception as e:
            logger.error(f"清理房间失败: {str(e)}")
    
    async def _cleanup_task(self):
        """定期清理任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 5分钟执行一次
                
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(minutes=10)
                
                # 清理超时用户
                users_to_remove = []
                for room_id, room in self.rooms.items():
                    for user_id, user in room.users.items():
                        if user.last_seen < timeout_threshold:
                            users_to_remove.append((room_id, user_id))
                
                for room_id, user_id in users_to_remove:
                    await self.leave_room(room_id, user_id)
                
                if users_to_remove:
                    logger.info(f"清理超时用户: {len(users_to_remove)}")
                
            except Exception as e:
                logger.error(f"清理任务失败: {str(e)}")
    
    async def get_room_list(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取房间列表"""
        try:
            room_list = []
            
            for room_id, room in self.rooms.items():
                # 如果是私有房间，只有成员才能看到
                if room.is_private and (not user_id or user_id not in room.users):
                    continue
                
                room_info = {
                    "room_id": room_id,
                    "name": room.name,
                    "description": room.description,
                    "user_count": len(room.users),
                    "max_users": room.max_users,
                    "is_private": room.is_private,
                    "created_at": room.created_at.isoformat()
                }
                
                room_list.append(room_info)
            
            return room_list
            
        except Exception as e:
            logger.error(f"获取房间列表失败: {str(e)}")
            return []
    
    async def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间信息"""
        try:
            if room_id not in self.rooms:
                return None
            
            room = self.rooms[room_id]
            
            return {
                "room_id": room_id,
                "name": room.name,
                "description": room.description,
                "created_by": room.created_by,
                "created_at": room.created_at.isoformat(),
                "user_count": len(room.users),
                "max_users": room.max_users,
                "is_private": room.is_private,
                "users": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "avatar": user.avatar,
                        "status": user.status.value,
                        "is_typing": user.is_typing,
                        "last_seen": user.last_seen.isoformat()
                    }
                    for user in room.users.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"获取房间信息失败: {str(e)}")
            return None


# 全局协作服务实例
collaboration_service = CollaborationService()
