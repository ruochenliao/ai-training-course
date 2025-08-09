# Copyright (c) 2025 左岚. All rights reserved.
"""
SSE API端点

提供SSE连接和消息处理的API接口。
"""

# # Standard library imports
import logging
from typing import Any, Dict, Optional

# # Third-party imports
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# # Local folder imports
from app.api.deps import get_current_user
from ...models.user import User
from ...sse.handlers import ChatHandler, WorkflowHandler
from ...sse.manager import ConnectionType, sse_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建处理器实例
chat_handler = ChatHandler(sse_manager)
workflow_handler = WorkflowHandler(sse_manager)


class ChatMessageRequest(BaseModel):
    """聊天消息请求"""
    content: str
    agent_type: str = "customer_service"
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentSelectRequest(BaseModel):
    """智能体选择请求"""
    agent_type: str
    session_id: Optional[str] = None


class WorkflowStartRequest(BaseModel):
    """工作流启动请求"""
    user_request: str
    context: Dict[str, Any] = {}


@router.get("/chat/{user_id}")
async def chat_sse_endpoint(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """聊天SSE连接端点"""
    try:
        # 验证用户权限
        if current_user.id != int(user_id) and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权限访问此连接")
        
        # 创建SSE连接
        connection_id = sse_manager.create_connection(
            user_id=user_id,
            connection_type=ConnectionType.CHAT,
            request=request
        )
        
        logger.info(f"创建聊天SSE连接: {connection_id}")
        
        # 返回SSE流
        return StreamingResponse(
            sse_manager.create_event_stream(connection_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"创建聊天SSE连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.get("/workflow/{user_id}")
async def workflow_sse_endpoint(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """工作流SSE连接端点"""
    try:
        # 验证用户权限
        if current_user.id != int(user_id) and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权限访问此连接")
        
        # 创建SSE连接
        connection_id = sse_manager.create_connection(
            user_id=user_id,
            connection_type=ConnectionType.WORKFLOW,
            request=request
        )
        
        logger.info(f"创建工作流SSE连接: {connection_id}")
        
        # 返回SSE流
        return StreamingResponse(
            sse_manager.create_event_stream(connection_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"创建工作流SSE连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.get("/admin/{user_id}")
async def admin_sse_endpoint(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """管理员SSE连接端点"""
    try:
        # 验证管理员权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 创建SSE连接
        connection_id = sse_manager.create_connection(
            user_id=user_id,
            connection_type=ConnectionType.ADMIN,
            request=request
        )
        
        logger.info(f"创建管理员SSE连接: {connection_id}")
        
        # 返回SSE流
        return StreamingResponse(
            sse_manager.create_event_stream(connection_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"创建管理员SSE连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/chat/send")
async def send_chat_message(
    message_request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """发送聊天消息"""
    try:
        user_id = str(current_user.id)
        
        # 在后台处理聊天消息
        background_tasks.add_task(
            chat_handler.handle_chat_message,
            user_id=user_id,
            content=message_request.content,
            agent_type=message_request.agent_type,
            session_id=message_request.session_id,
            metadata=message_request.metadata
        )
        
        return {"status": "success", "message": "消息已发送"}
        
    except Exception as e:
        logger.error(f"发送聊天消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


@router.post("/chat/select-agent")
async def select_agent(
    select_request: AgentSelectRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """选择智能体"""
    try:
        user_id = str(current_user.id)
        
        # 在后台处理智能体选择
        background_tasks.add_task(
            chat_handler.handle_agent_select,
            user_id=user_id,
            agent_type=select_request.agent_type,
            session_id=select_request.session_id
        )
        
        return {"status": "success", "message": "智能体已选择"}
        
    except Exception as e:
        logger.error(f"选择智能体失败: {e}")
        raise HTTPException(status_code=500, detail=f"选择失败: {str(e)}")


@router.post("/workflow/start")
async def start_workflow(
    workflow_request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """启动工作流"""
    try:
        user_id = str(current_user.id)
        
        # 在后台处理工作流启动
        background_tasks.add_task(
            workflow_handler.handle_workflow_start,
            user_id=user_id,
            user_request=workflow_request.user_request,
            context=workflow_request.context
        )
        
        return {"status": "success", "message": "工作流已启动"}
        
    except Exception as e:
        logger.error(f"启动工作流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.get("/stats")
async def get_sse_stats(current_user: User = Depends(get_current_user)):
    """获取SSE连接统计"""
    try:
        # 验证管理员权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = sse_manager.get_stats()
        return {"status": "success", "data": stats}
        
    except Exception as e:
        logger.error(f"获取SSE统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """广播消息"""
    try:
        # 验证管理员权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # # Local folder imports
        from ...sse.events import SSEEvent

        # 创建广播事件
        broadcast_event = SSEEvent(
            type="broadcast",
            data=message
        )
        
        # 在后台广播消息
        background_tasks.add_task(
            sse_manager.broadcast_to_all,
            broadcast_event
        )
        
        return {"status": "success", "message": "消息已广播"}
        
    except Exception as e:
        logger.error(f"广播消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"广播失败: {str(e)}")
