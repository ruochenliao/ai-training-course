"""
聊天服务API端点
基于AutoGen框架的智能体聊天服务接口
支持文本和多模态内容的智能识别和处理
"""
import asyncio
import logging
import base64
from io import BytesIO
from typing import AsyncGenerator, List, Optional

import PIL.Image
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_core.models import ModelInfo, ModelFamily
from autogen_core import Image
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from ....controllers.model import model_controller
from ....core.dependency import DependAuth
from ....models.admin import User
from ....schemas import Success, Fail

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

    async def get_model_client(self, model_name: str = None, vision_support: bool = False):
        """动态获取模型客户端"""
        try:
            if not model_name:
                # 根据是否需要视觉支持选择默认模型
                if vision_support:
                    default_model = await model_controller.model.filter(
                        is_active=True,
                        model_type="multimodal"
                    ).first()
                else:
                    default_model = await model_controller.model.filter(
                        is_active=True,
                        model_type="chat"
                    ).first()

                if not default_model:
                    # 如果数据库中没有模型，使用默认配置
                    logger.warning("数据库中没有找到可用模型，使用默认配置")
                    model_name = "gpt-3.5-turbo"
                    api_host = "https://api.openai.com/v1"
                    api_key = "sk-default-key"
                else:
                    model_name = default_model.model_name
                    api_host = default_model.api_host
                    api_key = default_model.api_key
            else:
                # 根据模型名称获取配置
                try:
                    model_config = await model_controller.get_model_by_name(model_name)
                    if not model_config:
                        raise Exception(f"模型 {model_name} 不存在或未启用")
                    api_host = model_config.api_host
                    api_key = model_config.api_key
                except Exception:
                    # 如果获取失败，使用默认配置
                    logger.warning(f"获取模型 {model_name} 配置失败，使用默认配置")
                    api_host = "https://api.openai.com/v1"
                    api_key = "sk-default-key"

            # 动态更新模型信息
            model_info = DEFAULT_VISION_MODEL_INFO if vision_support else DEFAULT_TEXT_MODEL_INFO
            if model_name not in _MODEL_INFO:
                _MODEL_INFO[model_name] = model_info
            if model_name not in _MODEL_TOKEN_LIMITS:
                _MODEL_TOKEN_LIMITS[model_name] = DEFAULT_TOKEN_LIMIT

            # 创建模型客户端
            return OpenAIChatCompletionClient(
                model=model_name,
                base_url=api_host,
                api_key=api_key,
                model_info=model_info,
            )
        except Exception as e:
            logger.error(f"创建模型客户端失败: {e}")
            # 返回一个默认的模型客户端
            model_name = "gpt-3.5-turbo"
            model_info = DEFAULT_VISION_MODEL_INFO if vision_support else DEFAULT_TEXT_MODEL_INFO
            if model_name not in _MODEL_INFO:
                _MODEL_INFO[model_name] = model_info
            if model_name not in _MODEL_TOKEN_LIMITS:
                _MODEL_TOKEN_LIMITS[model_name] = DEFAULT_TOKEN_LIMIT

            return OpenAIChatCompletionClient(
                model=model_name,
                base_url="https://api.openai.com/v1",
                api_key="sk-default-key",
                model_info=model_info,
            )

    async def initialize_agents(self):
        """初始化智能体系统"""
        try:
            # 获取模型客户端
            text_model_client = await self.get_model_client(vision_support=False)
            vision_model_client = await self.get_model_client(vision_support=True)

            # 创建文本智能体
            self.text_agent = AssistantAgent(
                "text_agent",
                model_client=text_model_client,
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
                system_message="""你是专门处理多模态内容的智能客服助手。你的职责是：

1. 分析和理解图片、视频等多媒体内容
2. 结合视觉信息和文本描述回答用户问题
3. 提供基于视觉内容的专业建议
4. 识别图片中的物品、场景、文字等信息

请用中文回复，详细描述你看到的内容，并提供相关的帮助。"""
            )

            self.initialized = True
            logger.info("智能聊天系统初始化成功")

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

    async def process_message(self, message: str, files: List[UploadFile] = None) -> AsyncGenerator[str, None]:
        """处理消息并生成流式响应"""
        try:
            # 确保系统已初始化
            if not self.initialized:
                await self.initialize_agents()

            # 检测是否为多模态内容
            is_multimodal = self.detect_multimodal_content(message, files)

            # 根据内容类型选择智能体
            if is_multimodal:
                selected_agent = self.vision_agent
                agent_type = "多模态智能体"
            else:
                selected_agent = self.text_agent
                agent_type = "文本智能体"

            logger.info(f"选择了{agent_type}来处理用户消息: {message[:50]}...")

            # 创建消息对象
            if is_multimodal and files:
                # 创建多模态消息
                user_message = await self.create_multimodal_message(message, files)
            else:
                # 创建文本消息
                user_message = message

            # 使用选定的智能体生成流式响应
            try:
                # 使用 run_stream 方法进行流式处理
                async for chunk in selected_agent.run_stream(task=user_message):
                    if hasattr(chunk, 'content') and chunk.content:
                        content = str(chunk.content)
                        if content.strip():
                            yield content
                            await asyncio.sleep(0.02)  # 小延迟提供更好的流式体验
                    elif hasattr(chunk, 'messages') and chunk.messages:
                        # 这是 TaskResult，包含最终消息
                        for msg in chunk.messages:
                            if hasattr(msg, 'content') and msg.content and msg.source == 'assistant':
                                content = str(msg.content)
                                if content.strip():
                                    yield content
                                    await asyncio.sleep(0.02)
                        break  # TaskResult 是最后一个项目

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

        if "application/json" in content_type:
            # JSON格式输入（纯文本）
            json_data = await request.json()
            logger.info(f"解析JSON数据: {json_data}")

            # 验证数据格式
            if "messages" not in json_data or not json_data["messages"]:
                logger.warning(f"消息验证失败: messages={json_data.get('messages')}")
                return Fail(msg="消息内容不能为空")

            # 获取用户消息
            user_message = None
            for msg in reversed(json_data["messages"]):
                if msg.get("role") == "user":
                    user_message = msg
                    break

            logger.info(f"找到用户消息: {user_message}")

            if not user_message or not user_message.get("content"):
                logger.warning(f"用户消息验证失败: {user_message}")
                return Fail(msg="未找到有效的用户消息")

            final_message = user_message["content"].strip()
            final_session_id = json_data.get("session_id")
            file_paths = []  # JSON格式不支持文件

            logger.info(f"处理JSON请求: message='{final_message}', session_id='{final_session_id}'")

        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            # Form格式输入（支持多模态）
            try:
                form_data = await request.form()
            except Exception as e:
                logger.error(f"解析Form数据失败: {e}")
                return Fail(msg="Form数据解析失败")

            message = form_data.get("message")
            if not message or not message.strip():
                return Fail(msg="消息内容不能为空")

            final_message = message.strip()
            final_session_id = form_data.get("session_id")

            # 处理上传的文件
            uploaded_files = []
            files = form_data.getlist("files")
            for file in files:
                if hasattr(file, 'filename') and file.filename:
                    # 验证文件类型（如果有文件的话）
                    if file.content_type and not file.content_type.startswith('image/'):
                        return Fail(msg=f"不支持的文件类型: {file.content_type}，目前仅支持图片文件")
                    uploaded_files.append(file)

            logger.info(f"接收到Form请求: 消息='{final_message}', 文件数量={len(uploaded_files)}")
        else:
            # 尝试作为JSON处理（兼容性处理）
            try:
                json_data = await request.json()
                logger.info(f"尝试作为JSON解析: {json_data}")

                # 检查是否是简单的消息格式
                if "message" in json_data:
                    final_message = json_data["message"].strip()
                    final_session_id = json_data.get("session_id")
                    uploaded_files = []
                    logger.info(f"处理简单JSON请求: message='{final_message}', session_id='{final_session_id}'")
                else:
                    return Fail(msg="不支持的内容类型或数据格式")
            except:
                return Fail(msg="不支持的内容类型，请使用JSON或Form格式")

        # 返回流式响应
        return StreamingResponse(
            _generate_stream_response(
                message=final_message,
                session_id=final_session_id,
                files=uploaded_files if 'uploaded_files' in locals() else [],
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


async def _generate_stream_response(
        message: str,
        session_id: Optional[str],
        files: List[UploadFile],
        user_id: int
) -> AsyncGenerator[str, None]:
    """生成流式响应"""

    try:
        # 保存用户消息到数据库
        if session_id:
            try:
                from ....controllers.chat import chat_controller
                from ....schemas.chat import ChatMessageCreate

                user_message_create = ChatMessageCreate(
                    session_id=int(session_id) if session_id.isdigit() else 1,
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
        async for content in smart_chat_system.process_message(message, files):
            if content.strip():
                full_response += content
                # 直接输出内容
                yield f"data: {content}\n\n"

        # 发送结束标记
        yield "data: [DONE]\n\n"

        # 保存AI回复到数据库
        if session_id and full_response:
            try:
                ai_message_create = ChatMessageCreate(
                    session_id=int(session_id) if session_id.isdigit() else 1,
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


@router.get("/session/{session_id}", summary="获取会话信息")
async def get_session_info(
        session_id: str,
        current_user: User = DependAuth
):
    """获取指定会话的信息"""
    try:
        from ....controllers.session import session_controller

        session_id_int = int(session_id)
        session = await session_controller.get_user_session(session_id_int, current_user.id)

        if not session:
            return Fail(msg="会话不存在或无权限访问")

        session_dict = await session.to_dict()
        return Success(data=session_dict)

    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        return Fail(msg=f"获取会话信息失败: {str(e)}")


@router.get("/sessions", summary="获取用户会话列表（聊天端）")
async def list_user_sessions(
        current_user: User = DependAuth
):
    """
    获取当前用户的所有会话列表（聊天端使用）
    返回简化的会话信息，适用于聊天界面
    """
    try:
        from ....controllers.session import session_controller

        total, sessions = await session_controller.get_user_sessions(
            user_id=current_user.id,
            page=1,
            page_size=100  # 聊天端显示更多会话
        )

        # 转换为简化格式
        session_list = []
        for session in sessions:
            session_dict = await session.to_dict()
            simplified_session = {
                "id": str(session_dict["id"]),
                "title": session_dict.get("session_title", "新对话"),
                "updated_at": session_dict.get("updated_at")
            }
            session_list.append(simplified_session)

        return Success(data=session_list)

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
        from ....controllers.session import session_controller

        session_id_int = int(session_id)
        deleted_count = await session_controller.delete_user_sessions(
            [session_id_int],
            current_user.id
        )

        if deleted_count > 0:
            return Success(msg="会话已关闭")
        else:
            return Fail(msg="会话不存在或无权限删除")

    except ValueError:
        return Fail(msg="无效的会话ID")
    except Exception as e:
        logger.error(f"关闭会话失败: {e}")
        return Fail(msg=f"关闭会话失败: {str(e)}")


@router.post("/session/create", summary="直接创建新会话")
async def create_session(
        current_user: User = DependAuth
):
    """
    直接创建新的聊天会话
    适用于明确需要新会话的场景
    """
    try:
        from ....controllers.session import session_controller
        from ....schemas.session import SessionCreate

        session_data = SessionCreate(
            session_title="新对话",
            user_id=current_user.id,
            session_content=""
        )

        new_session = await session_controller.create_user_session(session_data)
        session_dict = await new_session.to_dict()

        return Success(data={
            "session_id": str(session_dict["id"]),
            "session_title": session_dict["session_title"],
            "user_id": session_dict["user_id"],
            "created_at": session_dict["created_at"],
            "message": "会话创建成功"
        })

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return Fail(msg=f"创建会话失败: {str(e)}")


@router.get("/stats", summary="获取服务统计")
async def get_service_stats(
        current_user: User = DependAuth
):
    """获取多智能体聊天服务统计信息（管理员功能）"""
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            return Fail(msg="权限不足")

        from ....controllers.session import session_controller
        from ....controllers.chat import chat_controller

        # 获取会话统计
        total_sessions, _ = await session_controller.get_user_sessions(
            user_id=None,  # 获取所有用户的会话
            page=1,
            page_size=1
        )

        # 获取消息统计
        total_messages = await chat_controller.get_total_message_count()

        return Success(data={
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "agent_system": "smart-chat-system",
            "agents": ["text_agent", "vision_agent"],
            "features": ["流式响应", "多模态识别", "智能选择"]
        })

    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        return Fail(msg=f"获取服务统计失败: {str(e)}")



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

        return Success(data={
            "status": "healthy" if all_agents_ready else "initializing",
            "agent_system": "Smart Chat System",
            "agents_status": agent_status,
            "features": ["流式响应", "多模态识别", "智能选择", "图片分析"],
            "service_uptime": "正常运行"
        })

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return Fail(msg=f"服务异常: {str(e)}")
