from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator

from app.controllers.chat import chat_controller
from app.controllers.model import model_controller
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas import Success, Fail
from app.schemas.chat import SendDTO, ChatMessageCreate

router = APIRouter()


@router.post("/send", summary="发送聊天消息")
async def send_message(
    send_data: SendDTO,
    current_user: User = DependAuth
):
    """发送聊天消息"""
    try:
        user_id = current_user.id
        # 验证必要参数
        if not send_data.messages:
            return Fail(msg="消息内容不能为空")

        if not send_data.session_id:
            return Fail(msg="会话ID不能为空")

        # 获取用户消息（最后一条通常是用户输入）
        user_message = None
        for msg in reversed(send_data.messages):
            if msg.role == "user":
                user_message = msg
                break

        if not user_message or not user_message.content:
            return Fail(msg="未找到有效的用户消息")

        # 保存用户消息到数据库
        user_message_create = ChatMessageCreate(
            session_id=int(send_data.session_id),
            user_id=user_id,
            role="user",
            content=user_message.content,
            model_name=send_data.model,
            total_tokens=0,
            deduct_cost=0
        )
        await chat_controller.create_message(user_message_create)

        # 如果是流式响应
        if send_data.stream:
            return StreamingResponse(
                generate_stream_response(send_data, user_id),
                media_type="text/plain"
            )
        else:
            # 非流式响应 - 模拟AI回复
            ai_response = await generate_ai_response(send_data, user_id)
            return Success(data=ai_response)
            
    except Exception as e:
        return Fail(msg=f"发送消息失败: {str(e)}")


async def generate_stream_response(send_data: SendDTO, user_id: int) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    try:
        # 模拟AI流式回复
        ai_response_text = f"这是对消息 '{send_data.messages[-1].content}' 的AI回复。"
        
        # 分块发送响应
        for i, char in enumerate(ai_response_text):
            chunk_data = {
                "id": f"chatcmpl-{i}",
                "object": "chat.completion.chunk",
                "choices": [{
                    "index": 0,
                    "delta": {"content": char},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
            await asyncio.sleep(0.05)  # 模拟延迟
        
        # 发送结束标记
        end_chunk = {
            "id": f"chatcmpl-end",
            "object": "chat.completion.chunk",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
        # 保存AI回复到数据库
        ai_message_create = ChatMessageCreate(
            session_id=int(send_data.session_id),
            user_id=user_id,
            role="assistant",
            content=ai_response_text,
            model_name=send_data.model,
            total_tokens=len(ai_response_text.split()),
            deduct_cost=0.001
        )
        await chat_controller.create_message(ai_message_create)
        
    except Exception as e:
        error_chunk = {
            "error": {
                "message": f"生成回复时出错: {str(e)}",
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def generate_ai_response(send_data: SendDTO, user_id: int) -> dict:
    """生成非流式AI回复"""
    try:
        # 模拟AI回复
        user_content = send_data.messages[-1].content
        ai_response_text = f"这是对消息 '{user_content}' 的AI回复。我理解您的问题，这里是我的回答。"
        
        # 保存AI回复到数据库
        ai_message_create = ChatMessageCreate(
            session_id=int(send_data.session_id),
            user_id=user_id,
            role="assistant",
            content=ai_response_text,
            model_name=send_data.model,
            total_tokens=len(ai_response_text.split()),
            deduct_cost=0.001
        )
        ai_message = await chat_controller.create_message(ai_message_create)
        
        return {
            "id": f"chatcmpl-{ai_message.id}",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": ai_response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_content.split()),
                "completion_tokens": len(ai_response_text.split()),
                "total_tokens": len(user_content.split()) + len(ai_response_text.split())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成AI回复失败: {str(e)}")


@router.get("/models", summary="获取可用模型列表")
async def get_available_models():
    """获取可用的聊天模型列表"""
    try:
        total, models = await model_controller.get_active_models(
            model_type="chat",
            page_size=100
        )
        
        model_list = []
        for model in models:
            model_dict = await model.to_dict()
            model_list.append({
                "id": model_dict["model_name"],
                "name": model_dict["model_show"],
                "description": model_dict["model_describe"],
                "price": model_dict["model_price"]
            })
        
        return Success(data=model_list)
        
    except Exception as e:
        return Fail(msg=f"获取模型列表失败: {str(e)}")
