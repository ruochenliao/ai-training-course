"""
WebSocket API端点

提供WebSocket连接和实时通信功能。
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_db, get_current_user_websocket
from app.models.user import User
from app.websocket.manager import connection_manager, ConnectionType
from app.websocket.handlers import ChatHandler, WorkflowHandler

router = APIRouter()
logger = logging.getLogger(__name__)

# 创建处理器
chat_handler = ChatHandler(connection_manager)
workflow_handler = WorkflowHandler(connection_manager)


@router.websocket("/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    """聊天WebSocket端点"""
    connection_id = None
    try:
        # 建立连接
        connection_id = await connection_manager.connect(
            websocket, user_id, ConnectionType.CHAT
        )
        
        # 订阅用户频道
        connection_manager.subscribe_to_channel(connection_id, f"user_{user_id}")
        
        logger.info(f"聊天WebSocket连接建立: {connection_id}")
        
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 获取连接对象
            connection = connection_manager.get_connection(connection_id)
            if not connection:
                break
            
            # 处理消息
            await chat_handler.handle_message(connection, message)
            
    except WebSocketDisconnect:
        logger.info(f"聊天WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"聊天WebSocket错误: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/workflow/{user_id}")
async def websocket_workflow_endpoint(websocket: WebSocket, user_id: str):
    """工作流WebSocket端点"""
    connection_id = None
    try:
        # 建立连接
        connection_id = await connection_manager.connect(
            websocket, user_id, ConnectionType.WORKFLOW
        )
        
        # 订阅工作流频道
        connection_manager.subscribe_to_channel(connection_id, f"workflow_{user_id}")
        
        logger.info(f"工作流WebSocket连接建立: {connection_id}")
        
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 获取连接对象
            connection = connection_manager.get_connection(connection_id)
            if not connection:
                break
            
            # 处理消息
            await workflow_handler.handle_message(connection, message)
            
    except WebSocketDisconnect:
        logger.info(f"工作流WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"工作流WebSocket错误: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/admin/{user_id}")
async def websocket_admin_endpoint(websocket: WebSocket, user_id: str):
    """管理员WebSocket端点"""
    connection_id = None
    try:
        # 建立连接
        connection_id = await connection_manager.connect(
            websocket, user_id, ConnectionType.ADMIN
        )
        
        # 订阅管理员频道
        connection_manager.subscribe_to_channel(connection_id, "admin")
        connection_manager.subscribe_to_channel(connection_id, f"user_{user_id}")
        
        logger.info(f"管理员WebSocket连接建立: {connection_id}")
        
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 获取连接对象
            connection = connection_manager.get_connection(connection_id)
            if not connection:
                break
            
            # 处理管理员消息
            await handle_admin_message(connection, message)
            
    except WebSocketDisconnect:
        logger.info(f"管理员WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"管理员WebSocket错误: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def handle_admin_message(connection, message: Dict[str, Any]):
    """处理管理员消息"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == "broadcast":
            # 广播消息
            broadcast_message = {
                "type": "system_notification",
                "data": {
                    "title": data.get("title", "系统通知"),
                    "message": data.get("message", ""),
                    "level": data.get("level", "info")
                },
                "timestamp": datetime.now().isoformat()
            }
            
            sent_count = await connection_manager.broadcast_to_all(broadcast_message)
            
            await connection.send_message({
                "type": "broadcast_result",
                "data": {
                    "sent_count": sent_count,
                    "message": "广播发送完成"
                }
            })
            
        elif message_type == "get_stats":
            # 获取连接统计
            stats = connection_manager.get_stats()
            
            await connection.send_message({
                "type": "stats",
                "data": stats
            })
            
        else:
            await connection.send_error("未知的管理员消息类型", "UNKNOWN_ADMIN_MESSAGE")
            
    except Exception as e:
        logger.error(f"管理员消息处理失败: {e}")
        await connection.send_error(f"管理员消息处理失败: {str(e)}")


# HTTP API端点用于WebSocket管理
@router.get("/connections/stats")
async def get_connection_stats(current_user: User = Depends(get_current_user_websocket)):
    """获取连接统计"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return connection_manager.get_stats()


@router.post("/connections/{user_id}/send")
async def send_message_to_user(
    user_id: str,
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user_websocket)
):
    """发送消息给指定用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    sent_count = await connection_manager.send_to_user(user_id, message)
    
    return {
        "success": True,
        "sent_count": sent_count,
        "message": f"消息已发送给用户 {user_id}"
    }


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user_websocket)
):
    """广播消息"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    sent_count = await connection_manager.broadcast_to_all(message)
    
    return {
        "success": True,
        "sent_count": sent_count,
        "message": "广播消息发送完成"
    }


@router.delete("/connections/{connection_id}")
async def disconnect_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user_websocket)
):
    """断开指定连接"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    await connection_manager.disconnect(connection_id)
    
    return {
        "success": True,
        "message": f"连接 {connection_id} 已断开"
    }


@router.post("/cleanup")
async def cleanup_inactive_connections(
    timeout_minutes: int = 30,
    current_user: User = Depends(get_current_user_websocket)
):
    """清理不活跃连接"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    await connection_manager.cleanup_inactive_connections(timeout_minutes)
    
    return {
        "success": True,
        "message": f"已清理超过 {timeout_minutes} 分钟的不活跃连接"
    }
