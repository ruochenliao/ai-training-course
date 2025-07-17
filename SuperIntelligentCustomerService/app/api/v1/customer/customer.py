import json
import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from ....core.dependency import DependAuth
from ....models.admin import User
from ....schemas.customer import ChatRequest, ChatMessage, SessionRequest, SessionResponse, MessageContent, \
    ImageContent, MultiModalContent
from ....services.chat_service import ChatService
from ....services.session_service import SessionService
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

        # 保存用户消息到会话
        if request.session_id:
            # 添加用户消息到会话
            user_message = request.messages[-1]
            session_service.add_message(request.session_id, user_message)

        async def response_generator():
            assistant_response = ""
            async for chunk in chat_service.chat_stream(
                messages=request.messages,
                user_id=str(current_user.id),
                session_id=request.session_id
            ):
                # 确保每个chunk立即发送
                if chunk:  # 确保chunk不为空
                    assistant_response += chunk
                    encoded_chunk = json.dumps({"content": chunk})
                    yield f"data: {encoded_chunk}\n\n"
            # 保存AI回复到会话
            if request.session_id and assistant_response:
                assistant_message = ChatMessage(role="assistant", content=assistant_response)
                session_service.add_message(request.session_id, assistant_message)

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


@router.post("/session/create", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    current_user: User = DependAuth
):
    """创建新的聊天会话"""
    try:
        session_data = session_service.create_session(request.user_id or str(current_user.id))
        return SessionResponse(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            created_at=session_data["created_at"],
            last_active=session_data["last_active"],
            messages=session_data["messages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = DependAuth
):
    """获取会话信息和历史消息"""
    try:
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")

        return SessionResponse(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            created_at=session_data["created_at"],
            last_active=session_data["last_active"],
            messages=session_data["messages"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions(
    user_id: str,
    current_user: User = DependAuth
):
    """获取用户的所有会话"""
    try:
        sessions_data = session_service.get_user_sessions(user_id)
        return [
            SessionResponse(
                session_id=session["session_id"],
                user_id=session["user_id"],
                created_at=session["created_at"],
                last_active=session["last_active"],
                messages=session["messages"]
            ) for session in sessions_data
        ]
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

        return {
            "url": image_url,
            "file_name": file.filename,
            "content_type": file.content_type,
            "size": os.path.getsize(file_path)
        }
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
