from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator, Dict, List
from datetime import datetime

from app.controllers.chat import chat_controller
from app.controllers.model import model_controller
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas import Success, Fail
from app.schemas.chat import SendDTO, ChatMessageCreate
from app.utils.serializer import safe_serialize

# 导入Deepseek配置和autogen
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS
from autogen_agentchat.agents import AssistantAgent

router = APIRouter()

# 定义Deepseek模型信息
deepseek_model_info = ModelInfo(
    vision=False,  # 不支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

# Deepseek模型配置字典
DEEPSEEK_MODELS: Dict[str, ModelInfo] = {
    "deepseek-chat": deepseek_model_info,  # 将模型信息关联到deepseek-chat模型
}

# Deepseek模型的令牌限制
DEEPSEEK_TOKEN_LIMITS: Dict[str, int] = {
    "deepseek-chat": 128000,  # 设置最大令牌数为128000
}

# 更新全局模型信息和令牌限制
_MODEL_INFO.update(DEEPSEEK_MODELS)
_MODEL_TOKEN_LIMITS.update(DEEPSEEK_TOKEN_LIMITS)

# 创建OpenAI兼容的聊天完成客户端
model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",  # 使用的模型名称
    base_url="https://api.deepseek.com/v1",  # Deepseek API的基础URL
    api_key="sk-56f5743d59364543a00109a4c1c10a56",  # API密钥
    model_info=deepseek_model_info,  # 指定模型信息
)

# 创建支持流式输出的AssistantAgent
def create_assistant_agent():
    """创建支持流式输出的助手代理"""
    return AssistantAgent(
        "超级智能客服",
        model_client=model_client,
        model_client_stream=True,  # 启用流式输出
        system_message="你是超级智能客服，专业、友好、乐于助人。请用中文回复用户的问题。"
    )


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

        # 只支持流式响应
        return StreamingResponse(
            generate_stream_response(send_data, user_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
            
    except Exception as e:
        return Fail(msg=f"发送消息失败: {str(e)}")


async def generate_stream_response(send_data: SendDTO, user_id: int) -> AsyncGenerator[str, None]:
    """生成流式响应 - 使用autogen AssistantAgent"""
    try:
        # 构建用户任务内容
        user_task = ""
        if send_data.messages:
            # 获取最后一条用户消息
            for msg in reversed(send_data.messages):
                if msg.role == "user" and msg.content:
                    user_task = msg.content
                    break

        if not user_task:
            user_task = "你好"

        # 创建助手代理
        agent = create_assistant_agent()

        full_response = ""
        chunk_id = f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # 使用autogen的流式输出
            async for message in agent.run_stream(task=user_task):
                # 提取消息内容
                content = ""
                if hasattr(message, 'content'):
                    content = str(message.content)
                elif hasattr(message, 'text'):
                    content = str(message.text)
                else:
                    content = str(message)

                # 过滤用户消息回显和重复内容
                if content and content.strip():
                    # 跳过与用户输入相同的内容
                    if content.strip() == user_task.strip():
                        continue

                    # 跳过包含用户输入的内容
                    if user_task.strip() in content.strip():
                        continue

                    # 跳过已经发送过的内容（避免重复）
                    if content in full_response:
                        continue

                    # 检查是否是来自用户的消息（通过消息属性判断）
                    if hasattr(message, 'source') and message.source == 'user':
                        continue

                    # 跳过空白或无意义的内容
                    if len(content.strip()) < 2:
                        continue

                    full_response += content

                    # 构造OpenAI格式的流式响应
                    chunk_data = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": send_data.model or "deepseek-chat",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"

        except Exception as api_error:
            # 如果autogen调用失败，使用备用响应
            print(f"AutoGen流式调用失败: {api_error}")
            fallback_response = f"我是超级智能客服，很高兴为您服务！\n\n您的问题：{user_task}\n\n我正在为您查找相关信息，请稍等..."

            # 分块发送备用响应
            for char in fallback_response:
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": send_data.model or "deepseek-chat",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": char},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.03)  # 模拟打字效果

            full_response = fallback_response

        # 发送结束标记
        end_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": send_data.model or "deepseek-chat",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

        # 保存AI回复到数据库
        if full_response and send_data.session_id:
            ai_message_create = ChatMessageCreate(
                session_id=int(send_data.session_id),
                user_id=user_id,
                role="assistant",
                content=full_response,
                model_name=send_data.model or "deepseek-chat",
                total_tokens=len(full_response.split()),
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
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"





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
                "price": safe_serialize(model_dict["model_price"])
            })
        
        return Success(data=model_list)
        
    except Exception as e:
        return Fail(msg=f"获取模型列表失败: {str(e)}")
