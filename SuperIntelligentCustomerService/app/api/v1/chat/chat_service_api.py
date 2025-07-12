"""
聊天服务API端点
基于AutoGen框架的智能体聊天服务接口
支持文本和多模态内容的智能识别和处理
标准化实现，参考roles.py模式
"""
import asyncio
import logging
from io import BytesIO
from typing import AsyncGenerator

import PIL.Image
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS
from fastapi import APIRouter, Request, Query, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....controllers.chat import chat_controller
from ....controllers.model import model_controller
from ....core.dependency import DependAuth
from ....models.admin import User
from ....schemas import Success, Fail, SuccessExtra
from ....schemas.chat_service import *
from ....utils.serializer import safe_serialize
from ....utils.encryption import decrypt_api_key, is_api_key_encrypted

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
    """智能聊天系统 - 根据内容类型自动选择合适的处理方式"""

    def __init__(self):
        self.text_agent = None
        self.vision_agent = None
        self.initialized = False
        self.current_text_model = None
        self.current_vision_model = None

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

    async def initialize_agents(self, text_model_name: str = None, vision_model_name: str = None):
        """初始化智能体系统"""
        try:
            # 获取模型客户端
            text_model_client = await self.get_model_client(model_name=text_model_name, vision_support=False)
            vision_model_client = await self.get_model_client(model_name=vision_model_name, vision_support=True)

            # 创建文本智能体
            self.text_agent = AssistantAgent(
                "text_agent",
                model_client=text_model_client,
                model_client_stream=True,  # 启用流式token
                system_message="""你是专门处理文本对话的智能客服助手。你的职责是：

1. 回答用户的文本问题
2. 提供专业、友好、准确的服务
3. 理解用户意图并给出有用的建议
4. 保持对话的连贯性和上下文理解

请用中文回复，语气要专业且友好。"""
            )

            # 创建多模态智能体
            self.vision_agent = AssistantAgent(
                "vision_agent",
                model_client=vision_model_client,
                model_client_stream=True,  # 启用流式token
                system_message="""你是专门处理多模态内容的智能客服助手。你的职责是：

1. 分析和理解图片、视频等多媒体内容
2. 结合视觉信息和文本描述回答用户问题
3. 提供基于视觉内容的专业建议
4. 识别图片中的物品、场景、文字等信息

请用中文回复，详细描述你看到的内容，并提供相关的帮助。"""
            )

            # 记录当前使用的模型
            self.current_text_model = text_model_name
            self.current_vision_model = vision_model_name
            self.initialized = True
            logger.info(f"智能聊天系统初始化成功 - 文本模型: {text_model_name}, 视觉模型: {vision_model_name}")

        except Exception as e:
            logger.error(f"初始化智能体系统失败: {e}")
            raise

    def detect_multimodal_content(self, message: str, files: List[str] = None) -> bool:
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

    async def process_message(self, message: str, files: List[UploadFile] = None, model_name: str = None) -> AsyncGenerator[str, None]:
        """处理消息并生成流式响应"""
        try:
            # 检测是否为多模态内容
            is_multimodal = self.detect_multimodal_content(message, files)

            # 确定需要使用的模型
            target_model = model_name if model_name else None

            # 检查是否需要重新初始化智能体（模型切换）
            need_reinit = False
            if not self.initialized:
                need_reinit = True
            elif is_multimodal and self.current_vision_model != target_model:
                need_reinit = True
                logger.info(f"检测到视觉模型切换: {self.current_vision_model} -> {target_model}")
            elif not is_multimodal and self.current_text_model != target_model:
                need_reinit = True
                logger.info(f"检测到文本模型切换: {self.current_text_model} -> {target_model}")

            # 重新初始化智能体（如果需要）
            if need_reinit:
                if is_multimodal:
                    await self.initialize_agents(vision_model_name=target_model)
                else:
                    await self.initialize_agents(text_model_name=target_model)

            # 根据内容类型选择智能体
            if is_multimodal:
                selected_agent = self.vision_agent
                agent_type = "多模态智能体"
                current_model = self.current_vision_model or "默认视觉模型"
            else:
                selected_agent = self.text_agent
                agent_type = "文本智能体"
                current_model = self.current_text_model or "默认文本模型"

            logger.info(f"选择了{agent_type}({current_model})来处理用户消息: {message[:50]}...")

            # 创建消息对象
            if is_multimodal and files:
                # 创建多模态消息
                user_message = await self.create_multimodal_message(message, files)
            else:
                # 创建文本消息
                user_message = message

            # 使用选定的智能体生成流式响应
            try:
                logger.info("开始流式处理...")

                # 根据官方文档，run_stream返回异步迭代器，产生消息和最终TaskResult
                full_response = ""

                async for message in selected_agent.run_stream(task=user_message):
                    try:
                        # 检查消息类型
                        message_type = getattr(message, 'type', None)

                        # 处理流式token块 (ModelClientStreamingChunkEvent)
                        if message_type == 'ModelClientStreamingChunkEvent':
                            if hasattr(message, 'content') and message.content:
                                content = str(message.content)
                                if content:
                                    full_response += content
                                    yield content
                                    await asyncio.sleep(0.01)

                        # 处理文本消息 (TextMessage)
                        elif message_type == 'TextMessage':
                            if (hasattr(message, 'source') and message.source == 'assistant' and
                                hasattr(message, 'content') and message.content):
                                content = str(message.content).strip()

                                # 过滤掉用户输入的内容
                                if content and content != user_message:
                                    # 如果内容以用户消息开头，移除用户消息部分
                                    if isinstance(user_message, str) and content.startswith(user_message):
                                        content = content[len(user_message):].strip()

                                    if content:
                                        # 如果没有流式内容，直接输出完整内容
                                        if not full_response:
                                            full_response = content
                                            yield content
                                            await asyncio.sleep(0.01)
                                        # 如果有流式内容但不匹配，可能是最终的完整响应
                                        elif content != full_response and len(content) > len(full_response):
                                            # 输出剩余部分
                                            remaining = content[len(full_response):]
                                            if remaining:
                                                full_response = content
                                                yield remaining
                                                await asyncio.sleep(0.01)

                        # 处理TaskResult（最终结果）
                        elif hasattr(message, 'messages'):
                            # 这是TaskResult，包含完整的对话历史
                            logger.debug("收到TaskResult")
                            # 如果没有收到任何流式内容，从TaskResult中提取
                            if not full_response:
                                for msg in message.messages:
                                    if (hasattr(msg, 'source') and msg.source == 'assistant' and
                                        hasattr(msg, 'content') and msg.content):
                                        content = str(msg.content).strip()
                                        if content and content != user_message:
                                            # 过滤用户输入
                                            if isinstance(user_message, str) and content.startswith(user_message):
                                                content = content[len(user_message):].strip()
                                            if content:
                                                full_response = content
                                                yield content
                                                await asyncio.sleep(0.01)
                                                break

                        # 处理其他类型的消息（如工具调用等）
                        else:
                            logger.debug(f"收到其他类型消息: {message_type}")

                    except Exception as chunk_error:
                        logger.warning(f"处理消息时出错: {chunk_error}")
                        continue

                logger.info(f"流式处理完成，总长度: {len(full_response)}")

            except Exception as e:
                logger.error(f"智能体响应生成失败: {e}")
                yield f"抱歉，生成回复时出现错误：{str(e)}"

        except Exception as e:
            logger.error(f"智能体处理消息失败: {e}")
            yield f"抱歉，处理您的请求时出现了错误：{str(e)}"

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
                "Content-Type": "text/event-stream"
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
    """生成流式响应"""

    try:
        # 保存用户消息到数据库
        if session_id:
            try:
                from ....controllers.chat import chat_controller
                from ....schemas.chat import ChatMessageCreate

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

                user_message_create = ChatMessageCreate(
                    session_id=session_id_int,
                    user_id=user_id,
                    role="user",
                    content=message,
                    model_name="smart-agent",
                    total_tokens=0,
                    deduct_cost=0
                )
                await chat_controller.create_message(user_message_create)
            except Exception as save_error:
                logger.warning(f"保存用户消息失败: {save_error}")

        # 使用智能聊天系统处理消息
        full_response = ""
        async for content in smart_chat_system.process_message(message, files, model_name):
            if content.strip():
                full_response += content
                # 直接输出内容
                yield f"data: {content}\n\n"

        # 发送结束标记
        yield "data: [DONE]\n\n"

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
                await chat_controller.create_message(ai_message_create)
            except Exception as save_error:
                logger.warning(f"保存AI回复失败: {save_error}")

    except Exception as e:
        logger.error(f"流式响应生成失败: {e}")
        # 输出错误信息
        yield f"data: 抱歉，处理您的请求时出现了错误：{str(e)}\n\n"
        yield "data: [DONE]\n\n"


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
        total_messages = await chat_controller.get_total_message_count()

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


@router.get("/health", summary="健康检查")
async def health_check():
    """智能聊天服务健康检查"""
    try:
        # 检查智能聊天系统状态
        agent_status = {
            "text_agent": smart_chat_system.text_agent is not None,
            "vision_agent": smart_chat_system.vision_agent is not None,
            "initialized": smart_chat_system.initialized
        }

        all_agents_ready = smart_chat_system.initialized and all([
            smart_chat_system.text_agent is not None,
            smart_chat_system.vision_agent is not None
        ])

        health_status = HealthStatus(
            status="healthy" if all_agents_ready else "initializing",
            agent_system="Smart Chat System",
            agents_status=agent_status,
            features=["流式响应", "多模态识别", "智能选择", "图片分析"],
            service_uptime="正常运行"
        )

        return Success(data=health_status.model_dump())

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")
