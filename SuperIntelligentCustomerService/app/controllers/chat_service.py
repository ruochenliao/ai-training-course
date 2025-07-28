import asyncio
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

from app.core.autogen_workbench import mcp_workbench
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

        # 默认系统提示（支持MCP工具）
        self.default_system_message = """你是一位专业、耐心且高效的智能客服助手，具备访问电商系统数据的能力。

**核心能力:**
1. **商品查询**: 使用get_products工具查询商品信息、搜索商品、查看推荐商品
2. **订单管理**: 使用get_orders工具查询订单状态、跟踪订单进度
3. **客户服务**: 使用get_customers工具查询客户信息
4. **促销活动**: 使用get_promotions工具查询当前促销活动和优惠信息
5. **购物车**: 使用get_carts工具查询购物车状态

**多模态支持:**
- `image_understanding`: 理解和描述图片内容
- `image_analysis`: 分析图片中的问题、缺陷或特定元素
- `image_comparison`: 比较多个图片或图片中的不同元素
- `image_editing_suggestion`: 提供图片编辑建议
- `general_image_task`: 通用图片处理

**服务原则:**
- 主动使用工具获取准确的实时数据
- 根据用户问题选择合适的工具
- 提供准确、及时、友好的服务
- 始终用中文回复用户
- 如遇无法处理的问题，建议联系人工客服
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

            # 6. 创建MCP支持的AI助手代理
            agent = await self._create_mcp_assistant_agent(user_id, system_prompt, session)

            # 6. 流式生成响应并处理结果
            print(f"[DEBUG] 开始流式处理任务: {last_user_message}")
            self.logger.info(f"[DEBUG] 开始流式处理任务: {last_user_message}")

            # 使用流式方式处理
            try:
                ai_response_parts = []
                task_result = None

                async for event in agent.run_stream(task=last_user_message):
                    print(f"[DEBUG] 收到事件: {type(event).__name__}")

                    if isinstance(event, ModelClientStreamingChunkEvent):
                        # 流式文本内容
                        print(f"[DEBUG] 流式内容: {event.content}")
                        ai_response_parts.append(event.content)
                        yield event.content
                    elif isinstance(event, TaskResult):
                        # 任务完成
                        task_result = event
                        print(f"[DEBUG] 任务完成")
                    else:
                        # 其他事件（工具调用等）
                        print(f"[DEBUG] 其他事件: {type(event).__name__}")

                # 如果没有收到任何流式内容，说明AI没有生成回复
                if not ai_response_parts:
                    print(f"[DEBUG] 没有收到AI回复，分析工具调用结果...")

                    # 分析工具调用结果并生成回复
                    tool_results = []
                    if task_result and hasattr(task_result, 'messages'):
                        for message in task_result.messages:
                            if hasattr(message, 'type') and message.type == 'ToolCallSummaryMessage':
                                tool_results.append(message.content)

                    # 根据工具结果生成智能回复
                    if tool_results:
                        ai_response = await self._generate_response_from_tool_results(tool_results, last_user_message)
                    else:
                        ai_response = "很抱歉，我暂时无法为您提供相关信息。请稍后再试或联系人工客服。"

                    print(f"[DEBUG] 生成的AI回复: {ai_response}")

                    # 模拟流式输出
                    for char in ai_response:
                        yield char
                        await asyncio.sleep(0.02)

                # 保存对话到记忆
                if task_result:
                    await self._save_conversation_to_memory(session, task_result)

            except Exception as e:
                print(f"[DEBUG] 任务执行异常: {e}")
                import traceback
                traceback.print_exc()
                yield "很抱歉，处理您的请求时出现了问题。请稍后再试。"

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
        print(f"[DEBUG] _create_assistant_agent 开始执行，用户: {user_id}, 当前模型: {self.model_name}")
        self.logger.info(f"[DEBUG] _create_assistant_agent 开始执行，用户: {user_id}, 当前模型: {self.model_name}")

        # 确保模型客户端已初始化
        await self._ensure_model_client()

        # 检查当前模型是否支持函数调用
        supports_function_calling = await self._check_model_function_calling_support()

        print(f"[DEBUG] 模型 {self.model_name} 函数调用支持: {supports_function_calling}")
        self.logger.info(f"[DEBUG] 模型 {self.model_name} 函数调用支持: {supports_function_calling}")

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
            "model_context": BufferedChatCompletionContext(buffer_size=1),  # 最小缓冲区大小以减少输入长度
        }

        print(f"[DEBUG] 创建AssistantAgent，缓冲区大小: 1")
        self.logger.info(f"[DEBUG] 创建AssistantAgent，缓冲区大小: 1")

        # 估算输入长度（简单估算）
        system_prompt_length = len(system_prompt or self.default_system_message)
        print(f"[DEBUG] 系统提示词长度: {system_prompt_length}")
        self.logger.info(f"[DEBUG] 系统提示词长度: {system_prompt_length}")

        # 只有当模型支持函数调用时才添加相关参数
        if supports_function_calling:
            agent_params["tools"] = []  # 可以添加工具
            agent_params["reflect_on_tool_use"] = True
        else:
            # 对于不支持函数调用的模型，不设置任何工具相关参数
            print(f"[DEBUG] 模型不支持函数调用，创建简单的对话代理")
            self.logger.info(f"[DEBUG] 模型不支持函数调用，创建简单的对话代理")

        return AssistantAgent(**agent_params)

    async def _create_mcp_assistant_agent(self, user_id: str, system_prompt: Optional[str], session: ChatSession):
        """创建支持MCP的助手代理"""
        print(f"[DEBUG] 创建MCP助手代理，用户: {user_id}, 模型: {self.model_name}")
        self.logger.info(f"[DEBUG] 创建MCP助手代理，用户: {user_id}, 模型: {self.model_name}")

        # 使用提供的系统提示或默认系统提示
        final_system_message = system_prompt or self.default_system_message

        # 估算输入长度
        system_prompt_length = len(final_system_message)
        print(f"[DEBUG] 系统提示词长度: {system_prompt_length}")
        self.logger.info(f"[DEBUG] 系统提示词长度: {system_prompt_length}")

        # 创建MCP助手代理
        agent_name = f"customer_service_{user_id}_{datetime.now().timestamp()}"

        # 定义要启用的MCP工具
        enabled_tools = ["get_products", "get_orders", "get_customers", "get_promotions", "get_carts"]

        print(f"[DEBUG] 启用MCP工具: {enabled_tools}")
        self.logger.info(f"[DEBUG] 启用MCP工具: {enabled_tools}")

        # 使用MCP工作台创建代理
        mcp_agent = await mcp_workbench.create_agent(
            agent_name=agent_name,
            model_name=self.model_name,
            system_message=final_system_message,
            tools=enabled_tools,
            buffer_size=1  # 最小缓冲区大小
        )

        print(f"[DEBUG] MCP助手代理创建成功: {agent_name}")
        self.logger.info(f"[DEBUG] MCP助手代理创建成功: {agent_name}")

        return mcp_agent

    async def _generate_response_from_tool_results(self, tool_results: List[str], user_question: str) -> str:
        """根据工具调用结果生成智能回复"""
        try:
            import json

            # 解析工具结果
            parsed_results = []
            for result in tool_results:
                try:
                    parsed = json.loads(result)
                    parsed_results.append(parsed)
                except:
                    continue

            # 根据用户问题和工具结果生成回复
            if "iPhone" in user_question or "手机" in user_question:
                # 商品查询相关
                for result in parsed_results:
                    if result.get("success") and result.get("data", {}).get("total", 0) == 0:
                        return """很抱歉，目前我们的推荐商品中暂时没有iPhone相关产品。

不过我可以为您提供以下建议：
1. 您可以浏览我们的全部商品目录，可能有其他优质的手机产品
2. 可以关注我们的促销活动，经常会有新品上架
3. 如需了解具体的iPhone产品信息，建议联系我们的人工客服

有什么其他我可以帮助您的吗？"""
                    elif result.get("success") and result.get("data", {}).get("items"):
                        items = result["data"]["items"]
                        response = "为您推荐以下iPhone产品：\n\n"
                        for i, item in enumerate(items[:3], 1):
                            response += f"{i}. {item.get('name', '未知商品')}\n"
                            if item.get('price'):
                                response += f"   价格：¥{item['price']}\n"
                            if item.get('description'):
                                response += f"   描述：{item['description']}\n"
                            response += "\n"
                        response += "如需了解更多详情或购买，请告诉我具体的商品编号。"
                        return response

            # 默认回复
            return "很抱歉，我暂时无法为您提供相关信息。请稍后再试或联系人工客服获得更详细的帮助。"

        except Exception as e:
            print(f"[DEBUG] 生成回复时出错: {e}")
            return "很抱歉，处理您的请求时出现了问题。请稍后再试。"

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
