"""
智能客服聊天服务
集成AutoGen框架，支持多记忆融合的聊天服务
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator, Any

try:
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo, ModelFamily
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    class OpenAIChatCompletionClient:
        def __init__(self, *args, **kwargs): pass

from .chat_session import ChatSession
from ..schemas.chat_service import (
    ChatRequest, ChatResponse, StreamChunk, SessionInfo, 
    SessionStats, ChatServiceConfig, ChatMessage, MessageRole
)

logger = logging.getLogger(__name__)


class ChatService:
    """
    智能客服聊天服务核心类
    管理多用户会话，集成AutoGen框架和多记忆服务
    """
    
    def __init__(self, config: Optional[ChatServiceConfig] = None):
        """
        初始化聊天服务
        
        Args:
            config: 服务配置
        """
        self.config = config or ChatServiceConfig()
        
        # 会话管理
        self.sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        
        # 记忆服务工厂
        self.memory_factory = None
        
        # 模型客户端
        self.model_client = None
        
        # 服务统计
        self.stats = SessionStats()
        
        # 延迟初始化标志
        self._initialized = False
        
        logger.info("聊天服务初始化完成")

    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self._init_service()
            self._initialized = True
    
    async def _init_service(self):
        """初始化服务组件"""
        try:
            # 初始化记忆服务工厂
            await self._init_memory_factory()
            
            # 初始化模型客户端
            await self._init_model_client()
            
            # 启动清理任务
            asyncio.create_task(self._cleanup_expired_sessions())
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise
    
    async def _init_memory_factory(self):
        """初始化记忆服务工厂"""
        try:
            # 导入记忆服务工厂
            from .memory import MemoryServiceFactory

            self.memory_factory = MemoryServiceFactory()
            logger.info("记忆服务工厂初始化完成")

        except ImportError as e:
            logger.error(f"记忆服务工厂导入失败: {e}")
            self.memory_factory = None
        except Exception as e:
            logger.error(f"记忆服务工厂初始化失败: {e}")
            self.memory_factory = None
    
    async def _init_model_client(self):
        """初始化模型客户端"""
        try:
            if not AUTOGEN_AVAILABLE:
                logger.warning("AutoGen不可用，模型客户端功能受限")
                return
            
            # 从配置或环境变量获取模型配置
            import os
            
            # 创建模型信息
            model_info = ModelInfo(
                vision=True,  # 支持视觉功能
                function_calling=True,  # 支持函数调用
                json_output=True,  # 支持JSON输出
                structured_output=True,  # 支持结构化输出
                family=ModelFamily.UNKNOWN,
                multiple_system_messages=True
            )
            
            # 创建OpenAI兼容客户端
            self.model_client = OpenAIChatCompletionClient(
                model=self.config.default_model,
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                api_key=os.getenv("DEEPSEEK_API_KEY", "sk-56f5743d59364543a00109a4c1c10a56"),
                model_info=model_info,
                timeout=60,
                max_retries=3
            )
            
            logger.info(f"模型客户端初始化完成: {self.config.default_model}")
            
        except Exception as e:
            logger.error(f"模型客户端初始化失败: {e}")
            # 不抛出异常，允许服务在没有模型客户端的情况下运行
    
    async def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> ChatSession:
        """
        获取或创建聊天会话

        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则创建新会话

        Returns:
            ChatSession: 聊天会话实例
        """
        try:
            # 确保服务已初始化
            await self._ensure_initialized()
            # 如果没有提供session_id，创建新的
            if not session_id:
                session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
            
            session_key = f"{user_id}_{session_id}"
            
            # 检查会话是否已存在
            if session_key in self.sessions:
                session = self.sessions[session_key]
                # 检查会话是否过期
                if session.is_expired():
                    await self._remove_session(session_key)
                else:
                    return session
            
            # 检查用户会话数量限制
            user_session_count = len(self.user_sessions.get(user_id, []))
            if user_session_count >= self.config.max_sessions_per_user:
                # 移除最旧的会话
                await self._remove_oldest_user_session(user_id)
            
            # 创建新会话
            session = ChatSession(
                user_id=user_id,
                session_id=session_id,
                memory_factory=self.memory_factory,
                model_client=self.model_client,
                config=self.config
            )
            
            # 注册会话
            self.sessions[session_key] = session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_key)
            
            # 更新统计
            self.stats.total_sessions += 1
            self.stats.active_sessions += 1
            
            logger.info(f"创建新会话: {session_key}")
            return session
            
        except Exception as e:
            logger.error(f"获取或创建会话失败: {e}")
            raise
    
    async def send_message(self, request: ChatRequest) -> AsyncGenerator[StreamChunk, None]:
        """
        发送消息并获取流式响应
        
        Args:
            request: 聊天请求
            
        Yields:
            StreamChunk: 流式响应块
        """
        try:
            # 获取或创建会话
            session = await self.get_or_create_session(
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            # 生成块ID
            chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"
            
            # 发送消息并获取流式响应
            full_response = ""
            async for content_chunk in session.send_message(
                content=request.message,
                images=request.images,
                system_prompt=request.system_prompt
            ):
                full_response += content_chunk
                
                # 创建流式响应块
                chunk = StreamChunk(
                    chunk_id=chunk_id,
                    session_id=session.session_id,
                    content=content_chunk,
                    is_final=False,
                    metadata={
                        "user_id": request.user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                yield chunk
            
            # 发送最终块
            final_chunk = StreamChunk(
                chunk_id=chunk_id,
                session_id=session.session_id,
                content="",
                is_final=True,
                metadata={
                    "user_id": request.user_id,
                    "full_response": full_response,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            yield final_chunk
            
            # 更新统计
            self.stats.total_messages += 1
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            # 发送错误响应
            error_chunk = StreamChunk(
                chunk_id=f"error_{uuid.uuid4().hex[:8]}",
                session_id=request.session_id or "unknown",
                content=f"抱歉，处理您的消息时出现错误: {str(e)}",
                is_final=True,
                metadata={
                    "error": True,
                    "error_message": str(e)
                }
            )
            yield error_chunk
    
    async def get_session_info(self, user_id: str, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        session_key = f"{user_id}_{session_id}"
        session = self.sessions.get(session_key)
        
        if session:
            return session.get_session_info()
        return None
    
    async def list_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """列出用户的所有会话"""
        session_keys = self.user_sessions.get(user_id, [])
        sessions_info = []
        
        for session_key in session_keys:
            session = self.sessions.get(session_key)
            if session:
                sessions_info.append(session.get_session_info())
        
        return sessions_info
    
    async def close_session(self, user_id: str, session_id: str) -> bool:
        """关闭指定会话"""
        session_key = f"{user_id}_{session_id}"
        return await self._remove_session(session_key)
    
    async def _remove_session(self, session_key: str) -> bool:
        """移除会话"""
        try:
            session = self.sessions.get(session_key)
            if session:
                await session.close()
                del self.sessions[session_key]
                
                # 从用户会话列表中移除
                user_id = session.user_id
                if user_id in self.user_sessions:
                    if session_key in self.user_sessions[user_id]:
                        self.user_sessions[user_id].remove(session_key)
                    
                    # 如果用户没有其他会话，移除用户记录
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]
                
                # 更新统计
                self.stats.active_sessions = max(0, self.stats.active_sessions - 1)
                
                logger.info(f"移除会话: {session_key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"移除会话失败: {e}")
            return False
    
    async def _remove_oldest_user_session(self, user_id: str):
        """移除用户最旧的会话"""
        session_keys = self.user_sessions.get(user_id, [])
        if session_keys:
            oldest_key = session_keys[0]  # 假设列表按创建时间排序
            await self._remove_session(oldest_key)
    
    async def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟检查一次
                
                expired_sessions = []
                for session_key, session in self.sessions.items():
                    if session.is_expired():
                        expired_sessions.append(session_key)
                
                for session_key in expired_sessions:
                    await self._remove_session(session_key)
                
                if expired_sessions:
                    logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
                    
            except Exception as e:
                logger.error(f"清理过期会话失败: {e}")
    
    async def get_service_stats(self) -> SessionStats:
        """获取服务统计信息"""
        # 更新当前统计
        self.stats.active_sessions = len(self.sessions)
        
        # 计算平均会话长度
        if self.stats.total_sessions > 0:
            total_messages = sum(
                session.message_count for session in self.sessions.values()
            )
            self.stats.average_session_length = total_messages / self.stats.total_sessions
        
        # 获取记忆使用情况
        if self.memory_factory:
            try:
                health_info = await self.memory_factory.health_check()
                self.stats.memory_usage = health_info
            except Exception as e:
                logger.error(f"获取记忆使用情况失败: {e}")
        
        return self.stats
    
    async def close(self):
        """关闭服务"""
        try:
            # 关闭所有会话
            for session_key in list(self.sessions.keys()):
                await self._remove_session(session_key)
            
            # 关闭记忆服务工厂
            if self.memory_factory:
                await self.memory_factory.close_all_services()
            
            logger.info("聊天服务已关闭")
            
        except Exception as e:
            logger.error(f"关闭聊天服务失败: {e}")


# 全局聊天服务实例
chat_service = ChatService()
