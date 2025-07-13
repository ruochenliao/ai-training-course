"""
聊天会话管理类
管理单用户对话状态，集成多记忆服务
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Any, AsyncGenerator

try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage, MultiModalMessage
    from autogen_agentchat.task import TaskResult
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # 创建占位符类
    class AssistantAgent:
        def __init__(self, *args, **kwargs): pass
        async def on_messages_stream(self, *args, **kwargs): pass
    class TextMessage:
        def __init__(self, content, source=""): 
            self.content = content
            self.source = source
    class MultiModalMessage:
        def __init__(self, content, source=""): 
            self.content = content
            self.source = source
    class TaskResult:
        def __init__(self, messages=None, stop_reason=None):
            self.messages = messages or []
            self.stop_reason = stop_reason

from ..schemas.chat_service import (
    ChatMessage, MessageRole, MessageType, SessionInfo,
    MemoryContext, ChatServiceConfig
)
from ..core.custom_context import create_safe_assistant_with_memory

logger = logging.getLogger(__name__)


class ChatSession:
    """
    聊天会话管理类
    管理单用户对话状态，集成三种记忆服务
    """
    
    def __init__(
        self,
        user_id: str,
        session_id: str,
        memory_factory,
        model_client: Optional[Any] = None,
        config: Optional[ChatServiceConfig] = None
    ):
        """
        初始化聊天会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            memory_factory: 记忆服务工厂
            model_client: 模型客户端
            config: 会话配置
        """
        self.user_id = user_id
        self.session_id = session_id
        self.memory_factory = memory_factory
        self.model_client = model_client
        self.config = config or ChatServiceConfig()
        
        # 会话状态
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.is_active = True
        
        # 消息历史
        self.messages: List[ChatMessage] = []
        
        # 记忆服务
        self.chat_memory = None
        self.private_memory = None
        self.public_memory = None
        
        # AutoGen智能体
        self.assistant_agent: Optional[AssistantAgent] = None
        
        # 延迟初始化标志
        self._memory_initialized = False
        
        logger.info(f"创建聊天会话: {session_id} (用户: {user_id})")

    async def _ensure_memory_initialized(self):
        """确保记忆服务已初始化"""
        if not self._memory_initialized:
            await self._init_memory_services()
            self._memory_initialized = True
    
    async def _init_memory_services(self):
        """初始化记忆服务"""
        try:
            if self.memory_factory is None:
                logger.warning(f"会话 {self.session_id} 记忆工厂未初始化，跳过记忆服务初始化")
                return

            # 获取记忆服务实例
            self.chat_memory = self.memory_factory.get_chat_memory_service(self.user_id)
            self.private_memory = self.memory_factory.get_private_memory_service(self.user_id)
            self.public_memory = self.memory_factory.get_public_memory_service()

            logger.info(f"会话 {self.session_id} 记忆服务初始化完成")
        except Exception as e:
            logger.error(f"初始化记忆服务失败: {e}")
            # 不抛出异常，允许会话在没有记忆服务的情况下工作
            self.chat_memory = None
            self.private_memory = None
            self.public_memory = None
    
    async def _create_assistant_agent(self, system_prompt: Optional[str] = None) -> AssistantAgent:
        """创建AutoGen助手智能体"""
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen不可用，无法创建智能体")
            return None
        
        try:
            # 使用自定义系统提示或默认提示
            prompt = system_prompt or self.config.system_prompt
            
            # 创建记忆适配器列表
            memory_adapters = []
            
            # 导入记忆适配器
            try:
                from .memory import AutoGenMemoryAdapter
                
                # 创建多记忆融合适配器
                memory_adapter = AutoGenMemoryAdapter(
                    user_id=self.user_id,
                    db_path=None  # 使用默认路径
                )
                memory_adapters.append(memory_adapter)
            except ImportError:
                logger.warning("记忆适配器不可用")
            
            # 创建助手智能体（使用修复后的上下文）
            assistant = create_safe_assistant_with_memory(
                name="intelligent_assistant",
                model_client=self.model_client,
                system_message=prompt,
                memory_adapters=memory_adapters if memory_adapters else None
            )
            
            logger.info(f"会话 {self.session_id} 助手智能体创建成功")
            return assistant
            
        except Exception as e:
            logger.error(f"创建助手智能体失败: {e}")
            return None
    
    async def send_message(
        self,
        content: str,
        images: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        发送消息并获取流式响应
        
        Args:
            content: 消息内容
            images: 图片URL列表
            system_prompt: 自定义系统提示
            
        Yields:
            str: 响应内容片段
        """
        try:
            # 更新活动时间
            self.last_activity = datetime.now()
            
            # 创建用户消息
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=content,
                message_type=MessageType.MULTIMODAL if images else MessageType.TEXT,
                images=images,
                timestamp=datetime.now()
            )
            
            # 添加到消息历史
            self.messages.append(user_message)
            self.message_count += 1
            
            # 保存用户消息到聊天记忆
            if self.chat_memory:
                await self.chat_memory.add_message(
                    session_id=self.session_id,
                    role="user",
                    content=content,
                    metadata={"images": images} if images else None
                )
            
            # 创建或获取助手智能体
            if not self.assistant_agent:
                self.assistant_agent = await self._create_assistant_agent(system_prompt)
            
            if not self.assistant_agent:
                yield "抱歉，智能助手暂时不可用，请稍后再试。"
                return
            
            # 准备消息
            if images and self.config.enable_multimodal:
                # 多模态消息
                autogen_message = MultiModalMessage(
                    content=content,
                    source="user"
                )
            else:
                # 文本消息
                autogen_message = TextMessage(
                    content=content,
                    source="user"
                )
            
            # 流式处理响应
            full_response = ""
            async for chunk in self._stream_response([autogen_message]):
                full_response += chunk
                yield chunk
            
            # 创建AI回复消息
            ai_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_response,
                message_type=MessageType.TEXT,
                timestamp=datetime.now()
            )
            
            # 添加到消息历史
            self.messages.append(ai_message)
            self.message_count += 1
            
            # 保存AI回复到聊天记忆
            if self.chat_memory:
                await self.chat_memory.add_message(
                    session_id=self.session_id,
                    role="assistant",
                    content=full_response
                )
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            yield f"抱歉，处理您的消息时出现错误: {str(e)}"
    
    async def _stream_response(self, messages: List[Any]) -> AsyncGenerator[str, None]:
        """处理流式响应"""
        try:
            if not AUTOGEN_AVAILABLE or not self.assistant_agent:
                yield "智能助手不可用"
                return
            
            # 使用AutoGen的流式处理
            async for event in self.assistant_agent.on_messages_stream(messages):
                if hasattr(event, 'content') and event.content:
                    yield event.content
                elif hasattr(event, 'delta') and event.delta:
                    yield event.delta
                    
        except Exception as e:
            logger.error(f"流式响应处理失败: {e}")
            yield f"响应处理错误: {str(e)}"
    
    async def get_memory_context(self, limit: int = 10) -> MemoryContext:
        """获取记忆上下文"""
        try:
            context = MemoryContext()
            
            # 获取聊天历史
            if self.chat_memory:
                history_result = await self.chat_memory.query(
                    query="",
                    limit=limit,
                    session_id=self.session_id
                )
                context.chat_history = [
                    ChatMessage(
                        role=MessageRole(item.metadata.get("role", "user")),
                        content=item.content,
                        timestamp=item.timestamp
                    )
                    for item in history_result.items
                ]
            
            # 获取私有记忆
            if self.private_memory:
                private_result = await self.private_memory.query("用户偏好", limit=5)
                context.private_memories = [item.content for item in private_result.items]
            
            # 获取公共记忆
            if self.public_memory:
                public_result = await self.public_memory.query("常见问题", limit=5)
                context.public_memories = [item.content for item in public_result.items]
            
            return context
            
        except Exception as e:
            logger.error(f"获取记忆上下文失败: {e}")
            return MemoryContext()
    
    def get_session_info(self) -> SessionInfo:
        """获取会话信息"""
        return SessionInfo(
            session_id=self.session_id,
            user_id=self.user_id,
            created_at=self.created_at,
            last_activity=self.last_activity,
            message_count=self.message_count,
            status="active" if self.is_active else "inactive"
        )
    
    async def close(self):
        """关闭会话"""
        try:
            self.is_active = False
            
            # 关闭记忆服务
            if self.chat_memory:
                await self.chat_memory.close()
            if self.private_memory:
                await self.private_memory.close()
            if self.public_memory:
                await self.public_memory.close()
            
            logger.info(f"会话 {self.session_id} 已关闭")
            
        except Exception as e:
            logger.error(f"关闭会话失败: {e}")
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        timeout = timedelta(minutes=self.config.session_timeout_minutes)
        return datetime.now() - self.last_activity > timeout
