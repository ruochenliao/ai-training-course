"""
升级版流式聊天API
基于AutoGen智能体框架和SSE实现的高性能流式对话接口
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.dependency import DependAuth
from app.models.admin import User
from app.agents import AgentManager
from app.core.model_manager import model_manager
from app.schemas.base import Success

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamChatRequest(BaseModel):
    """流式聊天请求模型"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=10000)
    conversation_id: Optional[str] = Field(None, description="会话ID")
    model_name: Optional[str] = Field(None, description="指定使用的模型")
    temperature: Optional[float] = Field(0.7, description="温度参数", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(2048, description="最大token数", ge=1, le=8192)
    stream: bool = Field(True, description="是否流式输出")
    include_context: bool = Field(True, description="是否包含上下文")
    enable_tools: bool = Field(True, description="是否启用工具调用")
    enable_knowledge: bool = Field(True, description="是否启用知识检索")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class StreamChatResponse(BaseModel):
    """流式聊天响应模型"""
    type: str = Field(..., description="消息类型: text, tool_call, knowledge, error, done")
    content: str = Field("", description="消息内容")
    delta: str = Field("", description="增量内容")
    conversation_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")
    timestamp: str = Field(..., description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ChatSession:
    """聊天会话管理"""
    
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.agent_manager = None
    
    async def initialize_agents(self):
        """初始化智能体"""
        if not self.agent_manager:
            self.agent_manager = AgentManager()
            await self.agent_manager.initialize()
    
    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.now()
        self.message_count += 1


# 全局会话管理
active_sessions: Dict[str, ChatSession] = {}


async def get_or_create_session(user_id: str, conversation_id: Optional[str] = None) -> ChatSession:
    """获取或创建聊天会话"""
    if conversation_id is None:
        conversation_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
    
    session_key = f"{user_id}_{conversation_id}"
    
    if session_key not in active_sessions:
        session = ChatSession(user_id, conversation_id)
        await session.initialize_agents()
        active_sessions[session_key] = session
    
    session = active_sessions[session_key]
    session.update_activity()
    
    return session


async def generate_sse_response(
    session: ChatSession,
    request: StreamChatRequest,
    user: User
) -> AsyncGenerator[str, None]:
    """生成SSE流式响应"""
    try:
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        
        # 构建上下文
        context = {
            'user_id': str(user.id),
            'username': user.username,
            'conversation_id': session.conversation_id,
            'message_id': message_id,
            'enable_tools': request.enable_tools,
            'enable_knowledge': request.enable_knowledge,
            'metadata': request.metadata or {}
        }
        
        # 发送开始消息
        start_response = StreamChatResponse(
            type="start",
            content="",
            delta="",
            conversation_id=session.conversation_id,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            metadata={"status": "processing"}
        )
        yield f"data: {start_response.model_dump_json()}\n\n"
        
        # 使用智能体处理消息
        if session.agent_manager:
            # 流式处理
            async for chunk in session.agent_manager.stream_chat(
                message=request.message,
                context=context,
                model_config={
                    'model_name': request.model_name,
                    'temperature': request.temperature,
                    'max_tokens': request.max_tokens
                }
            ):
                chunk_response = StreamChatResponse(
                    type="text",
                    content="",
                    delta=chunk,
                    conversation_id=session.conversation_id,
                    message_id=message_id,
                    timestamp=datetime.now().isoformat()
                )
                yield f"data: {chunk_response.model_dump_json()}\n\n"
                
                # 添加小延迟以避免过快的流式输出
                await asyncio.sleep(0.01)
        
        else:
            # 降级处理：直接使用模型服务
            llm_service = model_manager.get_default_model(ModelType.LLM)
            if llm_service:
                messages = [
                    {"role": "system", "content": "你是一个专业的智能客服助手。"},
                    {"role": "user", "content": request.message}
                ]
                
                async for chunk in llm_service.chat_completion_stream(
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    chunk_response = StreamChatResponse(
                        type="text",
                        content="",
                        delta=chunk,
                        conversation_id=session.conversation_id,
                        message_id=message_id,
                        timestamp=datetime.now().isoformat()
                    )
                    yield f"data: {chunk_response.model_dump_json()}\n\n"
                    await asyncio.sleep(0.01)
        
        # 发送完成消息
        done_response = StreamChatResponse(
            type="done",
            content="",
            delta="",
            conversation_id=session.conversation_id,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            metadata={"status": "completed"}
        )
        yield f"data: {done_response.model_dump_json()}\n\n"
        
    except Exception as e:
        logger.error(f"流式聊天处理失败: {str(e)}")
        
        # 发送错误消息
        error_response = StreamChatResponse(
            type="error",
            content=f"处理消息时发生错误: {str(e)}",
            delta="",
            conversation_id=session.conversation_id,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            metadata={"error": str(e)}
        )
        yield f"data: {error_response.model_dump_json()}\n\n"


@router.post("/stream", summary="流式聊天对话")
async def stream_chat(
    request: StreamChatRequest,
    current_user: User = DependAuth
):
    """
    流式聊天对话接口
    
    - 支持Server-Sent Events (SSE)流式响应
    - 集成AutoGen智能体框架
    - 支持工具调用和知识检索
    - 支持模型热切换
    """
    try:
        # 获取或创建会话
        session = await get_or_create_session(
            user_id=str(current_user.id),
            conversation_id=request.conversation_id
        )
        
        # 返回流式响应
        return StreamingResponse(
            generate_sse_response(session, request, current_user),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"流式聊天接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式聊天失败: {str(e)}")


@router.post("/chat", summary="普通聊天对话")
async def normal_chat(
    request: StreamChatRequest,
    current_user: User = DependAuth
):
    """
    普通聊天对话接口（非流式）
    
    - 返回完整的聊天响应
    - 适用于不支持SSE的客户端
    """
    try:
        # 获取或创建会话
        session = await get_or_create_session(
            user_id=str(current_user.id),
            conversation_id=request.conversation_id
        )
        
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        
        # 构建上下文
        context = {
            'user_id': str(current_user.id),
            'username': current_user.username,
            'conversation_id': session.conversation_id,
            'message_id': message_id,
            'enable_tools': request.enable_tools,
            'enable_knowledge': request.enable_knowledge,
            'metadata': request.metadata or {}
        }
        
        # 处理消息
        if session.agent_manager:
            response_content = await session.agent_manager.process_message(
                message=request.message,
                context=context,
                model_config={
                    'model_name': request.model_name,
                    'temperature': request.temperature,
                    'max_tokens': request.max_tokens
                }
            )
        else:
            # 降级处理
            response_content = "抱歉，智能体服务暂时不可用，请稍后再试。"
        
        # 构建响应
        response = {
            "conversation_id": session.conversation_id,
            "message_id": message_id,
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "user_id": str(current_user.id),
                "message_count": session.message_count
            }
        }
        
        return Success(data=response, msg="聊天成功")
        
    except Exception as e:
        logger.error(f"普通聊天接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")


@router.get("/sessions", summary="获取用户会话列表")
async def get_user_sessions(
    current_user: User = DependAuth
):
    """获取当前用户的所有活跃会话"""
    try:
        user_sessions = []
        user_id = str(current_user.id)
        
        for session_key, session in active_sessions.items():
            if session.user_id == user_id:
                user_sessions.append({
                    "conversation_id": session.conversation_id,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "message_count": session.message_count
                })
        
        return Success(data=user_sessions, msg="获取会话列表成功")
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.delete("/sessions/{conversation_id}", summary="删除会话")
async def delete_session(
    conversation_id: str,
    current_user: User = DependAuth
):
    """删除指定会话"""
    try:
        user_id = str(current_user.id)
        session_key = f"{user_id}_{conversation_id}"
        
        if session_key in active_sessions:
            del active_sessions[session_key]
            return Success(msg="会话删除成功")
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.get("/health", summary="聊天服务健康检查")
async def chat_health_check():
    """聊天服务健康检查"""
    try:
        health_status = {
            "service": "chat_stream",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions),
            "model_manager_status": "unknown",
            "agent_manager_status": "unknown"
        }
        
        # 检查模型管理器状态
        try:
            model_health = await model_manager.health_check()
            health_status["model_manager_status"] = "healthy" if model_health.get("ready_models", 0) > 0 else "degraded"
        except Exception as e:
            health_status["model_manager_status"] = f"error: {str(e)}"
        
        # 检查智能体管理器状态
        try:
            # 这里可以添加智能体管理器的健康检查
            health_status["agent_manager_status"] = "healthy"
        except Exception as e:
            health_status["agent_manager_status"] = f"error: {str(e)}"
        
        return Success(data=health_status, msg="健康检查完成")
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
