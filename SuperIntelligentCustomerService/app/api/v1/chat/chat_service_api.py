"""
聊天服务API端点
基于AutoGen框架的智能聊天服务接口
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from starlette.responses import Response

from ....core.dependency import DependAuth
from ....models.admin import User
from ....schemas.chat_service import ChatRequest, ChatResponse, SessionInfo, SessionStats
from ....services.chat_service import chat_service
from ....utils.response import Success, Fail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send", summary="发送聊天消息")
async def send_chat_message(
    request: ChatRequest,
    current_user: User = DependAuth
):
    """
    发送聊天消息并获取AI回复
    支持流式和非流式响应
    """
    try:
        # 验证请求参数
        if not request.message.strip():
            return Fail(msg="消息内容不能为空")
        
        # 设置用户ID
        request.user_id = str(current_user.id)
        
        # 如果启用流式响应
        if request.stream:
            return StreamingResponse(
                _generate_stream_response(request),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # 非流式响应
            full_response = ""
            async for chunk in chat_service.send_message(request):
                if chunk.content:
                    full_response += chunk.content
                if chunk.is_final:
                    break
            
            return Success(data={
                "session_id": request.session_id,
                "response": full_response,
                "metadata": {
                    "user_id": request.user_id,
                    "model": request.model_name
                }
            })
    
    except Exception as e:
        logger.error(f"发送聊天消息失败: {e}")
        return Fail(msg=f"发送消息失败: {str(e)}")


async def _generate_stream_response(request: ChatRequest) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    try:
        async for chunk in chat_service.send_message(request):
            # 构造SSE格式的响应
            if chunk.content:
                data = {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "is_final": chunk.is_final,
                    "session_id": chunk.session_id
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            if chunk.is_final:
                # 发送结束标记
                yield f"data: [DONE]\n\n"
                break
                
    except Exception as e:
        logger.error(f"流式响应生成失败: {e}")
        error_data = {
            "error": True,
            "message": f"响应生成失败: {str(e)}"
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


@router.get("/session/{session_id}", summary="获取会话信息")
async def get_session_info(
    session_id: str,
    current_user: User = DependAuth
):
    """获取指定会话的信息"""
    try:
        user_id = str(current_user.id)
        session_info = await chat_service.get_session_info(user_id, session_id)
        
        if not session_info:
            return Fail(msg="会话不存在")
        
        return Success(data=session_info.dict())
    
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        return Fail(msg=f"获取会话信息失败: {str(e)}")


@router.get("/sessions", summary="获取用户会话列表")
async def list_user_sessions(
    current_user: User = DependAuth
):
    """获取当前用户的所有会话列表"""
    try:
        user_id = str(current_user.id)
        sessions = await chat_service.list_user_sessions(user_id)
        
        return Success(data=[session.dict() for session in sessions])
    
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return Fail(msg=f"获取会话列表失败: {str(e)}")


@router.delete("/session/{session_id}", summary="关闭会话")
async def close_session(
    session_id: str,
    current_user: User = DependAuth
):
    """关闭指定的会话"""
    try:
        user_id = str(current_user.id)
        success = await chat_service.close_session(user_id, session_id)
        
        if success:
            return Success(msg="会话已关闭")
        else:
            return Fail(msg="关闭会话失败")
    
    except Exception as e:
        logger.error(f"关闭会话失败: {e}")
        return Fail(msg=f"关闭会话失败: {str(e)}")


@router.post("/session/create", summary="创建新会话")
async def create_session(
    current_user: User = DependAuth
):
    """创建新的聊天会话"""
    try:
        user_id = str(current_user.id)
        session = await chat_service.get_or_create_session(user_id)
        
        return Success(data={
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "message": "会话创建成功"
        })
    
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return Fail(msg=f"创建会话失败: {str(e)}")


@router.get("/stats", summary="获取服务统计")
async def get_service_stats(
    current_user: User = DependAuth
):
    """获取聊天服务统计信息（管理员功能）"""
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            return Fail(msg="权限不足")
        
        stats = await chat_service.get_service_stats()
        return Success(data=stats.dict())
    
    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        return Fail(msg=f"获取服务统计失败: {str(e)}")


@router.post("/test", summary="测试聊天服务")
async def test_chat_service(
    current_user: User = DependAuth
):
    """测试聊天服务是否正常工作"""
    try:
        # 创建测试请求
        test_request = ChatRequest(
            user_id=str(current_user.id),
            session_id="test_session",
            message="你好，请介绍一下你自己",
            stream=False
        )
        
        # 发送测试消息
        full_response = ""
        async for chunk in chat_service.send_message(test_request):
            if chunk.content:
                full_response += chunk.content
            if chunk.is_final:
                break
        
        return Success(data={
            "test_message": test_request.message,
            "ai_response": full_response,
            "status": "聊天服务正常工作"
        })
    
    except Exception as e:
        logger.error(f"测试聊天服务失败: {e}")
        return Fail(msg=f"测试失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """聊天服务健康检查"""
    try:
        # 检查服务状态
        stats = await chat_service.get_service_stats()
        
        return Success(data={
            "status": "healthy",
            "active_sessions": stats.active_sessions,
            "total_sessions": stats.total_sessions,
            "service_uptime": "正常运行"
        })
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return Fail(msg=f"服务异常: {str(e)}")
