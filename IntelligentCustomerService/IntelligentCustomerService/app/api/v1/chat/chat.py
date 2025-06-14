"""
智能客服聊天API
基于FastAPI和Deepseek模型实现流式对话功能
"""
import json

from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse

from app.controllers.chat import chat_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, SuccessExtra, Fail
from app.schemas.chat import (
    SendMessageRequest,
    UpdateConversationRequest
)

router = APIRouter()


@router.post("/send-stream", summary="发送消息（流式）")
async def send_message_stream(
        request: SendMessageRequest,
        current_user: User = DependAuth,
):
    """
    发送消息到智能客服（流式响应）
    - 实时返回AI生成的回复内容
    - 支持Server-Sent Events (SSE)
    """
    user_id = current_user.id

    async def generate_stream():
        try:
            async for chunk in chat_controller.send_message_stream(request, user_id):
                # 将StreamMessageChunk转换为JSON字符串
                chunk_data = {
                    "conversation_id": chunk.conversation_id,
                    "message_id": chunk.message_id,
                    "content": chunk.content,
                    "is_complete": chunk.is_complete,
                    "timestamp": chunk.timestamp.isoformat()
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"

                # 如果完成，发送结束标志
                if chunk.is_complete:
                    yield "data: [DONE]\n\n"
                    break
        except Exception as e:
            error_data = {
                "error": str(e),
                "is_complete": True,
                "timestamp": "2024-01-01T00:00:00"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
            "X-Response-Type": "stream"  # 添加自定义头，供中间件识别流式响应
        }
    )


@router.post("/send", summary="发送消息（非流式）")
async def send_message(
        request: SendMessageRequest,
        current_user: User = DependAuth,
):
    """
    发送消息到智能客服（非流式响应）
    - 返回完整的对话响应
    """
    user_id = current_user.id
    try:
        response = await chat_controller.send_message(request, user_id)
        return Success(data=response, msg="消息发送成功")
    except Exception as e:
        return Fail(code=500, msg=f"发送消息失败: {str(e)}")


@router.post("/conversation/create", summary="创建新对话")
async def create_conversation(
        title: str = Query("新对话", description="对话标题"),
        current_user: User = DependAuth,
):
    """创建新的聊天对话"""
    user_id = current_user.id
    try:
        conversation = await chat_controller.create_conversation(user_id, title)
        conversation_dict = await conversation.to_dict()
        return Success(data=conversation_dict, msg="对话创建成功")
    except Exception as e:
        return Fail(code=500, msg=f"创建对话失败: {str(e)}")


@router.get("/conversations", summary="获取对话列表")
async def get_conversations(
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, description="每页数量"),
        current_user: User = DependAuth,
):
    """获取用户的对话列表"""
    user_id = current_user.id
    try:
        total, conversations = await chat_controller.get_user_conversations(
            user_id, page, page_size
        )

        data = []
        for conv in conversations:
            conv_dict = await conv.to_dict()
            data.append(conv_dict)

        return SuccessExtra(
            data=data,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        return Fail(code=500, msg=f"获取对话列表失败: {str(e)}")


@router.get("/conversation/{conversation_id}/messages", summary="获取对话消息")
async def get_conversation_messages(
        conversation_id: str,
        limit: int = Query(50, description="消息数量限制"),
        current_user: User = DependAuth,
):
    """获取指定对话的消息历史"""
    user_id = current_user.id
    try:
        # 验证对话是否存在且属于当前用户
        conversation = await chat_controller.get_conversation(conversation_id, user_id)
        if not conversation:
            return Fail(code=404, msg="对话不存在")

        messages = await chat_controller.get_conversation_messages(
            conversation_id, user_id, limit
        )

        data = []
        for msg in messages:
            msg_dict = await msg.to_dict()
            data.append(msg_dict)

        return Success(data=data, msg="获取消息成功")
    except Exception as e:
        return Fail(code=500, msg=f"获取消息失败: {str(e)}")


@router.put("/conversation/{conversation_id}", summary="更新对话")
async def update_conversation(
        conversation_id: str,
        request: UpdateConversationRequest,
        current_user: User = DependAuth,
):
    """更新对话信息（如标题）"""
    user_id = current_user.id
    try:
        if request.title is not None:
            success = await chat_controller.update_conversation_title(
                conversation_id, user_id, request.title
            )
            if not success:
                return Fail(code=404, msg="对话不存在")

        return Success(msg="对话更新成功")
    except Exception as e:
        return Fail(code=500, msg=f"更新对话失败: {str(e)}")


@router.delete("/conversation/{conversation_id}", summary="删除对话")
async def delete_conversation(
        conversation_id: str,
        current_user: User = DependAuth,
):
    """删除指定对话及其所有消息"""
    user_id = current_user.id
    try:
        success = await chat_controller.delete_conversation(conversation_id, user_id)
        if not success:
            return Fail(code=404, msg="对话不存在")

        return Success(msg="对话删除成功")
    except Exception as e:
        return Fail(code=500, msg=f"删除对话失败: {str(e)}")


@router.get("/stats", summary="获取聊天统计")
async def get_chat_stats(
        current_user: User = DependAuth,
):
    """获取用户的聊天统计信息"""
    user_id = current_user.id
    try:
        from app.models.admin import ChatConversation, ChatMessage

        # 统计对话数量
        total_conversations = await ChatConversation.filter(user_id=user_id).count()

        # 统计消息数量
        total_messages = await ChatMessage.filter(user_id=user_id).count()

        # 统计token使用量
        messages = await ChatMessage.filter(user_id=user_id).all()
        total_tokens_used = sum(msg.tokens_used for msg in messages)

        # 计算平均响应时间
        assistant_messages = [msg for msg in messages if msg.sender == "assistant" and msg.response_time > 0]
        avg_response_time = (
            sum(msg.response_time for msg in assistant_messages) / len(assistant_messages)
            if assistant_messages else 0
        )

        stats = {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tokens_used": total_tokens_used,
            "avg_response_time": round(avg_response_time, 2)
        }

        return Success(data=stats, msg="获取统计信息成功")
    except Exception as e:
        return Fail(code=500, msg=f"获取统计信息失败: {str(e)}")


@router.get("/config", summary="获取聊天配置")
async def get_chat_config():
    """获取聊天系统配置信息"""
    try:
        from app.core.llm_config import deepseek_config

        config = {
            "model_name": deepseek_config.model_name,
            "max_tokens": 128000,
            "temperature": 0.7,
            "stream_enabled": True
        }

        return Success(data=config, msg="获取配置成功")
    except Exception as e:
        return Fail(code=500, msg=f"获取配置失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """检查聊天服务健康状态"""
    try:
        # 简单的健康检查
        from app.core.llm_config import get_deepseek_client
        get_deepseek_client()

        return Success(data={"status": "healthy", "model": "deepseek-chat"}, msg="服务正常")
    except Exception as e:
        return Fail(code=500, msg=f"服务异常: {str(e)}")
