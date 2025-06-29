"""
对话API端点 - 企业级RAG系统
严格按照技术栈要求：/api/v1/conversations/ AutoGen智能体对话模块
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app import autogen_service
from app import deepseek_llm_service
from app import multimodal_conversation_service
from app import qwen_multimodal_service
from app.core import get_current_user
from app.core import get_db_session
from app.models import User, Conversation, Message, MessageRole, ContentType

router = APIRouter(prefix="/conversations", tags=["conversations"])


# Pydantic 模型
class ConversationCreate(BaseModel):
    """创建对话请求"""
    knowledge_base_id: Optional[int] = None
    title: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    search_mode: str = Field(default="auto", regex="^(semantic|hybrid|graph|auto)$")


class MessageSend(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1)
    use_agents: bool = True
    stream: bool = False


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    content_type: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """对话响应"""
    id: int
    title: Optional[str]
    knowledge_base_id: Optional[int]
    agent_config: Dict[str, Any]
    search_mode: str
    is_active: bool
    created_at: str
    updated_at: str
    message_count: int


class ImageUpload(BaseModel):
    """图像上传"""
    image_data: str  # base64编码
    filename: str
    prompt: Optional[str] = None


@router.post("/", response_model=Dict[str, Any])
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建新对话"""
    try:
        result = await multimodal_conversation_service.create_conversation(
            user_id=current_user.id,
            knowledge_base_id=request.knowledge_base_id,
            agent_config=request.agent_config
        )
        
        if result["success"]:
            return {
                "success": True,
                "conversation_id": result["conversation_id"],
                "autogen_enabled": result["autogen_enabled"],
                "multimodal_enabled": result["multimodal_enabled"],
                "message": "对话创建成功"
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取对话列表"""
    try:
        # TODO: 实现对话列表查询逻辑
        # 这里需要查询Conversation表
        
        return []
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取对话详情"""
    try:
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        
        if "error" in conv_info:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 检查权限
        if conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        return conv_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")


@router.post("/{conversation_id}/messages", response_model=Dict[str, Any])
async def send_message(
    conversation_id: str,
    request: MessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """发送消息"""
    try:
        # 验证对话权限
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        if "error" in conv_info or conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 发送消息
        result = await multimodal_conversation_service.send_message(
            conversation_id=conversation_id,
            content=request.content,
            use_agents=request.use_agents
        )
        
        if result["success"]:
            return {
                "success": True,
                "response": result["response"],
                "processing_time_ms": result["processing_time_ms"],
                "agent_used": result["agent_used"],
                "metadata": result.get("metadata", {})
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "response": result.get("response", "处理失败")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: str,
    request: MessageSend,
    current_user: User = Depends(get_current_user)
):
    """流式发送消息"""
    try:
        # 验证对话权限
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        if "error" in conv_info or conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        async def generate_stream():
            try:
                # 使用DeepSeek LLM的流式接口
                async for chunk in deepseek_llm_service.chat_completion(
                    messages=[{"role": "user", "content": request.content}],
                    stream=True
                ):
                    if chunk["success"] and chunk.get("content"):
                        yield f"data: {chunk['content']}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"流式响应生成失败: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式消息发送失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式消息发送失败: {str(e)}")


@router.post("/{conversation_id}/images", response_model=Dict[str, Any])
async def upload_image(
    conversation_id: str,
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """上传图像并分析"""
    try:
        # 验证对话权限
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        if "error" in conv_info or conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 读取图像数据
        image_data = await file.read()
        
        # 验证图像
        is_valid, error_msg = qwen_multimodal_service._validate_image(image_data, file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 分析图像
        if prompt:
            result = await qwen_multimodal_service.image_qa(
                image_data, prompt, filename=file.filename
            )
        else:
            result = await qwen_multimodal_service.describe_image_for_search(
                image_data, filename=file.filename
            )
        
        if result["success"]:
            # 发送包含图像分析的消息
            attachments = [{
                "type": "image",
                "filename": file.filename,
                "data": image_data
            }]
            
            message_content = prompt or "请分析这张图片"
            
            chat_result = await multimodal_conversation_service.send_message(
                conversation_id=conversation_id,
                content=message_content,
                content_type=ContentType.MIXED,
                attachments=attachments,
                use_agents=True
            )
            
            return {
                "success": True,
                "image_analysis": result["content"],
                "chat_response": chat_result["response"] if chat_result["success"] else None,
                "processing_time_ms": result["latency_ms"]
            }
        else:
            raise HTTPException(status_code=500, detail=f"图像分析失败: {result['error']}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像上传分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"图像上传分析失败: {str(e)}")


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取对话消息"""
    try:
        # 验证对话权限
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        if "error" in conv_info or conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # TODO: 实现消息查询逻辑
        # 这里需要查询Message表
        
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除对话"""
    try:
        # 验证对话权限
        conv_info = await multimodal_conversation_service.get_conversation_info(conversation_id)
        if "error" in conv_info or conv_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # TODO: 实现对话删除逻辑
        # 1. 删除消息记录
        # 2. 删除对话记录
        # 3. 清理AutoGen群聊
        
        return {
            "success": True,
            "message": "对话删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")


@router.get("/health")
async def health_check():
    """对话服务健康检查"""
    try:
        health = await multimodal_conversation_service.health_check()
        
        if health["status"] == "healthy":
            return health
        else:
            return health
            
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# WebSocket 支持 (实时对话)
@router.websocket("/ws/{conversation_id}")
async def websocket_conversation(websocket: WebSocket, conversation_id: str):
    """WebSocket实时对话"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_content = data.get("content", "")
            use_agents = data.get("use_agents", True)
            
            if not message_content:
                await websocket.send_json({
                    "error": "消息内容不能为空"
                })
                continue
            
            # 处理消息
            try:
                result = await multimodal_conversation_service.send_message(
                    conversation_id=conversation_id,
                    content=message_content,
                    use_agents=use_agents
                )
                
                # 发送响应
                await websocket.send_json({
                    "success": result["success"],
                    "response": result.get("response", ""),
                    "processing_time_ms": result.get("processing_time_ms", 0),
                    "agent_used": result.get("agent_used", False),
                    "metadata": result.get("metadata", {})
                })
                
            except Exception as e:
                await websocket.send_json({
                    "success": False,
                    "error": str(e),
                    "response": "处理消息时出现错误"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        await websocket.close()
