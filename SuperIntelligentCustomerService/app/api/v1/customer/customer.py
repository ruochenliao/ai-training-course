import base64
import json
import os
import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse

from app.controllers.chat_service import ChatService
from app.controllers.session_service import SessionService
from ....core.dependency import DependAuth
from ....models.admin import User, ChatMessage as ChatMessageModel
from ....schemas.base import Success
from ....schemas.customer import ChatRequest, ChatMessage, MessageContent, \
    ImageContent, MultiModalContent
from ....settings.config import settings

router = APIRouter()

# 初始化服务
session_service = SessionService()

# 确保上传目录存在
UPLOADS_DIR = os.path.join(settings.BASE_DIR, "data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/chat/stream", response_model=None)
async def customer_chat_stream(
    request: Request,
    current_user: User = DependAuth
):
    """客户服务流式聊天API"""
    try:
        # 解析请求数据，支持JSON和FormData两种格式
        content_type = request.headers.get("content-type", "")

        if content_type.startswith("application/json"):
            # JSON格式
            request_data = await request.json()
            chat_request = ChatRequest(**request_data)
        elif content_type.startswith("multipart/form-data"):
            # FormData格式（有文件上传）
            form = await request.form()

            # 解析消息
            messages_str = form.get("messages")
            if not messages_str:
                raise HTTPException(status_code=422, detail="Missing messages field")

            messages_data = json.loads(messages_str)
            messages = [ChatMessage(**msg) for msg in messages_data]

            # 构建ChatRequest对象
            chat_request = ChatRequest(
                messages=messages,
                session_id=form.get("session_id"),
                model=form.get("model"),
                system_prompt=form.get("system_prompt"),
                user_id=form.get("user_id", str(current_user.id))
            )

            # 处理文件（如果有的话）
            files = form.getlist("files")
            if files:
                print(f"收到 {len(files)} 个文件")

                # 处理图片文件，将其添加到最后一条用户消息中
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if last_message.role == "user":
                        # 创建多模态内容列表
                        multimodal_contents = []

                        # 添加文本内容
                        if isinstance(last_message.content, str):
                            multimodal_contents.append(MultiModalContent(text=last_message.content))
                        elif isinstance(last_message.content, MessageContent) and last_message.content.text:
                            multimodal_contents.append(MultiModalContent(text=last_message.content.text))

                        # 处理每个文件
                        for file in files:
                            if file.filename and file.content_type and file.content_type.startswith('image/'):
                                try:
                                    # 读取文件内容
                                    file_content = await file.read()

                                    # 创建图片内容
                                    image_content = ImageContent(
                                        url=f"data:{file.content_type};base64,{base64.b64encode(file_content).decode()}",
                                        file_name=file.filename
                                    )

                                    # 添加到多模态内容
                                    multimodal_contents.append(MultiModalContent(image=image_content))

                                    print(f"处理图片文件: {file.filename}, 大小: {len(file_content)} bytes")

                                except Exception as e:
                                    print(f"处理文件 {file.filename} 时出错: {e}")

                        # 更新消息内容为多模态格式
                        if len(multimodal_contents) > 0:  # 有内容（文本和/或图片）
                            new_content = MessageContent(
                                type="multi-modal",
                                content=multimodal_contents,
                                task="图片分析"
                            )
                            messages[-1] = ChatMessage(role="user", content=new_content)

                            # 更新ChatRequest中的消息
                            chat_request = ChatRequest(
                                messages=messages,
                                session_id=form.get("session_id"),
                                model=form.get("model"),
                                system_prompt=form.get("system_prompt"),
                                user_id=form.get("user_id", str(current_user.id))
                            )
        else:
            raise HTTPException(status_code=422, detail="Unsupported content type")

        chat_service = ChatService()

        # 保存用户消息到会话和数据库
        if chat_request.session_id:
            # 添加用户消息到会话
            user_message = chat_request.messages[-1]
            session_service.add_message(chat_request.session_id, user_message)

            # 同时保存到数据库
            try:
                await ChatMessageModel.create(
                    session_id=chat_request.session_id,
                    user_id=current_user.id,
                    role="user",
                    content=user_message.content if isinstance(user_message.content, str) else str(user_message.content),
                    model_name=None,
                    total_tokens=0,
                    deduct_cost=0,
                    remark="用户消息"
                )
            except Exception as e:
                print(f"保存用户消息到数据库失败: {e}")

        async def response_generator():
            assistant_response = ""
            chunk_index = 0

            async for chunk in chat_service.chat_stream(
                messages=chat_request.messages,
                user_id=str(current_user.id),
                session_id=chat_request.session_id
            ):
                # 确保每个chunk立即发送
                if chunk:  # 确保chunk不为空
                    assistant_response += chunk
                    chunk_index += 1

                    # 构建完整的流式事件格式
                    stream_event = {
                        "id": f"chunk_{chunk_index}_{int(datetime.now().timestamp() * 1000)}",
                        "type": "content",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": chat_request.session_id,
                        "user_id": current_user.id,
                        "model_name": "DeepSeek VL Chat",
                        "data": {"content": chunk},
                        "chunk_index": chunk_index,
                        "is_markdown": True
                    }

                    # 确保中文字符正确编码，不使用 ASCII 转义
                    encoded_chunk = json.dumps(stream_event, ensure_ascii=False)
                    yield f"data: {encoded_chunk}\n\n"
            # 发送完成事件
            complete_event = {
                "id": f"complete_{int(datetime.now().timestamp() * 1000)}",
                "type": "complete",
                "timestamp": datetime.now().isoformat(),
                "session_id": chat_request.session_id,
                "user_id": current_user.id,
                "model_name": "DeepSeek VL Chat",
                "data": {"total_chunks": chunk_index, "total_content": assistant_response},
                "is_markdown": True
            }
            encoded_complete = json.dumps(complete_event, ensure_ascii=False)
            yield f"data: {encoded_complete}\n\n"

            # 发送结束标记
            yield "data: [DONE]\n\n"

            # 保存AI回复到会话和数据库
            if chat_request.session_id and assistant_response:
                assistant_message = ChatMessage(role="assistant", content=assistant_response)
                session_service.add_message(chat_request.session_id, assistant_message)

                # 同时保存到数据库
                try:
                    await ChatMessageModel.create(
                        session_id=chat_request.session_id,
                        user_id=current_user.id,
                        role="assistant",
                        content=assistant_response,
                        model_name="DeepSeek VL Chat",  # 可以从配置中获取
                        total_tokens=0,  # 这里可以计算实际的token数
                        deduct_cost=0,   # 这里可以计算实际的费用
                        remark="AI回复"
                    )
                except Exception as e:
                    print(f"保存AI回复到数据库失败: {e}")

        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
            }
        )
    except Exception as e:
        print(f"❌ 聊天流式接口错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat/upload-image")
async def customer_upload_image(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    current_user: User = DependAuth
):
    """客户服务上传图片到聊天会话"""
    try:
        user_id = str(current_user.id)
        
        # 检查文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只能上传图片文件")

        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1] if "." in file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        # 创建用户目录
        user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(user_upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 生成图片URL
        image_url = f"/api/v1/customer/chat/images/{user_id}/{unique_filename}"

        # 如果有会话 ID，将图片消息添加到会话
        if session_id:
            # 创建多模态消息，参考AutoGen的MultiModalMessage格式
            image_item = MultiModalContent(
                image=ImageContent(
                    url=image_url,
                    file_name=file.filename
                )
            )

            image_content = MessageContent(
                type="multi-modal",
                content=[image_item],
                task="image_understanding"  # 默认任务类型
            )

            message = ChatMessage(role="user", content=image_content)
            session_service.add_message(session_id, message)

        data = {
            "url": image_url,
            "file_name": file.filename,
            "content_type": file.content_type,
            "size": os.path.getsize(file_path)
        }
        return Success(data=data, msg="图片上传成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/images/{user_id}/{image_name}")
async def customer_get_image(user_id: str, image_name: str):
    """获取客户服务上传的图片"""
    try:
        image_path = os.path.join(UPLOADS_DIR, user_id, image_name)
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图片不存在")

        # 根据文件扩展名确定内容类型
        file_ext = os.path.splitext(image_name)[1].lower()
        content_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp"
        }.get(file_ext, "application/octet-stream")

        return StreamingResponse(
            open(image_path, "rb"),
            media_type=content_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


