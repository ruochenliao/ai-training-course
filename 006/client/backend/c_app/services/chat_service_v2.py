import asyncio
import os
import json
import logging
from typing import List, AsyncGenerator, Optional, Dict, Any, Tuple

import aiofiles
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import ModelClientStreamingChunkEvent

from c_app.schemas.customer import ChatMessage
from c_app.core.llms import model_client

from c_app.services import agent_tools as tools

# 主要功能：基于agent自身的状态管理，支持多用户和用户记忆

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class ChatService:
    """聊天服务类，处理与LLM的对话逻辑，支持多用户和用户记忆"""

    def __init__(self):
        """初始化聊天服务
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
        self.default_system_message = "你是一个但问商城的专业、友好且高效的客服助手。你的名字是 小慧。你的主要目标是帮助用户解决与 但问商城 购物相关的问题，提供准确的信息，并提升用户满意度。首先识别用户的意图，然后调用相应的工具完成。"

    async def chat_stream(self, messages: List[ChatMessage],
                         user_id: str = "default",
                         session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式对话生成，支持用户记忆和会话管理

        Args:
            messages: 聊天消息列表，只用于当前请求，不会存储
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
            # 使用包含上下文的记忆列表创建新的代理
            agent = await self.get_agent(user_id)

            # 流式生成响应
            async for event in agent.run_stream(task=last_user_message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    yield event.content

            # Save agent state to file.
            state = await agent.save_state()
            state_path = os.path.join(BASE_DIR, "data", "agents", f"state_{user_id}.json")
            async with aiofiles.open(state_path, "w") as file:
                await file.write(json.dumps(state))

        except Exception as e:
            error_msg = f"聊天处理失败 {user_id}: {e}"
            self.logger.error(error_msg)
            yield f"很抱歉，处理您的请求时出现了错误。请稍后再试。"

    async def get_agent(self, user_id: str) -> AssistantAgent:
        """Get the assistant agent, load state from file."""
        # Create the assistant agent.
        agent = AssistantAgent(
            name="assistant",
            model_client=model_client,
            system_message=self.default_system_message,
            tools=self.tools,
            reflect_on_tool_use=True,  # True-对工具调用的结果再次发个大模型进行输出，False-原样输出
            model_client_stream=True
        )
        # Load state from file.
        state_path = os.path.join(BASE_DIR, "data", "agents", f"state_{user_id}.json")
        if not os.path.exists(state_path):
            return agent  # Return agent without loading state.
        async with aiofiles.open(state_path, "r") as file:
            state = json.loads(await file.read())
        await agent.load_state(state)
        return agent
