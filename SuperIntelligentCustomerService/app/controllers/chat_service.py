import base64
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import List, AsyncGenerator, Optional, Dict, Union

import requests
from PIL import Image as PILImage
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, MultiModalMessage as AGMultiModalMessage
from autogen_core import Image as AGImage
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_core.model_context import BufferedChatCompletionContext

from app.core.llms import get_model_client, get_default_model_client
from app.schemas.customer import ChatMessage, MessageContent
from app.services.memory_service import MemoryServiceFactory
from app.settings.config import settings

# 获取项目根目录
BASE_DIR = settings.BASE_DIR

class ChatSession:
    """聊天会话类，用于管理单个用户的对话历史和记忆"""

    def __init__(self, session_id: str, user_id: str):
        """初始化聊天会话

        Args:
            session_id: 会话唯一标识符
            user_id: 用户唯一标识符
        """
        # 初始化记忆服务工厂
        service = MemoryServiceFactory()
        self.chat_memory_service = service.get_chat_memory_service(user_id)
        self.public_memory_service = service.get_public_memory_service()
        self.private_memory_service = service.get_private_memory_service(user_id)

        self.session_id = session_id
        self.user_id = user_id

        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now()
        self.last_active = datetime.now()


class ChatService:
    """聊天服务类，处理与LLM的对话逻辑，支持多用户和用户记忆"""

    # 存储用户会话的字典
    _sessions: Dict[str, ChatSession] = {}

    def __init__(self, model: Optional[str] = None):
        """初始化聊天服务

        Args:
            model: 使用的模型名称，如果为None则使用配置中的默认模型
        """
        self.model_name = model or "deepseek-chat"  # 默认使用deepseek-chat
        self.model_client = None  # 将在异步方法中初始化

        # 初始化日志记录器
        self.logger = logging.getLogger("chat_service")

        # 创建日志目录
        logs_dir = os.path.join(BASE_DIR, "logs", "chat")
        os.makedirs(logs_dir, exist_ok=True)

        # 初始化日志处理
        file_handler = logging.FileHandler(os.path.join(logs_dir, "memory.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

        # 默认系统提示
        self.default_system_message = """
        **角色:** 你是一位专业、耐心且高效的智能客服助手。

        **核心任务:**
        1.  仔细分析用户的提问和上传的图片，准确识别其核心意图（例如：查询商品信息、搜索商品、查询订单状态、取消订单、了解促销活动、查询政策、检查退货资格、提交退货申请、提供反馈等）。
        2.  **处理图片内容:** 当用户上传图片时，你应该分析图片内容，并基于图片提供相关的帮助。你应该根据消息中指定的任务类型来处理图片。
        3.  **多模态任务类型:** 你需要支持以下任务类型，并根据任务类型提供相应的响应：
            * `image_understanding`: 理解和描述图片内容，回答"这是什么"类型的问题。
            * `image_analysis`: 分析图片中的问题、缺陷或特定元素。
            * `image_comparison`: 比较多个图片或图片中的不同元素。
            * `image_editing_suggestion`: 提供关于如何编辑或改进图片的建议。
            * `general_image_task`: 通用图片处理，根据用户描述提供相关帮助。
        4.  **回答策略:**
            * 如果用户的意图可以基于**对话历史**直接回答，请进行回答。
            * 如果无法确定用户意图或需要更多信息，请礼貌地询问用户以获取更多详细信息。
            * 始终保持专业、友好和乐于助人的态度。
            * 用简洁明了的语言回答，避免过于复杂的技术术语。
            * 如果遇到无法处理的问题，请诚实地告知用户并建议联系人工客服。

        **重要提醒:**
        - 请始终用中文回复用户。
        - 保持回答的准确性和实用性。
        - 对于图片相关的问题，请仔细观察图片内容并提供详细的分析。
        """

    async def _ensure_model_client(self):
        """确保模型客户端已初始化"""
        if self.model_client is None:
            self.model_client = await get_model_client(self.model_name)
            if self.model_client is None:
                # 如果指定模型不可用，使用默认模型
                self.model_client = await get_default_model_client()
                if self.model_client is None:
                    raise RuntimeError("无法获取任何可用的模型客户端")

    async def chat_stream(self, messages: List[ChatMessage],
                         system_prompt: Optional[str] = None,
                         user_id: str = "1",
                         session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式对话生成，支持用户记忆和会话管理

        处理用户消息（包括文本和图片），使用LLM生成响应，并保存对话历史到用户记忆中。
        支持多模态消息处理，可以处理包含图片的用户请求。

        Args:
            messages: 聊天消息列表，只用于当前请求，不会存储
            system_prompt: 系统提示，如果提供则用于创建代理
            user_id: 用户ID，用于维护用户的记忆体，默认为"1"
            session_id: 会话ID，如果提供则使用指定会话，否则创建新会话

        Yields:
            流式生成的响应片段
        """
        # 1. 输入验证
        if not messages:
            self.logger.warning(f"用户 {user_id} 提供了空消息列表")
            yield "请提供有效的用户消息"
            return

        if messages[-1].role != "user":
            self.logger.warning(f"用户 {user_id} 的最后一条消息不是用户消息")
            yield "请提供有效的用户消息"
            return

        # 2. 获取用户最后一条消息
        last_message = messages[-1]
        self.logger.info(f"处理用户 {user_id} 的聊天请求")

        # 3. 消息处理 - 根据消息类型进行不同处理
        last_user_message = await self._process_user_message(last_message, user_id)

        try:
            # 4. 确保模型客户端已初始化
            await self._ensure_model_client()

            # 5. 会话管理 - 获取或创建用户会话
            # 注意：这里使用user_id作为session_id是为了保持会话一致性
            session = self._get_or_create_session(user_id, session_id or user_id)

            # 6. 创建AI助手代理
            agent = await self._create_assistant_agent(user_id, system_prompt, session)

            # 6. 流式生成响应并处理结果
            async for event in agent.run_stream(task=last_user_message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 返回生成的文本片段
                    yield event.content
                elif isinstance(event, TaskResult):
                    # 保存对话到记忆
                    await self._save_conversation_to_memory(session, event)

        except Exception as e:
            error_msg = f"聊天处理失败 {user_id}: {e}"
            self.logger.error(error_msg)
            print(f"❌ ChatService.chat_stream 错误: {e}")
            import traceback
            traceback.print_exc()
            yield f"很抱歉，处理您的请求时出现了错误。请稍后再试。"

    async def _process_user_message(self, message: ChatMessage, user_id: str) -> Union[str, AGMultiModalMessage]:
        """处理用户消息，支持多模态内容

        Args:
            message: 用户消息
            user_id: 用户ID

        Returns:
            处理后的消息，可以是字符串或MultiModalMessage对象
        """
        # 检查是否是多模态消息（包含图片）
        if (isinstance(message.content, MessageContent) and
            message.content.type == "multi-modal" and
            message.content.content):

            self.logger.info(f"处理用户 {user_id} 的多模态消息")

            # 选择合适的多模态模型
            selected_model = await self._select_appropriate_model(is_multimodal=True)
            if selected_model != self.model_name:
                self.model_name = selected_model
                self.model_client = await get_model_client(selected_model)
                self.logger.info(f"切换到多模态模型: {selected_model}")

            # 获取文本内容，如果没有则使用默认提示
            text_content = message.content.text or "请分析这张图片的内容"
            content_list = [text_content]  # 初始化内容列表，先添加文本

            # 处理所有图片内容
            for item in message.content.content:
                if item.image and item.image.url:
                    image_result = await self._process_image(item.image.url, user_id)
                    content_list.append(image_result)

            # 创建AutoGen的MultiModalMessage对象
            return AGMultiModalMessage(content=content_list, source="User")
        else:
            # 对于纯文本消息，直接返回内容
            return message.content

    async def _process_image(self, image_url: str, user_id: str) -> AGImage:
        """处理图片URL，转换为AutoGen图片对象

        Args:
            image_url: 图片URL
            user_id: 用户ID

        Returns:
            AGImage对象
        """
        try:
            # 检查是否是本地图片URL
            if image_url.startswith("/api/v1/customer/chat/images/"):
                # 本地图片，需要构建完整路径
                return await self._load_local_image(image_url, user_id)
            else:
                # 外部图片URL
                return await self._load_external_image(image_url)
        except Exception as e:
            self.logger.error(f"处理图片失败 {image_url}: {e}")
            raise

    async def _load_local_image(self, image_url: str, user_id: str) -> AGImage:
        """从本地路径加载图片

        Args:
            image_url: 本地图片URL
            user_id: 用户ID

        Returns:
            AGImage对象
        """
        # 从URL中提取文件名
        # URL格式: /api/v1/customer/chat/images/{user_id}/{filename}
        url_parts = image_url.split('/')
        if len(url_parts) >= 2:
            filename = url_parts[-1]
            # 构建本地文件路径
            uploads_dir = os.path.join(BASE_DIR, "data", "uploads")
            image_path = os.path.join(uploads_dir, user_id, filename)

            if os.path.exists(image_path):
                self.logger.info(f"从本地加载图片: {image_path}")
                pil_image = PILImage.open(image_path)
                return AGImage(pil_image)
            else:
                raise FileNotFoundError(f"本地图片文件不存在: {image_path}")
        else:
            raise ValueError(f"无效的本地图片URL格式: {image_url}")

    async def _load_external_image(self, image_url: str) -> AGImage:
        """从外部URL或base64数据加载图片

        Args:
            image_url: 外部图片URL或base64数据URL

        Returns:
            AGImage对象

        Raises:
            Exception: 如果请求失败或图片处理出错
        """
        self.logger.info(f"加载图片: {image_url[:50]}...")

        # 检查是否是base64数据URL
        if image_url.startswith('data:'):
            # 处理base64格式的图片
            try:
                # 解析data URL格式: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
                header, data = image_url.split(',', 1)
                image_data = base64.b64decode(data)

                # 创建PIL图片对象并转换为AutoGen图片对象
                pil_image = PILImage.open(BytesIO(image_data))
                return AGImage(pil_image)

            except Exception as e:
                self.logger.error(f"解析base64图片失败: {e}")
                raise ValueError(f"无效的base64图片数据: {e}")
        else:
            # 处理外部URL
            response = requests.get(image_url, timeout=10)  # 添加超时设置
            response.raise_for_status()

            # 创建PIL图片对象并转换为AutoGen图片对象
            pil_image = PILImage.open(BytesIO(response.content))
            return AGImage(pil_image)

    async def _select_appropriate_model(self, is_multimodal: bool = False) -> str:
        """根据消息类型选择合适的模型

        Args:
            is_multimodal: 是否为多模态消息

        Returns:
            str: 选择的模型名称
        """
        try:
            from ..models.llm_models import LLMModel

            if is_multimodal:
                # 对于多模态消息，必须选择支持视觉的模型
                vision_models = await LLMModel.filter(
                    is_active=True,
                    vision=True
                ).order_by("-function_calling", "sort_order")  # 优先选择同时支持视觉和函数调用的模型

                if vision_models:
                    selected_model = vision_models[0].model_name
                    self.logger.info(f"为多模态消息选择视觉模型: {selected_model}")
                    return selected_model
                else:
                    self.logger.warning("没有找到支持视觉的模型，使用默认模型（可能无法处理图片）")
                    return self.model_name
            else:
                # 对于纯文本消息，使用当前模型或默认模型
                return self.model_name

        except Exception as e:
            self.logger.error(f"选择模型时出错: {e}")
            return self.model_name

    async def _check_model_function_calling_support(self) -> bool:
        """检查当前模型是否支持函数调用

        Returns:
            bool: 如果模型支持函数调用返回True，否则返回False
        """
        try:
            from ..models.llm_models import LLMModel
            model = await LLMModel.filter(model_name=self.model_name, is_active=True).first()
            if model:
                return model.function_calling
            else:
                # 如果数据库中找不到模型配置，默认不支持函数调用
                self.logger.warning(f"数据库中未找到模型 {self.model_name} 的配置，默认不支持函数调用")
                return False
        except Exception as e:
            self.logger.error(f"检查模型函数调用支持时出错: {e}")
            return False

    async def _create_assistant_agent(self, user_id: str, system_prompt: Optional[str], session: ChatSession) -> AssistantAgent:
        """创建AI助手代理

        Args:
            user_id: 用户ID
            system_prompt: 系统提示，如果为None则使用默认提示
            session: 用户会话

        Returns:
            AssistantAgent实例
        """
        print(f"🔧 [DEBUG] _create_assistant_agent 开始执行，用户: {user_id}, 当前模型: {self.model_name}")
        self.logger.info(f"🔧 [DEBUG] _create_assistant_agent 开始执行，用户: {user_id}, 当前模型: {self.model_name}")

        # 确保模型客户端已初始化
        await self._ensure_model_client()

        # 检查当前模型是否支持函数调用
        supports_function_calling = await self._check_model_function_calling_support()

        print(f"🔧 [DEBUG] 模型 {self.model_name} 函数调用支持: {supports_function_calling}")
        self.logger.info(f"🔧 [DEBUG] 模型 {self.model_name} 函数调用支持: {supports_function_calling}")

        # 根据模型能力动态设置 AssistantAgent 参数
        agent_params = {
            "name": f"agent_{user_id}",
            "model_client": self.model_client,
            "system_message": system_prompt or self.default_system_message,
            "model_client_stream": True,  # 启用流式输出
            "memory": [
                session.chat_memory_service.memory,
                session.public_memory_service.memory,
                session.private_memory_service.memory
            ],
            "model_context": BufferedChatCompletionContext(buffer_size=2),  # 进一步减少缓冲区大小
        }

        print(f"🔧 [DEBUG] 创建AssistantAgent，缓冲区大小: 2")
        self.logger.info(f"🔧 [DEBUG] 创建AssistantAgent，缓冲区大小: 2")

        # 只有当模型支持函数调用时才添加相关参数
        if supports_function_calling:
            agent_params["tools"] = []  # 可以添加工具
            agent_params["reflect_on_tool_use"] = True
        else:
            # 对于不支持函数调用的模型，不设置任何工具相关参数
            print(f"🔧 [DEBUG] 模型不支持函数调用，创建简单的对话代理")
            self.logger.info(f"🔧 [DEBUG] 模型不支持函数调用，创建简单的对话代理")

        return AssistantAgent(**agent_params)

    async def _save_conversation_to_memory(self, session: ChatSession, task_result: TaskResult) -> None:
        """保存对话到用户记忆

        Args:
            session: 用户会话
            task_result: 任务结果，包含用户消息和AI回复
        """
        try:
            # 保存用户提问
            if task_result.messages and len(task_result.messages) > 0:
                await session.chat_memory_service.memory.add(
                    MemoryContent(
                        content=task_result.messages[0].model_dump_json(),
                        mime_type=MemoryMimeType.JSON
                    )
                )

            # 保存AI回答
            if task_result.messages and len(task_result.messages) > 1:
                await session.chat_memory_service.memory.add(
                    MemoryContent(
                        content=task_result.messages[-1].model_dump_json(),
                        mime_type=MemoryMimeType.JSON
                    )
                )
        except Exception as e:
            self.logger.error(f"保存对话到记忆失败: {str(e)}", exc_info=True)

    def _get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ChatSession:
        """获取或创建用户会话

        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成

        Returns:
            用户会话
        """
        # 如果没有提供会话ID，生成一个新的
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 如果会话已存在，直接返回
        if session_id in self._sessions:
            return self._sessions[session_id]
        # 创建新的会话
        session = ChatSession(session_id=session_id, user_id=user_id)

        # 存储会话
        self._sessions[session_id] = session

        self.logger.info(f"Created new session {session_id} for user {user_id}")
        return session
