"""
聊天服务API端点
基于AutoGen框架的智能体聊天服务接口
支持文本和多模态内容的智能识别和处理
集成记忆功能，提供上下文感知的智能对话
标准化实现，参考roles.py模式
"""
import logging
from io import BytesIO
from typing import AsyncGenerator

import PIL.Image
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS
from fastapi import APIRouter, Request, Query, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....controllers.chat_session import ChatSession
from ....controllers.message_manager import message_manager
from ....controllers.model import model_controller
from ....core.dependency import DependAuth
from ....models.admin import User
from ....schemas import Success, Fail, SuccessExtra
from ....schemas.chat_service import *
from ....utils.encryption import decrypt_api_key, is_api_key_encrypted
from ....utils.serializer import safe_serialize

logger = logging.getLogger(__name__)

router = APIRouter()

# 默认模型信息配置
DEFAULT_TEXT_MODEL_INFO = ModelInfo(
    vision=False,  # 不支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

DEFAULT_VISION_MODEL_INFO = ModelInfo(
    vision=True,  # 支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

# 默认令牌限制
DEFAULT_TOKEN_LIMIT = 128000


class SmartChatSystem:
    """智能聊天系统 - 使用ChatSession管理会话，集成记忆功能"""

    def __init__(self):
        # 会话管理
        self.sessions = {}  # session_key -> ChatSession
        self.session_timeout_minutes = 30

        # 模型管理
        self.current_text_model = None
        self.current_vision_model = None

        # 记忆功能
        self.memory_enabled = True

    def _get_session_key(self, user_id: int, session_id: str = None) -> str:
        """生成会话键"""
        if session_id:
            return f"{user_id}_{session_id}"
        return f"{user_id}_default"

    async def get_or_create_session(
        self,
        user_id: int,
        session_id: str = None,
        text_model_name: str = None,
        vision_model_name: str = None
    ) -> ChatSession:
        """获取或创建聊天会话"""
        session_key = self._get_session_key(user_id, session_id)

        # 检查现有会话
        if session_key in self.sessions:
            session = self.sessions[session_key]
            if not session.is_expired(self.session_timeout_minutes):
                session.update_activity()
                return session
            else:
                # 会话过期，清理
                await session.close()
                del self.sessions[session_key]

        # 创建新会话
        try:
            # 获取模型客户端
            text_model_client = await self.get_model_client(
                model_name=text_model_name,
                vision_support=False
            )
            vision_model_client = await self.get_model_client(
                model_name=vision_model_name,
                vision_support=True
            )

            # 创建会话
            session = ChatSession(
                user_id=user_id,
                session_id=session_id or "default",
                text_model_client=text_model_client,
                vision_model_client=vision_model_client
            )

            self.sessions[session_key] = session
            logger.info(f"创建新会话: {session_key}")
            return session

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise

    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_keys = []
        for session_key, session in self.sessions.items():
            if session.is_expired(self.session_timeout_minutes):
                expired_keys.append(session_key)

        for key in expired_keys:
            try:
                await self.sessions[key].close()
                del self.sessions[key]
                logger.info(f"清理过期会话: {key}")
            except Exception as e:
                logger.error(f"清理会话失败: {e}")

    def get_session_stats(self) -> dict:
        """获取会话统计信息"""
        active_sessions = len(self.sessions)
        session_details = []

        for session_key, session in self.sessions.items():
            session_details.append({
                "key": session_key,
                "user_id": session.user_id,
                "session_id": session.session_id,
                "message_count": session.message_count,
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active
            })

        return {
            "active_sessions": active_sessions,
            "session_details": session_details
        }

    def _update_model_info(self, model_name: str, vision_support: bool):
        """更新模型信息到全局缓存"""
        model_info = DEFAULT_VISION_MODEL_INFO if vision_support else DEFAULT_TEXT_MODEL_INFO
        if model_name not in _MODEL_INFO:
            _MODEL_INFO[model_name] = model_info
        if model_name not in _MODEL_TOKEN_LIMITS:
            _MODEL_TOKEN_LIMITS[model_name] = DEFAULT_TOKEN_LIMIT
        return model_info

    def _create_model_client(self, model_name: str, api_host: str, api_key: str, model_info):
        """创建模型客户端"""
        return OpenAIChatCompletionClient(
            model=model_name,
            base_url=api_host,
            api_key=api_key,
            model_info=model_info,
        )

    def _get_default_config(self, vision_support: bool):
        """获取默认模型配置"""
        return {
            "model_name": "gpt-3.5-turbo",
            "api_host": "https://api.openai.com/v1",
            "api_key": "sk-default-key"
        }

    async def _get_model_config(self, model_name: str = None, vision_support: bool = False):
        """获取模型配置"""
        if not model_name:
            # 根据是否需要视觉支持选择默认模型
            model_type = "multimodal" if vision_support else "chat"
            default_model = await model_controller.model.filter(
                is_active=True,
                model_type=model_type
            ).first()

            if not default_model:
                logger.warning("数据库中没有找到可用模型，使用默认配置")
                return self._get_default_config(vision_support)

            # 验证API密钥必须是加密的
            if not is_api_key_encrypted(default_model.api_key):
                raise Exception(f"模型 {default_model.model_name} 的API密钥未加密")

            return {
                "model_name": default_model.model_name,
                "api_host": default_model.api_host,
                "api_key": decrypt_api_key(default_model.api_key)
            }
        else:
            # 根据模型名称获取配置
            try:
                model_config = await model_controller.get_model_by_name(model_name)
                if not model_config:
                    raise Exception(f"模型 {model_name} 不存在或未启用")

                # 验证API密钥必须是加密的
                if not is_api_key_encrypted(model_config.api_key):
                    raise Exception(f"模型 {model_name} 的API密钥未加密")

                return {
                    "model_name": model_name,
                    "api_host": model_config.api_host,
                    "api_key": decrypt_api_key(model_config.api_key)
                }
            except Exception:
                logger.warning(f"获取模型 {model_name} 配置失败，使用默认配置")
                default_config = self._get_default_config(vision_support)
                default_config["model_name"] = model_name  # 保持用户指定的模型名
                return default_config

    async def get_model_client(self, model_name: str = None, vision_support: bool = False):
        """动态获取模型客户端"""
        try:
            # 获取模型配置
            config = await self._get_model_config(model_name, vision_support)

            # 更新模型信息并创建客户端
            model_info = self._update_model_info(config["model_name"], vision_support)
            return self._create_model_client(
                config["model_name"],
                config["api_host"],
                config["api_key"],
                model_info
            )
        except Exception as e:
            logger.error(f"创建模型客户端失败: {e}")
            # 使用默认配置创建客户端
            default_config = self._get_default_config(vision_support)
            model_info = self._update_model_info(default_config["model_name"], vision_support)
            return self._create_model_client(
                default_config["model_name"],
                default_config["api_host"],
                default_config["api_key"],
                model_info
            )

    # 保留模型客户端创建方法，供ChatSession使用

    async def process_message(self, message: str, files: List[UploadFile] = None, model_name: str = None, user_id: int = None, session_id: str = None) -> AsyncGenerator[str, None]:
        """处理消息并生成流式响应，使用ChatSession管理"""
        try:
            # 清理过期会话
            await self.cleanup_expired_sessions()

            # 获取或创建会话
            session = await self.get_or_create_session(
                user_id=user_id,
                session_id=session_id,
                text_model_name=model_name if not files else None,
                vision_model_name=model_name if files else None
            )

            # 使用会话处理消息
            async for chunk in session.send_message(message, files):
                yield chunk

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            yield f"抱歉，处理您的请求时出现了错误：{str(e)}"

    def detect_multimodal_content(self, message: str, files: List[UploadFile] = None) -> bool:
        """检测是否包含多模态内容"""
        # 检查是否有文件上传
        if files and len(files) > 0:
            return True

        # 检查文本中是否提到图片、视频等
        multimodal_keywords = [
            '图片', '照片', '图像', '截图', '视频', '录像',
            'image', 'photo', 'picture', 'video', 'screenshot'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in multimodal_keywords)

    async def create_multimodal_message(self, text: str, files: List[UploadFile]) -> MultiModalMessage:
        """创建多模态消息"""
        content = [text]  # 文本内容

        for file in files:
            try:
                # 读取文件内容
                file_content = await file.read()

                # 检查文件类型
                if file.content_type and file.content_type.startswith('image/'):
                    # 处理图片文件
                    pil_image = PIL.Image.open(BytesIO(file_content))
                    img = Image(pil_image)
                    content.append(img)
                    logger.info(f"添加图片到多模态消息: {file.filename}")
                else:
                    logger.warning(f"不支持的文件类型: {file.content_type}")

            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")

        return MultiModalMessage(content=content, source="user")


# 全局智能聊天系统实例
smart_chat_system = SmartChatSystem()


@router.post("/send", summary="发送聊天消息（支持多模态）")
async def send_chat_message(
    request: Request,
    current_user: User = DependAuth
):
    """
    发送聊天消息并获取AI回复（统一接口）
    支持三种输入方式：
    1. JSON格式：纯文本消息
    2. Form格式：支持文件上传（多模态消息）
    3. Form格式：纯文本消息（兼容性）
    智能识别内容类型并选择合适的处理方式
    只支持流式响应
    """
    try:
        content_type = request.headers.get("content-type", "")
        logger.info(f"收到请求，Content-Type: {content_type}")

        # 解析请求数据
        message_data = await _parse_request_data(request, content_type)
        if not message_data:
            return Fail(msg="请求数据解析失败")

        # 验证消息内容
        if not message_data.get("message") or not message_data["message"].strip():
            return Fail(msg="消息内容不能为空")

        # 返回流式响应
        return StreamingResponse(
            _generate_stream_response(
                message=message_data["message"],
                session_id=message_data.get("session_id"),
                files=message_data.get("files", []),
                model_name=message_data.get("model_name"),
                user_id=current_user.id
            ),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲，确保流式响应实时传输
            }
        )

    except Exception as e:
        logger.error(f"发送聊天消息失败: {e}")
        return Fail(msg=f"发送消息失败: {str(e)}")


async def _parse_request_data(request: Request, content_type: str) -> Optional[dict]:
    """解析请求数据的辅助函数"""
    try:
        if "application/json" in content_type:
            # JSON格式输入（纯文本）
            json_data = await request.json()
            logger.info(f"解析JSON数据: {json_data}")

            # 验证数据格式
            if "messages" in json_data and json_data["messages"]:
                # 获取用户消息
                user_message = None
                for msg in reversed(json_data["messages"]):
                    if msg.get("role") == "user":
                        user_message = msg
                        break

                if user_message and user_message.get("content"):
                    return {
                        "message": user_message["content"].strip(),
                        "session_id": json_data.get("session_id"),
                        "model_name": json_data.get("model_name"),
                        "files": []
                    }
            elif "message" in json_data:
                # 简单消息格式
                return {
                    "message": json_data["message"].strip(),
                    "session_id": json_data.get("session_id"),
                    "model_name": json_data.get("model_name"),
                    "files": []
                }

        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            # Form格式输入（支持多模态）
            form_data = await request.form()
            message = form_data.get("message")

            if message and message.strip():
                # 处理上传的文件
                uploaded_files = []
                files = form_data.getlist("files")
                for file in files:
                    if hasattr(file, 'filename') and file.filename:
                        # 验证文件类型
                        if file.content_type and not file.content_type.startswith('image/'):
                            logger.warning(f"不支持的文件类型: {file.content_type}")
                            continue
                        uploaded_files.append(file)

                # 处理 session_id 类型转换
                session_id = form_data.get("session_id")
                if session_id:
                    try:
                        session_id = int(session_id)
                    except (ValueError, TypeError):
                        logger.warning(f"无效的session_id格式: {session_id}")
                        session_id = None

                return {
                    "message": message.strip(),
                    "session_id": session_id,
                    "model_name": form_data.get("model_name"),
                    "files": uploaded_files
                }

        return None
    except Exception as e:
        logger.error(f"解析请求数据失败: {e}")
        return None


async def _generate_stream_response(
        message: str,
        session_id: Optional[str],
        files: List[UploadFile],
        model_name: Optional[str],
        user_id: int
) -> AsyncGenerator[str, None]:
    """生成优化的流式响应，包含完整的元数据和状态信息"""
    import json
    import time
    from datetime import datetime

    message_id = f"msg_{int(time.time() * 1000)}"
    start_time = datetime.now()

    def create_stream_event(event_type: str, data: any = None, **kwargs) -> str:
        """创建标准化的流式事件"""
        event = {
            "id": message_id,
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "model_name": model_name or "smart-chat-system",
            **kwargs
        }
        if data is not None:
            event["data"] = data
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    try:
        # 发送开始事件
        yield create_stream_event("start", {"message": "开始处理您的请求..."})

        # 保存用户消息到数据库
        if session_id:
            try:
                from ....schemas.chat_service import ChatServiceMessage

                # 安全地转换session_id为整数
                try:
                    if isinstance(session_id, int):
                        session_id_int = session_id
                    elif isinstance(session_id, str) and session_id.isdigit():
                        session_id_int = int(session_id)
                    else:
                        session_id_int = 1
                except (ValueError, AttributeError):
                    session_id_int = 1

                user_message_create = ChatServiceMessage(
                    session_id=session_id_int,
                    user_id=user_id,
                    role="user",
                    content=message,
                    model_name="smart-agent",
                    total_tokens=0,
                    deduct_cost=0
                )
                await message_manager.create_message(user_message_create)
                yield create_stream_event("user_message_saved", {"status": "success"})
            except Exception as save_error:
                logger.warning(f"保存用户消息失败: {save_error}")
                yield create_stream_event("user_message_saved", {"status": "failed", "error": str(save_error)})

        # 发送处理状态
        yield create_stream_event("processing", {"message": "AI正在思考中..."})

        # 使用智能聊天系统处理消息（集成记忆功能）
        full_response = ""
        chunk_count = 0

        async for content in smart_chat_system.process_message(message, files, model_name, user_id, session_id):
            if content.strip():
                full_response += content
                chunk_count += 1

                # 发送内容块事件
                yield create_stream_event(
                    "content",
                    content,
                    chunk_index=chunk_count,
                    total_length=len(full_response),
                    is_markdown=True
                )

        # 发送完成事件
        processing_time = (datetime.now() - start_time).total_seconds()
        yield create_stream_event(
            "complete",
            {
                "full_content": full_response,
                "total_chunks": chunk_count,
                "processing_time": processing_time,
                "word_count": len(full_response.split()),
                "char_count": len(full_response)
            }
        )

        # 保存AI回复到数据库
        if session_id and full_response:
            try:
                # 安全地转换session_id为整数
                try:
                    if isinstance(session_id, int):
                        session_id_int = session_id
                    elif isinstance(session_id, str) and session_id.isdigit():
                        session_id_int = int(session_id)
                    else:
                        session_id_int = 1
                except (ValueError, AttributeError):
                    session_id_int = 1

                ai_message_create = ChatMessageCreate(
                    session_id=session_id_int,
                    user_id=user_id,
                    role="assistant",
                    content=full_response.strip(),
                    model_name="smart-chat-system",
                    total_tokens=len(full_response.split()),
                    deduct_cost=0.001
                )
                await message_manager.create_message(ai_message_create)
                yield create_stream_event("ai_message_saved", {"status": "success"})
            except Exception as save_error:
                logger.warning(f"保存AI回复失败: {save_error}")
                yield create_stream_event("ai_message_saved", {"status": "failed", "error": str(save_error)})

        # 发送结束标记
        yield create_stream_event("done", {"message": "处理完成"})

    except Exception as e:
        logger.error(f"流式响应生成失败: {e}")
        # 发送错误事件
        yield create_stream_event(
            "error",
            {
                "message": f"抱歉，处理您的请求时出现了错误：{str(e)}",
                "error_type": type(e).__name__,
                "recoverable": True
            }
        )
        yield create_stream_event("done", {"message": "处理结束（出现错误）"})


@router.get("/session/get", summary="获取会话信息")
async def get_session_info(
        session_id: int = Query(..., description="会话ID"),
        current_user: User = DependAuth
):
    """获取指定会话的信息"""
    try:
        from ....controllers.session import session_controller

        session = await session_controller.get_user_session(session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        session_dict = await session.to_dict()
        return Success(data=session_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")


@router.get("/session/list", summary="获取用户会话列表")
async def list_user_sessions(
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, description="每页数量"),
        current_user: User = DependAuth
):
    """获取当前用户的会话列表"""
    try:
        from ....controllers.session import session_controller

        total, sessions = await session_controller.get_user_sessions(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # 转换为标准格式
        session_list = []
        for session in sessions:
            session_dict = await session.to_dict()
            session_list.append({
                "id": str(session_dict["id"]),
                "title": session_dict.get("session_title", "新对话"),
                "updated_at": session_dict.get("updated_at")
            })

        return SuccessExtra(data=session_list, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.delete("/session/delete", summary="删除会话")
async def delete_session(
        session_id: int = Query(..., description="会话ID"),
        current_user: User = DependAuth
):
    """删除指定的会话"""
    try:
        from ....controllers.session import session_controller

        deleted_count = await session_controller.delete_user_sessions(
            [session_id],
            current_user.id
        )

        if deleted_count > 0:
            return Success(msg="会话删除成功")
        else:
            raise HTTPException(status_code=404, detail="会话不存在或无权限删除")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.post("/session/create", summary="创建新会话")
async def create_session(
        session_in: SessionCreate,
        current_user: User = DependAuth
):
    """创建新的聊天会话"""
    try:
        from ....controllers.session import session_controller
        from ....schemas.session import SessionCreate as SessionCreateSchema

        session_data = SessionCreateSchema(
            session_title=session_in.session_title,
            user_id=current_user.id,
            session_content=""
        )

        new_session = await session_controller.create_user_session(session_data)
        session_dict = await new_session.to_dict()

        return Success(data={
            "session_id": str(session_dict["id"]),
            "session_title": session_dict["session_title"],
            "user_id": session_dict["user_id"],
            "created_at": session_dict["created_at"]
        }, msg="会话创建成功")

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/stats", summary="获取服务统计")
async def get_service_stats(
        current_user: User = DependAuth
):
    """获取多智能体聊天服务统计信息（管理员功能）"""
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")

        from ....controllers.session import session_controller

        # 获取会话统计
        total_sessions, _ = await session_controller.get_user_sessions(
            user_id=None,  # 获取所有用户的会话
            page=1,
            page_size=1
        )

        # 获取消息统计
        total_messages = await message_manager.get_total_message_count()

        stats_data = ServiceStats(
            total_sessions=total_sessions,
            total_messages=total_messages,
            agent_system="smart-chat-system",
            agents=["text_agent", "vision_agent"],
            features=["流式响应", "多模态识别", "智能选择"]
        )

        return Success(data=stats_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务统计失败: {str(e)}")


@router.post("/session/validate", summary="智能会话验证")
async def validate_or_create_session(
        validate_request: SessionValidateRequest,
        current_user: User = DependAuth
):
    """智能验证会话是否存在，如果不存在则自动创建新会话"""
    try:
        from ....controllers.session import session_controller
        from ....schemas.session import SessionCreate

        user_id = current_user.id
        session_id = validate_request.session_id

        # 如果没有提供session_id或session_id无效，创建新会话
        if not session_id or session_id.strip() in ["", "not_login", "undefined", "null"]:
            session_data = SessionCreate(
                session_title="新对话",
                user_id=user_id,
                session_content=""
            )
            new_session = await session_controller.create_user_session(session_data)
            session_dict = await new_session.to_dict()
            return Success(data={
                "session_id": session_dict["id"],
                "session_title": session_dict["session_title"],
                "created": True
            })

        # 验证现有会话
        try:
            session_id_int = int(session_id.strip())
            if session_id_int <= 0:
                raise ValueError("会话ID必须为正整数")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="会话ID格式错误")

        # 检查会话是否存在且属于当前用户
        session = await session_controller.get_user_session(session_id_int, user_id)
        if session:
            session_dict = await session.to_dict()
            return Success(data={
                "session_id": session_dict["id"],
                "session_title": session_dict["session_title"],
                "created": False
            })
        else:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证会话失败: {str(e)}")


@router.get("/models/list", summary="获取可用模型列表")
async def get_available_models(
        page: int = Query(1, description="页码"),
        page_size: int = Query(50, description="每页数量"),
        model_type: str = Query("chat", description="模型类型")
):
    """获取可用的聊天模型列表"""
    try:
        total, models = await model_controller.get_active_models(
            model_type=model_type,
            page=page,
            page_size=page_size
        )

        model_list = []
        for model in models:
            model_dict = await model.to_dict()
            model_info = ChatModelInfo(
                id=model_dict["model_name"],
                name=model_dict["model_show"],
                description=model_dict["model_describe"],
                price=safe_serialize(model_dict["model_price"]),
                model_type=model_dict["model_type"]
            )
            model_list.append(model_info.model_dump())

        return SuccessExtra(data=model_list, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/memory/stats", summary="获取记忆统计信息")
async def get_memory_stats(
        session_id: str = Query("default", description="会话ID"),
        current_user: User = DependAuth
):
    """获取当前用户的记忆统计信息"""
    try:
        # 获取或创建会话
        session = await smart_chat_system.get_or_create_session(
            user_id=current_user.id,
            session_id=session_id
        )

        # 获取记忆统计
        memory_stats = await session.get_memory_stats()

        return Success(data=memory_stats)

    except Exception as e:
        logger.error(f"获取记忆统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")


@router.post("/memory/query", summary="查询相关记忆")
async def query_memory(
        query: str = Query(..., description="查询内容"),
        limit: int = Query(5, description="返回数量限制"),
        session_id: str = Query("default", description="会话ID"),
        current_user: User = DependAuth
):
    """查询用户的相关记忆"""
    try:
        # 获取或创建会话
        session = await smart_chat_system.get_or_create_session(
            user_id=current_user.id,
            session_id=session_id
        )

        # 查询相关记忆
        memory_data = await session.query_memory(query, limit)

        return Success(data=memory_data, msg=f"找到 {len(memory_data)} 条相关记忆")

    except Exception as e:
        logger.error(f"查询记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询记忆失败: {str(e)}")


@router.delete("/memory/clear", summary="清空用户记忆")
async def clear_user_memory(
        memory_type: str = Query("private", description="记忆类型: private, chat, all"),
        session_id: str = Query("default", description="会话ID"),
        current_user: User = DependAuth
):
    """清空用户的记忆数据"""
    try:
        # 检查是否为管理员或用户本人
        if not current_user.is_superuser:
            # 普通用户只能清空自己的私有记忆
            if memory_type not in ["private", "chat"]:
                raise HTTPException(status_code=403, detail="权限不足，只能清空私有记忆或聊天记忆")

        # 获取或创建会话
        session = await smart_chat_system.get_or_create_session(
            user_id=current_user.id,
            session_id=session_id
        )

        # 清空记忆
        success = await session.clear_memory(memory_type)

        if success:
            return Success(msg=f"已清空{memory_type}记忆")
        else:
            raise HTTPException(status_code=400, detail="清空记忆失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空记忆失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """智能聊天服务健康检查"""
    try:
        # 获取会话统计
        session_stats = smart_chat_system.get_session_stats()

        # 检查系统状态
        system_status = {
            "active_sessions": session_stats["active_sessions"],
            "memory_enabled": smart_chat_system.memory_enabled,
            "session_timeout_minutes": smart_chat_system.session_timeout_minutes
        }

        features = ["流式响应", "多模态识别", "智能选择", "图片分析", "会话管理"]
        if smart_chat_system.memory_enabled:
            features.extend(["对话记忆", "用户偏好", "知识库检索"])

        health_status = HealthStatus(
            status="healthy",
            agent_system="Smart Chat System with ChatSession",
            agents_status=system_status,
            features=features,
            service_uptime="正常运行"
        )

        return Success(data=health_status.model_dump())

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")


@router.get("/session/status", summary="获取会话状态")
async def get_session_status(
        session_id: str = Query("default", description="会话ID"),
        current_user: User = DependAuth
):
    """获取会话状态信息"""
    try:
        # 获取或创建会话
        session = await smart_chat_system.get_or_create_session(
            user_id=current_user.id,
            session_id=session_id
        )

        # 获取会话信息
        session_info = session.get_session_info()
        agent_status = session.get_agent_status()

        return Success(data={
            "session_info": session_info,
            "agent_status": agent_status
        })

    except Exception as e:
        logger.error(f"获取会话状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话状态失败: {str(e)}")


@router.get("/system/stats", summary="获取系统统计")
async def get_system_stats(
        current_user: User = DependAuth
):
    """获取系统统计信息（管理员功能）"""
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")

        # 获取会话统计
        session_stats = smart_chat_system.get_session_stats()

        # 获取消息统计
        total_messages = await message_manager.get_total_message_count()

        stats_data = {
            "session_stats": session_stats,
            "total_messages": total_messages,
            "system_info": {
                "memory_enabled": smart_chat_system.memory_enabled,
                "session_timeout_minutes": smart_chat_system.session_timeout_minutes,
                "current_text_model": smart_chat_system.current_text_model,
                "current_vision_model": smart_chat_system.current_vision_model
            }
        }

        return Success(data=stats_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")
