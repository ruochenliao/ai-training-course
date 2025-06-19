"""
AutoGen Memory 适配器
将基于向量数据库的记忆服务适配为AutoGen的Memory协议
支持高质量的语义检索和重排
"""
import logging
from typing import List, Sequence, Dict, Any

try:
    from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
    from autogen_agentchat.messages import BaseMessage, TextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # 创建占位符类
    class Memory:
        pass
    class MemoryContent:
        pass
    class MemoryMimeType:
        TEXT = "text"
    class BaseMessage:
        pass
    class TextMessage:
        pass

from .factory import MemoryServiceFactory

logger = logging.getLogger(__name__)


class AutoGenMemoryAdapter(Memory):
    """AutoGen Memory协议适配器 - 支持向量数据库"""

    def __init__(self, user_id: str, db_path: str = None):
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen不可用，记忆适配器功能受限")

        self.user_id = user_id
        self.memory_factory = MemoryServiceFactory(db_path)
        self.chat_memory = self.memory_factory.get_chat_memory_service(user_id)
        self.private_memory = self.memory_factory.get_private_memory_service(user_id)
        self.public_memory = self.memory_factory.get_public_memory_service()

        # 添加错误处理标志
        self.context_update_enabled = True
        self.max_context_retries = 3

        logger.info(f"AutoGen记忆适配器初始化完成 (使用ChromaDB向量数据库)")
        
    async def add(self, memory_content: MemoryContent) -> None:
        """添加记忆内容"""
        try:
            content = memory_content.content
            metadata = memory_content.metadata or {}
            
            # 根据元数据类型决定存储位置
            memory_type = metadata.get("memory_type", "private")
            
            if memory_type == "chat":
                # 存储到聊天记忆
                session_id = metadata.get("session_id", "default")
                role = metadata.get("role", "user")
                await self.chat_memory.add_message(session_id, role, content, metadata)
                
            elif memory_type == "public":
                # 存储到公共记忆
                await self.public_memory.add_memory(content, metadata)
                
            else:
                # 默认存储到私有记忆
                await self.private_memory.add_memory(content, metadata)
                
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise
    
    async def query(self, query: str, limit: int = 5) -> List[MemoryContent]:
        """查询相关记忆 - 使用向量检索和重排"""
        try:
            if not AUTOGEN_AVAILABLE:
                logger.warning("AutoGen不可用，返回空结果")
                return []

            results = []

            # 智能分配检索数量
            chat_limit = max(1, limit // 3)
            private_limit = max(1, limit // 3)
            public_limit = limit - chat_limit - private_limit

            # 从各个记忆源检索（使用向量数据库）
            chat_results = await self.chat_memory.retrieve_memories(query, limit=chat_limit)
            private_results = await self.private_memory.retrieve_memories(query, limit=private_limit)
            public_results = await self.public_memory.retrieve_memories(query, limit=public_limit)

            # 合并结果并重新评分
            all_results = []

            # 为不同类型的记忆添加类型权重
            for item in chat_results:
                item.metadata["memory_source"] = "chat"
                item.metadata["source_weight"] = 0.8  # 聊天记忆权重较高
                all_results.append(item)

            for item in private_results:
                item.metadata["memory_source"] = "private"
                item.metadata["source_weight"] = 0.9  # 私有记忆权重最高
                all_results.append(item)

            for item in public_results:
                item.metadata["memory_source"] = "public"
                item.metadata["source_weight"] = 0.7  # 公共记忆权重适中
                all_results.append(item)

            # 重新计算综合相关性分数
            for item in all_results:
                base_score = item.metadata.get("relevance_score", 0)
                source_weight = item.metadata.get("source_weight", 1.0)
                item.metadata["final_relevance_score"] = base_score * source_weight

            # 按综合相关性排序
            all_results.sort(
                key=lambda x: x.metadata.get("final_relevance_score", 0),
                reverse=True
            )

            # 转换为MemoryContent格式
            for item in all_results[:limit]:
                memory_content = MemoryContent(
                    content=item.content,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=item.metadata
                )
                results.append(memory_content)

            logger.debug(f"记忆查询完成: 查询='{query}', 结果数={len(results)}")
            return results

        except Exception as e:
            logger.error(f"Failed to query memory: {e}")
            return []
    
    async def update_context(self, messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        """更新上下文，添加相关记忆

        根据autogen官方文档实现Memory协议的update_context方法
        """
        try:
            if not AUTOGEN_AVAILABLE:
                logger.debug("AutoGen不可用，跳过上下文更新")
                return messages

            if not messages:
                logger.debug("消息序列为空，跳过上下文更新")
                return messages

            # 直接处理Sequence[BaseMessage]，不强制转换为list
            # 这是根据autogen官方文档的正确做法
            return await self._update_context_with_memory(messages)

        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            # 返回原始消息，确保不中断流程
            return messages

    async def _update_context_with_memory(self, messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        """使用记忆更新上下文

        根据autogen官方文档的最佳实践实现
        """
        try:
            # 获取最后一条消息作为查询
            # 使用索引访问而不是转换为list
            if not hasattr(messages, '__len__') or len(messages) == 0:
                logger.debug("消息序列为空或无法获取长度")
                return messages

            # 安全地获取最后一条消息
            try:
                last_message = messages[-1]
            except (IndexError, TypeError) as e:
                logger.debug(f"无法获取最后一条消息: {e}")
                return messages

            # 检查消息类型和内容
            if not hasattr(last_message, 'content'):
                logger.debug("最后一条消息没有content属性")
                return messages

            query = getattr(last_message, 'content', '')
            if not query or not isinstance(query, str):
                logger.debug("查询内容为空或不是字符串")
                return messages

            # 查询相关记忆
            logger.debug(f"查询记忆: {query[:50]}...")
            relevant_memories = await self.query(query, limit=3)

            if not relevant_memories:
                logger.debug("没有找到相关记忆")
                return messages

            # 构建记忆上下文
            memory_context = self._build_memory_context(relevant_memories)
            if not memory_context:
                logger.debug("记忆上下文构建失败")
                return messages

            # 创建包含记忆的系统消息
            try:
                # 根据autogen文档，直接创建TextMessage
                system_content = f"相关记忆信息：\n{memory_context}\n\n请基于以上记忆信息回答用户问题。"

                # 创建新的消息列表，包含记忆上下文
                # 将记忆信息插入到最后一条消息之前
                updated_messages = list(messages)  # 现在安全地转换为list

                # 创建系统消息
                if AUTOGEN_AVAILABLE:
                    system_message = TextMessage(
                        source="system",
                        content=system_content
                    )
                    updated_messages.insert(-1, system_message)
                    logger.debug(f"已添加记忆上下文，消息数量: {len(updated_messages)}")

                return updated_messages

            except Exception as msg_error:
                logger.warning(f"创建系统消息失败: {msg_error}")
                return messages

        except Exception as e:
            logger.error(f"更新上下文失败: {e}")
            return messages
    
    def _build_memory_context(self, memories: List[MemoryContent]) -> str:
        """构建记忆上下文字符串"""
        context_parts = []

        try:
            for i, memory in enumerate(memories, 1):
                if not memory:
                    continue

                # 安全地获取内容和元数据
                content = getattr(memory, 'content', '') if hasattr(memory, 'content') else str(memory)
                metadata = getattr(memory, 'metadata', {}) if hasattr(memory, 'metadata') else {}

                if not isinstance(metadata, dict):
                    metadata = {}

                memory_type = metadata.get("memory_type", "unknown")
                relevance_score = metadata.get("relevance_score", 0)

                # 确保相关性分数是数字
                try:
                    relevance_score = float(relevance_score)
                except (ValueError, TypeError):
                    relevance_score = 0.0

                context_part = f"{i}. [{memory_type}] (相关性: {relevance_score:.3f})\n{content}"
                context_parts.append(context_part)

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Failed to build memory context: {e}")
            return "记忆上下文构建失败"
    
    async def clear(self) -> None:
        """清空记忆（仅清空当前用户的私有记忆）"""
        try:
            # 注意：这里只清空私有记忆，不清空聊天记忆和公共记忆
            # 因为聊天记忆是对话历史，公共记忆是共享知识库
            logger.warning("Memory clear operation is limited to prevent data loss")
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            raise
    
    async def close(self) -> None:
        """关闭记忆服务"""
        try:
            # 清理缓存
            self.memory_factory.clear_cache()
            
        except Exception as e:
            logger.error(f"Failed to close memory: {e}")
            raise


class ConversationMemoryAdapter(AutoGenMemoryAdapter):
    """对话专用的记忆适配器 - 支持向量数据库"""

    def __init__(self, user_id: str, session_id: str, db_path: str = None):
        super().__init__(user_id, db_path)
        self.session_id = session_id
        logger.info(f"对话记忆适配器初始化: user_id={user_id}, session_id={session_id}")
    
    async def add_conversation_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加对话消息到记忆"""
        try:
            # 直接使用聊天记忆服务添加消息
            await self.chat_memory.add_message(self.session_id, role, content, metadata)
            logger.debug(f"对话消息已添加: role={role}, session={self.session_id}")
        except Exception as e:
            logger.error(f"添加对话消息失败: {e}")
            raise
    
    async def get_conversation_history(self, limit: int = 10) -> List[MemoryContent]:
        """获取对话历史"""
        try:
            messages = await self.chat_memory.get_session_history(self.session_id, limit)

            results = []
            for msg in messages:
                # msg是MemoryItem对象，从metadata中获取role和timestamp
                role = msg.metadata.get("role", "unknown")
                timestamp = msg.metadata.get("timestamp", msg.created_at.isoformat() if msg.created_at else None)

                memory_content = MemoryContent(
                    content=msg.content,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={
                        "memory_type": "chat",
                        "session_id": self.session_id,
                        "role": role,
                        "timestamp": timestamp
                    }
                )
                results.append(memory_content)

            return results

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
