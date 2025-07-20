import json
import os
import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
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
    request: ChatRequest,
    current_user: User = DependAuth
):
    """客户服务流式聊天API"""
    try:
        chat_service = ChatService()

        # 保存用户消息到会话和数据库
        if request.session_id:
            # 添加用户消息到会话
            user_message = request.messages[-1]
            session_service.add_message(request.session_id, user_message)

            # 同时保存到数据库
            try:
                await ChatMessageModel.create(
                    session_id=request.session_id,
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
                messages=request.messages,
                user_id=str(current_user.id),
                session_id=request.session_id
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
                        "session_id": request.session_id,
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
                "session_id": request.session_id,
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
            if request.session_id and assistant_response:
                assistant_message = ChatMessage(role="assistant", content=assistant_response)
                session_service.add_message(request.session_id, assistant_message)

                # 同时保存到数据库
                try:
                    await ChatMessageModel.create(
                        session_id=request.session_id,
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


