"""
文件处理监控API路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.services.file_processing_monitor import (
    file_processing_monitor,
    get_file_status,
    get_all_file_status,
    ProcessingEvent
)
from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.knowledge import KnowledgeFile
import json
import asyncio

router = APIRouter()


@router.get("/status/{file_id}", summary="获取文件处理状态", response_model=dict)
async def get_file_processing_status(
    file_id: int,
    current_user: User = DependAuth
):
    """
    获取指定文件的处理状态
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        
    Returns:
        文件处理状态
    """
    try:
        # 检查文件权限
        file_obj = await KnowledgeFile.get_or_none(id=file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查访问权限（这里简化处理，实际应该检查知识库权限）
        kb = await file_obj.knowledge_base
        if kb.owner_id != current_user.id and not kb.is_public:
            raise HTTPException(status_code=403, detail="无权限访问该文件")
        
        # 获取监控状态
        monitor_status = get_file_status(file_id)
        
        # 如果监控中没有，从数据库获取
        if not monitor_status:
            monitor_status = {
                "file_id": file_id,
                "filename": file_obj.name,
                "status": file_obj.embedding_status,
                "progress": 100.0 if file_obj.embedding_status == "completed" else 0.0,
                "error_message": file_obj.embedding_error,
                "started_at": None,
                "completed_at": file_obj.processed_at.isoformat() if file_obj.processed_at else None,
                "estimated_completion": None,
                "processing_time": None
            }
        
        return {
            "success": True,
            "data": monitor_status,
            "msg": "获取处理状态成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")


@router.get("/status", summary="获取所有文件处理状态", response_model=dict)
async def get_all_processing_status(
    current_user: User = DependAuth
):
    """
    获取当前用户所有文件的处理状态
    
    Args:
        current_user: 当前用户
        
    Returns:
        所有文件处理状态
    """
    try:
        # 获取所有监控状态
        all_status = get_all_file_status()
        
        # 过滤用户有权限的文件
        user_status = []
        for status in all_status:
            try:
                file_obj = await KnowledgeFile.get_or_none(id=status["file_id"])
                if file_obj:
                    kb = await file_obj.knowledge_base
                    if kb.owner_id == current_user.id or kb.is_public:
                        user_status.append(status)
            except:
                continue
        
        return {
            "success": True,
            "data": user_status,
            "msg": f"获取处理状态成功，共 {len(user_status)} 个文件"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")


@router.get("/statistics", summary="获取处理统计信息", response_model=dict)
async def get_processing_statistics(
    current_user: User = DependAuth
):
    """
    获取文件处理统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        处理统计信息
    """
    try:
        # 获取全局统计
        global_stats = await file_processing_monitor.get_statistics()
        
        # 获取用户相关统计
        user_files = await KnowledgeFile.filter(
            knowledge_base__owner_id=current_user.id,
            is_deleted=False
        ).all()
        
        user_stats = {
            "total_files": len(user_files),
            "pending_files": len([f for f in user_files if f.embedding_status == "pending"]),
            "processing_files": len([f for f in user_files if f.embedding_status == "processing"]),
            "completed_files": len([f for f in user_files if f.embedding_status == "completed"]),
            "failed_files": len([f for f in user_files if f.embedding_status == "failed"])
        }
        
        return {
            "success": True,
            "data": {
                "global": global_stats,
                "user": user_stats
            },
            "msg": "获取统计信息成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/cancel/{file_id}", summary="取消文件处理", response_model=dict)
async def cancel_file_processing(
    file_id: int,
    current_user: User = DependAuth
):
    """
    取消文件处理
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        
    Returns:
        取消结果
    """
    try:
        # 检查文件权限
        file_obj = await KnowledgeFile.get_or_none(id=file_id)
        if not file_obj:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        kb = await file_obj.knowledge_base
        if kb.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限操作该文件")
        
        # 检查文件状态
        if file_obj.embedding_status not in ["pending", "processing"]:
            raise HTTPException(status_code=400, detail="文件不在处理中，无法取消")
        
        # 取消处理
        await file_processing_monitor.cancel_processing(file_id)
        
        # 更新数据库状态
        file_obj.embedding_status = "cancelled"
        file_obj.embedding_error = "用户取消处理"
        await file_obj.save()
        
        return {
            "success": True,
            "msg": "文件处理已取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消处理失败: {str(e)}")


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections and websocket in self.user_connections[user_id]:
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # 连接已断开，移除
                    self.disconnect(connection, user_id)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket端点，用于实时推送文件处理状态
    
    Args:
        websocket: WebSocket连接
        user_id: 用户ID
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# 事件监听器
async def processing_event_listener(event: ProcessingEvent, status):
    """
    处理事件监听器，用于WebSocket推送
    
    Args:
        event: 处理事件
        status: 处理状态
    """
    try:
        # 获取文件信息以确定用户
        file_obj = await KnowledgeFile.get_or_none(id=status.file_id)
        if file_obj:
            kb = await file_obj.knowledge_base
            user_id = kb.owner_id
            
            # 推送给用户
            message = {
                "type": "processing_update",
                "event": event.value,
                "data": status.to_dict()
            }
            await manager.send_to_user(user_id, message)
            
    except Exception as e:
        print(f"推送事件失败: {e}")


# 注册事件监听器
file_processing_monitor.add_event_listener(processing_event_listener)
