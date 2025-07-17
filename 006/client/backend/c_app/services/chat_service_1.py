import asyncio
import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, AsyncGenerator, Optional, Dict, Any, Tuple

import aiofiles
import yaml
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_agentchat.ui import Console  # 新增导入
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.memory._base_memory import ContentType
from autogen_ext.experimental.task_centric_memory import MemoryController
from autogen_ext.experimental.task_centric_memory.utils import Teachability

from c_app.core.config import settings
from c_app.services.memory_service import PersistentListMemory
from c_app.schemas.customer import ChatMessage
from c_app.core.llms import model_client

class ChatSession:
    """聊天会话类，用于管理单个用户的对话历史和记忆"""

    def __init__(self, session_id: str, user_id: str):
        """初始化聊天会话

        Args:
            session_id: 会话唯一标识符
            user_id: 用户唯一标识符
        """
        # 获取项目根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        # 确保记忆存储目录存在
        self.memories_dir = os.path.join(self.base_dir, "data", "memories")
        os.makedirs(self.memories_dir, exist_ok=True)

        self.session_id = session_id
        self.user_id = user_id
        self.user_memory = PersistentListMemory(name=f"memory_{user_id}", storage_dir=self.memories_dir)

        self.messages: List[ChatMessage] = []
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    def add_message(self, message: ChatMessage) -> None:
        """添加消息到会话历史

        Args:
            message: 要添加的消息
        """
        self.messages.append(message)
        self.last_active = datetime.now()

    def get_messages(self) -> List[ChatMessage]:
        """获取会话历史消息

        Returns:
            会话历史消息列表
        """
        return self.messages

    def clear_messages(self) -> None:
        """清除会话历史消息"""
        self.messages = []

    async def add_memory(self, content: ContentType, mime_type: MemoryMimeType = MemoryMimeType.TEXT) -> None:
        """添加记忆

        Args:
            content: 内容
            mime_type: 内容类型
        """
        await self.user_memory.add(
            MemoryContent(
                content=content,
                mime_type=mime_type
            )
        )
async def web_search(message: str) -> str:
    """从互联网查询数据"""
    return f"今天的股票行情很好"

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

        # 默认系统提示
        self.default_system_message = """你是但问智能助手，你要只能根据用户的判断选择合适的工具回答问题，如果没有找到合适的工具，请回复说：非常抱歉，我无法回答您的问题。"""

    async def chat_stream(self, messages: List[ChatMessage],
                         system_prompt: Optional[str] = None,
                         user_id: str = "default",
                         session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式对话生成，支持用户记忆和会话管理

        Args:
            messages: 聊天消息列表，只用于当前请求，不会存储
            system_prompt: 系统提示，如果提供则用于创建代理
            user_id: 用户ID，用于维护用户的记忆体，默认为"default"
            session_id: 会话ID，如果提供则使用指定会话，否则创建新会话

        Yields:
            流式生成的响应片段
        """
        # 确保有消息
        if not messages or messages[-1].role != "user":
            yield "请提供有效的用户消息"
            return

        # 获取用户最后一条消息
        last_user_message = messages[-1].content
        self.logger.info(f"处理用户 {user_id} 的聊天请求: '{last_user_message[:50]}...'")

        try:
            # 默认session_id暂时跟 user_id 相同
            session = self._get_or_create_session(user_id, user_id)
            # 使用包含上下文的记忆列表创建新的代理
            agent = AssistantAgent(
                name=f"agent_{user_id}",
                model_client=self.model_client,
                system_message=system_prompt or self.default_system_message,
                model_client_stream=True,  # 启用流式输出
                tools=[web_search],
                reflect_on_tool_use=True,
                memory=[session.user_memory]  # 使用包含上下文的记忆列表
            )

            # 流式生成响应
            async for event in agent.run_stream(task=last_user_message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    yield event.content
                elif isinstance(event, TaskResult):
                    # 用户提问
                    await session.user_memory.add(MemoryContent(content=event.messages[0].model_dump_json(), mime_type=MemoryMimeType.JSON))
                    # AI回答
                    await session.user_memory.add(MemoryContent(content=event.messages[-1].model_dump_json(), mime_type=MemoryMimeType.JSON))
            # 保存聊天历史
            await session.user_memory.save_to_disk()

        except Exception as e:
            error_msg = f"聊天处理失败 {user_id}: {e}"
            self.logger.error(error_msg)
            yield f"很抱歉，处理您的请求时出现了错误。请稍后再试。"
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
