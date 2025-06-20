"""
实时协作API
提供多用户实时聊天、协作编辑、状态同步等接口
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
import json

from ...services.collaboration_service import (
    collaboration_service, 
    MessageType, 
    UserStatus,
    CollaborationMessage
)
from ...services.analytics_service import analytics_service, EventType
from ...core.dependency import DependPermission

logger = logging.getLogger(__name__)

collaboration_router = APIRouter()


class CreateRoomRequest(BaseModel):
    """创建房间请求"""
    name: str = Field(..., description="房间名称")
    description: Optional[str] = Field(None, description="房间描述")
    is_private: bool = Field(False, description="是否私有")
    max_users: int = Field(50, description="最大用户数", ge=2, le=100)
    created_by: str = Field(..., description="创建者ID")


class JoinRoomRequest(BaseModel):
    """加入房间请求"""
    room_id: str = Field(..., description="房间ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    avatar: Optional[str] = Field(None, description="用户头像")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    room_id: str = Field(..., description="房间ID")
    user_id: str = Field(..., description="发送者ID")
    message_type: str = Field(..., description="消息类型")
    content: Dict[str, Any] = Field(..., description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


@collaboration_router.post("/rooms", summary="创建协作房间")
async def create_room(request: CreateRoomRequest):
    """
    创建协作房间
    
    创建一个新的实时协作房间
    """
    try:
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.FEATURE_USED,
            user_id=request.created_by,
            properties={
                "feature_name": "create_collaboration_room",
                "room_name": request.name,
                "is_private": request.is_private,
                "max_users": request.max_users
            }
        )
        
        # 创建房间
        room_id = await collaboration_service.create_room(
            name=request.name,
            created_by=request.created_by,
            description=request.description,
            is_private=request.is_private,
            max_users=request.max_users
        )
        
        return {
            "success": True,
            "room_id": room_id,
            "message": "房间创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建房间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.get("/rooms", summary="获取房间列表")
async def get_room_list(user_id: Optional[str] = Query(None)):
    """
    获取房间列表
    
    返回可用的协作房间列表
    """
    try:
        rooms = await collaboration_service.get_room_list(user_id=user_id)
        
        return {
            "success": True,
            "rooms": rooms,
            "count": len(rooms)
        }
        
    except Exception as e:
        logger.error(f"获取房间列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.get("/rooms/{room_id}", summary="获取房间信息")
async def get_room_info(room_id: str):
    """
    获取房间详细信息
    
    返回指定房间的详细信息
    """
    try:
        room_info = await collaboration_service.get_room_info(room_id)
        
        if room_info:
            return {
                "success": True,
                "room": room_info
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="房间不存在"
            )
        
    except Exception as e:
        logger.error(f"获取房间信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.post("/rooms/{room_id}/join", summary="加入房间")
async def join_room_api(room_id: str, request: JoinRoomRequest):
    """
    加入协作房间
    
    用户加入指定的协作房间
    """
    try:
        # 注意：这里只是API接口，实际的WebSocket连接在WebSocket端点处理
        # 这个接口主要用于验证和预处理
        
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.FEATURE_USED,
            user_id=request.user_id,
            properties={
                "feature_name": "join_collaboration_room",
                "room_id": room_id
            }
        )
        
        return {
            "success": True,
            "message": "请通过WebSocket连接加入房间",
            "websocket_url": f"/api/v1/collaboration/rooms/{room_id}/ws"
        }
        
    except Exception as e:
        logger.error(f"加入房间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.post("/rooms/{room_id}/leave", summary="离开房间")
async def leave_room_api(room_id: str, user_id: str):
    """
    离开协作房间
    
    用户离开指定的协作房间
    """
    try:
        success = await collaboration_service.leave_room(room_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": "已离开房间"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="离开房间失败"
            )
        
    except Exception as e:
        logger.error(f"离开房间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.post("/rooms/{room_id}/messages", summary="发送消息")
async def send_message_api(room_id: str, request: SendMessageRequest):
    """
    发送消息到房间
    
    向指定房间发送消息
    """
    try:
        # 验证消息类型
        try:
            message_type = MessageType(request.message_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的消息类型: {request.message_type}"
            )
        
        # 发送消息
        success = await collaboration_service.send_message(
            room_id=room_id,
            user_id=request.user_id,
            message_type=message_type,
            content=request.content,
            metadata=request.metadata
        )
        
        if success:
            return {
                "success": True,
                "message": "消息发送成功"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="消息发送失败"
            )
        
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.websocket("/rooms/{room_id}/ws")
async def collaboration_websocket(
    websocket: WebSocket,
    room_id: str,
    user_id: str = Query(...),
    username: str = Query(...),
    avatar: Optional[str] = Query(None)
):
    """
    协作房间WebSocket连接
    
    建立实时协作连接
    """
    await websocket.accept()
    
    try:
        logger.info(f"用户 {user_id} 尝试连接到房间 {room_id}")
        
        # 加入房间
        success = await collaboration_service.join_room(
            room_id=room_id,
            user_id=user_id,
            username=username,
            websocket=websocket,
            avatar=avatar
        )
        
        if not success:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "加入房间失败"
            }))
            await websocket.close()
            return
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "已成功连接到协作房间",
            "room_id": room_id,
            "user_id": user_id
        }))
        
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.FEATURE_USED,
            user_id=user_id,
            properties={
                "feature_name": "collaboration_websocket_connected",
                "room_id": room_id
            }
        )
        
        # 处理消息循环
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type_str = message_data.get("type")
                content = message_data.get("content", {})
                metadata = message_data.get("metadata")
                
                # 验证消息类型
                try:
                    message_type = MessageType(message_type_str)
                except ValueError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"无效的消息类型: {message_type_str}"
                    }))
                    continue
                
                # 发送消息到房间
                await collaboration_service.send_message(
                    room_id=room_id,
                    user_id=user_id,
                    message_type=message_type,
                    content=content,
                    metadata=metadata
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "无效的JSON格式"
                }))
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} 断开连接")
    except Exception as e:
        logger.error(f"协作WebSocket错误: {str(e)}")
    finally:
        # 离开房间
        await collaboration_service.leave_room(room_id, user_id)
        
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.FEATURE_USED,
            user_id=user_id,
            properties={
                "feature_name": "collaboration_websocket_disconnected",
                "room_id": room_id
            }
        )


@collaboration_router.get("/message-types", summary="获取消息类型")
async def get_message_types():
    """
    获取支持的消息类型
    
    返回系统支持的所有消息类型
    """
    try:
        message_types = [
            {
                "type": MessageType.CHAT.value,
                "name": "聊天消息",
                "description": "普通的文本聊天消息"
            },
            {
                "type": MessageType.USER_JOIN.value,
                "name": "用户加入",
                "description": "用户加入房间的系统消息"
            },
            {
                "type": MessageType.USER_LEAVE.value,
                "name": "用户离开",
                "description": "用户离开房间的系统消息"
            },
            {
                "type": MessageType.TYPING.value,
                "name": "正在输入",
                "description": "用户正在输入的状态消息"
            },
            {
                "type": MessageType.STOP_TYPING.value,
                "name": "停止输入",
                "description": "用户停止输入的状态消息"
            },
            {
                "type": MessageType.CURSOR_MOVE.value,
                "name": "光标移动",
                "description": "协作编辑中的光标位置"
            },
            {
                "type": MessageType.DOCUMENT_EDIT.value,
                "name": "文档编辑",
                "description": "协作编辑的文档变更"
            },
            {
                "type": MessageType.VOICE_START.value,
                "name": "语音开始",
                "description": "开始语音通话"
            },
            {
                "type": MessageType.VOICE_END.value,
                "name": "语音结束",
                "description": "结束语音通话"
            },
            {
                "type": MessageType.SYSTEM.value,
                "name": "系统消息",
                "description": "系统通知消息"
            },
            {
                "type": MessageType.HEARTBEAT.value,
                "name": "心跳",
                "description": "保持连接的心跳消息"
            }
        ]
        
        return {
            "success": True,
            "message_types": message_types
        }
        
    except Exception as e:
        logger.error(f"获取消息类型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.get("/user-statuses", summary="获取用户状态")
async def get_user_statuses():
    """
    获取支持的用户状态
    
    返回系统支持的所有用户状态
    """
    try:
        user_statuses = [
            {
                "status": UserStatus.ONLINE.value,
                "name": "在线",
                "description": "用户当前在线"
            },
            {
                "status": UserStatus.AWAY.value,
                "name": "离开",
                "description": "用户暂时离开"
            },
            {
                "status": UserStatus.BUSY.value,
                "name": "忙碌",
                "description": "用户正在忙碌"
            },
            {
                "status": UserStatus.OFFLINE.value,
                "name": "离线",
                "description": "用户已离线"
            }
        ]
        
        return {
            "success": True,
            "user_statuses": user_statuses
        }
        
    except Exception as e:
        logger.error(f"获取用户状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.get("/stats", summary="获取协作统计")
async def get_collaboration_stats():
    """
    获取协作统计信息
    
    返回系统的协作使用统计
    """
    try:
        # 获取房间列表
        rooms = await collaboration_service.get_room_list()
        
        # 计算统计信息
        total_rooms = len(rooms)
        active_rooms = len([r for r in rooms if r["user_count"] > 0])
        total_users = sum(r["user_count"] for r in rooms)
        
        # 按房间类型统计
        private_rooms = len([r for r in rooms if r["is_private"]])
        public_rooms = total_rooms - private_rooms
        
        return {
            "success": True,
            "stats": {
                "total_rooms": total_rooms,
                "active_rooms": active_rooms,
                "private_rooms": private_rooms,
                "public_rooms": public_rooms,
                "total_users": total_users,
                "avg_users_per_room": total_users / max(active_rooms, 1)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取协作统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@collaboration_router.post("/test", summary="测试协作功能")
async def test_collaboration():
    """
    测试协作功能
    
    执行基础的协作功能测试
    """
    try:
        test_results = {
            "room_creation": False,
            "room_info": False,
            "room_list": False,
            "errors": []
        }
        
        # 测试创建房间
        try:
            room_id = await collaboration_service.create_room(
                name="测试房间",
                created_by="test_user",
                description="这是一个测试房间"
            )
            test_results["room_creation"] = True
            
            # 测试获取房间信息
            room_info = await collaboration_service.get_room_info(room_id)
            test_results["room_info"] = room_info is not None
            
            # 测试获取房间列表
            rooms = await collaboration_service.get_room_list()
            test_results["room_list"] = len(rooms) > 0
            
        except Exception as e:
            test_results["errors"].append(f"房间测试失败: {str(e)}")
        
        # 总体测试结果
        test_results["overall_success"] = (
            test_results["room_creation"] and
            test_results["room_info"] and
            test_results["room_list"]
        )
        
        return {
            "success": True,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"协作功能测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
