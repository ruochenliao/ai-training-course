import os
import logging
import uuid
import requests
from io import BytesIO
from datetime import datetime
from typing import List, AsyncGenerator, Optional, Dict, Any, Tuple, Union
from PIL import Image as PILImage

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, MultiModalMessage as AGMultiModalMessage
from autogen_core import Image as AGImage
from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_core.model_context import BufferedChatCompletionContext

from c_app.schemas.customer import ChatMessage, MessageContent
from c_app.core.llms import model_client, vllm_model_client
from c_app.services import agent_tools as tools
from c_app.services.memory_service import MemoryServiceFactory

# 主要功能：聊天历史、公共知识库、私有知识库持久化

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ChatSession:
    """聊天会话类，用于管理单个用户的对话历史和记忆"""

    def __init__(self, session_id: str, user_id: str):
        """初始化聊天会话

        Args:
            session_id: 会话唯一标识符
            user_id: 用户唯一标识符
        """
        service = MemoryServiceFactory()
        self.chat_memory_service = service.get_chat_memory_service(user_id)
        self.public_memory_service = service.get_public_memory_service()
        self.private_memory_service = service.get_private_memory_service(user_id)

        self.session_id = session_id
        self.user_id = user_id

        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now()
        self.last_active = datetime.now()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class ChatService:
    """聊天服务类，处理与LLM的对话逻辑，支持多用户和用户记忆"""

    # 存储用户会话的字典
    _sessions: Dict[str, ChatSession] = {}

    def __init__(self, model: Optional[str] = None):
        """初始化聊天服务

        Args:
            model: 使用的模型名称，如果为None则使用配置中的默认模型
        """
        self.model_client = model_client

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
        self.tools = [tools.get_active_promotions, tools.get_order_status, tools.get_policy, tools.get_product_details,
                      tools.search_products, tools.submit_return_request, tools.check_return_eligibility,
                      tools.cancel_order]
        # 默认系统提示
        self.default_system_message = """
        **角色:** 你是一位专业、耐心且高效的智能客服助手。

        **核心任务:**
        1.  仔细分析用户的提问和上传的图片，准确识别其核心意图（例如：查询商品信息、搜索商品、查询订单状态、取消订单、了解促销活动、查询政策、检查退货资格、提交退货申请、提供反馈等）。
        2.  **处理图片内容:** 当用户上传图片时，你应该分析图片内容，并基于图片提供相关的帮助。你应该根据消息中指定的任务类型来处理图片。
        3.  **多模态任务类型:** 你需要支持以下任务类型，并根据任务类型提供相应的响应：
            * `image_understanding`: 理解和描述图片内容，回答“这是什么”类型的问题。
            * `image_analysis`: 分析图片中的问题、缺陷或特定元素。
            * `image_comparison`: 比较多个图片或图片中的不同元素。
            * `image_editing_suggestion`: 提供关于如何编辑或改进图片的建议。
            * `general_image_task`: 通用图片处理，根据用户描述提供相关帮助。
        4.  **严格约束信息来源:** 你**只能**根据以下来源查找和提供答案：
            * **提供的工具 (Provided Tools):** 你拥有以下可调用的工具，用于执行特定任务。**必须**根据用户意图选择合适的工具，并使用其返回的结果来回答。
                * `get_product_details(product_id: int)`: 根据商品 ID 获取商品的详细信息。
                * `search_products(query: str)`: 根据关键词搜索商品 (返回最多5个结果)。
                * `get_order_status(order_number: str)`: 根据订单号查询订单状态和物流信息。
                * `cancel_order(order_number: str)`: 尝试取消指定订单号的订单 (仅限特定状态订单)。
                * `get_active_promotions()`: 获取当前有效的促销活动列表。
                * `get_policy(policy_type: str)`: 获取指定类型的店铺政策 (有效类型: 'return', 'shipping', 'payment', 'privacy', 'terms')。
                * `check_return_eligibility(order_number: str, product_sku: str)`: 检查指定订单中的某个商品 SKU 是否符合退货条件。
                * `submit_return_request(order_id: int, product_id: int, reason: str)`: 为指定订单中的某个商品提交退货申请。
                * `log_feedback(feedback_type: str, content: str, subject: Optional[str] = None, email: Optional[str] = None)`: 记录用户反馈 (有效类型: 'complaint', 'suggestion', 'praise')。
            * **当前对话历史 (Conversation History):** 参考 memory 中的历史信息。
        3.  **回答策略:**
            * 如果用户的意图可以通过调用上述某个**工具**来满足，请调用相应工具，并基于其返回结果清晰、简洁地回答用户。
            * 如果用户的意图可以基于**对话历史**直接回答，请进行回答。
            * **如果无法通过调用工具或参考对话历史找到答案，或者用户的意图超出了可用工具的能力范围 (例如，询问未包含的政策类型、需要进行工具无法执行的操作、或询问通用知识)，** 你**必须**礼貌地告知用户，并引导他们联系人工客服。

        **失败/无法处理时的标准回复:**
        当无法通过提供的工具或对话历史满足用户请求时，**必须**使用类似以下的回复：

        "抱歉，关于您的问题，我目前无法通过可用的工具或信息找到确切答案，或者这超出了我的处理范围。为了更好地帮助您，请添加我们的人工客服微信：**huice666**，将有专业同事为您提供进一步解答。感谢您的理解！"

        **行为准则:**
        * **专业礼貌:** 始终保持友好、专业的语气。
        * **准确高效:** 尽力调用正确的工具并提供精准的信息，避免猜测或提供不确定的答案。
        * **遵守约束:** 绝对不要尝试从指定来源之外获取信息或提供服务。不编造答案。如果工具返回错误信息，应如实告知用户无法完成操作或查询，并可根据情况建议联系人工客服。
        * **主动引导:** 在无法解决问题时，清晰地指引用户联系人工渠道。
        * **工具参数:** 在调用工具前，如果缺少必要的参数 (如 `product_id`, `order_number` 等)，需要向用户询问以获取这些信息。
        """

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
            # 4. 会话管理 - 获取或创建用户会话
            # 注意：这里使用user_id作为session_id是为了保持会话一致性
            session = self._get_or_create_session(user_id, session_id or user_id)

            # 5. 创建AI助手代理
            agent = self._create_assistant_agent(user_id, system_prompt, session)

            # 6. 流式生成响应并处理结果
            async for event in agent.run_stream(task=last_user_message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 返回生成的文本片段
                    yield event.content
                elif isinstance(event, TaskResult):
                    # 保存对话到记忆
                    await self._save_conversation_to_memory(session, event)

        except Exception as e:
            # 7. 异常处理
            error_msg = f"聊天处理失败 {user_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)  # 记录完整的异常堆栈
            yield f"很抱歉，处理您的请求时出现了错误。请稍后再试。"

    async def _process_user_message(self, message: ChatMessage, user_id: str) -> Any:
        """处理用户消息，支持文本和多模态消息

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

            # 对于多模态消息，使用支持多模态的模型
            self.model_client = vllm_model_client
            self.logger.info(f"处理用户 {user_id} 的多模态消息")

            # 获取文本内容，如果没有则使用默认提示
            text_content = message.content.text or "请深刻理解图片中表达的含义并调用合适的工具"
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

    async def _process_image(self, image_url: str, user_id: str) -> Union[AGImage, str]:
        """处理图片URL，加载图片并转换为AutoGen的Image对象

        Args:
            image_url: 图片URL
            user_id: 用户ID

        Returns:
            AGImage对象或错误信息字符串
        """
        try:
            # 处理内部图片URL（以/api/v1/chat/images/开头）
            if image_url.startswith("/api/v1/chat/images/"):
                return await self._load_internal_image(image_url)
            else:
                # 处理外部URL
                return await self._load_external_image(image_url)
        except Exception as e:
            self.logger.error(f"加载图片时出错: {str(e)}", exc_info=True)
            return f"[图片加载失败: {image_url}]"

    async def _load_internal_image(self, image_url: str) -> AGImage:
        """从内部存储加载图片

        Args:
            image_url: 内部图片URL（格式：/api/v1/chat/images/{user_id}/{filename}）

        Returns:
            AGImage对象

        Raises:
            ValueError: 如果URL格式无效
            FileNotFoundError: 如果图片文件不存在
        """
        # 解析URL获取用户ID和文件名
        parts = image_url.split('/')
        if len(parts) < 6:
            raise ValueError(f"无效的图片URL格式: {image_url}")

        user_id_from_url = parts[5]
        image_name = parts[6]

        # 构建文件路径
        file_path = os.path.join(BASE_DIR, "data", "uploads", user_id_from_url, image_name)
        self.logger.info(f"从本地文件加载图片: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"图片文件不存在: {file_path}")

        # 加载并返回图片
        pil_image = PILImage.open(file_path)
        return AGImage(pil_image)

    async def _load_external_image(self, image_url: str) -> AGImage:
        """从外部URL加载图片

        Args:
            image_url: 外部图片URL

        Returns:
            AGImage对象

        Raises:
            Exception: 如果请求失败或图片处理出错
        """
        self.logger.info(f"从外部URL加载图片: {image_url}")
        response = requests.get(image_url, timeout=10)  # 添加超时设置
        response.raise_for_status()

        # 创建PIL图片对象并转换为AutoGen图片对象
        pil_image = PILImage.open(BytesIO(response.content))
        return AGImage(pil_image)

    def _create_assistant_agent(self, user_id: str, system_prompt: Optional[str], session: ChatSession) -> AssistantAgent:
        """创建AI助手代理

        Args:
            user_id: 用户ID
            system_prompt: 系统提示，如果为None则使用默认提示
            session: 用户会话

        Returns:
            AssistantAgent实例
        """
        return AssistantAgent(
            name=f"agent_{user_id}",
            model_client=self.model_client,
            system_message=system_prompt or self.default_system_message,
            model_client_stream=True,  # 启用流式输出
            tools=self.tools,
            reflect_on_tool_use=True,
            memory=[
                session.chat_memory_service.memory,
                session.public_memory_service.memory,
                session.private_memory_service.memory
            ],
            model_context=BufferedChatCompletionContext(buffer_size=10),
        )

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
