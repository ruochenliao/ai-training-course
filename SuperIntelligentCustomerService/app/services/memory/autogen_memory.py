"""
AutoGen Memory 适配器
将基于向量数据库的记忆服务适配为AutoGen的Memory协议
支持高质量的语义检索和重排
"""
import logging
from typing import List, Dict, Any

try:
    from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
    from autogen_agentchat.messages import BaseMessage, TextMessage
    from typing import Sequence
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # 创建占位符类
    class Memory:
        async def add(self, memory_content): pass
        async def query(self, query, limit=5): return []
        async def update_context(self, messages): return messages
        async def clear(self): pass
        async def close(self): pass
    class MemoryContent:
        def __init__(self, content, mime_type=None, metadata=None):
            self.content = content
            self.mime_type = mime_type
            self.metadata = metadata or {}
    class MemoryMimeType:
        TEXT = "text"
    class BaseMessage:
        def __init__(self, content=""):
            self.content = content
    class TextMessage(BaseMessage):
        def __init__(self, source="", content=""):
            super().__init__(content)
            self.source = source
    from typing import Sequence

from .factory import MemoryServiceFactory

logger = logging.getLogger(__name__)


class AutoGenMemoryAdapter(Memory):
    """
    AutoGen Memory协议适配器
    支持向量数据库和增强的记忆管理功能，基于新的BaseMemoryService架构
    """

    def __init__(self, user_id: str, db_path: str = None):
        """
        初始化AutoGen记忆适配器

        Args:
            user_id: 用户ID
            db_path: 数据库路径
        """
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen不可用，记忆适配器功能受限")

        self.user_id = user_id
        self.memory_factory = MemoryServiceFactory(db_path)

        # 初始化各类记忆服务
        try:
            self.chat_memory = self.memory_factory.get_chat_memory_service(user_id)
            self.private_memory = self.memory_factory.get_private_memory_service(user_id)
            self.public_memory = self.memory_factory.get_public_memory_service()
        except Exception as e:
            logger.error(f"初始化记忆服务失败: {e}")
            raise

        # 配置参数
        self.context_update_enabled = True
        self.max_context_retries = 3
        self.default_query_limit = 5

        # 统计信息
        self.operation_stats = {
            "add_operations": 0,
            "query_operations": 0,
            "update_operations": 0,
            "clear_operations": 0,
            "error_count": 0
        }

        logger.info(f"AutoGen记忆适配器初始化完成 (用户: {user_id})")
        
    async def add(self, memory_content: MemoryContent) -> None:
        """
        添加记忆内容（实现AutoGen Memory接口）

        Args:
            memory_content: 记忆内容对象
        """
        try:
            self.operation_stats["add_operations"] += 1

            content = memory_content.content
            metadata = memory_content.metadata or {}

            # 根据元数据类型决定存储位置
            memory_type = metadata.get("memory_type", "private")

            if memory_type == "chat":
                # 存储到聊天记忆
                session_id = metadata.get("session_id", "default")
                role = metadata.get("role", "user")
                await self.chat_memory.add(content, {
                    **metadata,
                    "session_id": session_id,
                    "role": role
                })

            elif memory_type == "public":
                # 存储到公共记忆
                await self.public_memory.add(content, metadata)

            else:
                # 默认存储到私有记忆
                await self.private_memory.add(content, metadata)

            logger.debug(f"成功添加记忆内容到 {memory_type} 存储")

        except Exception as e:
            self.operation_stats["error_count"] += 1
            logger.error(f"添加记忆内容失败: {e}")
            raise
    
    async def query(self, query: str, limit: int = 5) -> List[MemoryContent]:
        """
        查询相关记忆（实现AutoGen Memory接口）
        使用向量检索和智能重排，支持多源记忆融合

        Args:
            query: 查询内容
            limit: 返回数量限制

        Returns:
            记忆内容列表
        """
        try:
            self.operation_stats["query_operations"] += 1

            if not AUTOGEN_AVAILABLE:
                logger.warning("AutoGen不可用，返回空结果")
                return []

            # 智能分配检索数量
            chat_limit = max(1, limit // 3)
            private_limit = max(1, limit // 3)
            public_limit = limit - chat_limit - private_limit

            # 并行从各个记忆源检索
            chat_query_result = await self.chat_memory.query(query, limit=chat_limit)
            private_query_result = await self.private_memory.query(query, limit=private_limit)
            public_query_result = await self.public_memory.query(query, limit=public_limit)

            # 合并结果并重新评分
            all_results = []

            # 为不同类型的记忆添加类型权重和来源标识
            for item in chat_query_result.items:
                item.metadata.update({
                    "memory_source": "chat",
                    "source_weight": 0.8,  # 聊天记忆权重较高
                    "query_time": chat_query_result.query_time
                })
                all_results.append(item)

            for item in private_query_result.items:
                item.metadata.update({
                    "memory_source": "private",
                    "source_weight": 0.9,  # 私有记忆权重最高
                    "query_time": private_query_result.query_time
                })
                all_results.append(item)

            for item in public_query_result.items:
                item.metadata.update({
                    "memory_source": "public",
                    "source_weight": 0.7,  # 公共记忆权重较低
                    "query_time": public_query_result.query_time
                })
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
            results = []
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
            self.operation_stats["error_count"] += 1
            logger.error(f"查询记忆失败: {e}")
            return []
    
    async def update_context(self, messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        """更新上下文，添加相关记忆

        根据autogen 0.6.1官方文档实现Memory协议的update_context方法
        这个方法会在AssistantAgent处理消息前被调用，用于注入相关的记忆信息
        """
        try:
            if not AUTOGEN_AVAILABLE:
                logger.debug("AutoGen不可用，跳过上下文更新")
                return messages

            if not messages:
                logger.debug("消息序列为空，跳过上下文更新")
                return messages

            # 在autogen 0.6.1中，update_context方法负责修改消息序列
            # 添加相关的记忆信息到上下文中
            return await self._update_context_with_memory(messages)

        except Exception as e:
            logger.error(f"更新上下文失败: {e}")
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

            # 将记忆信息注入到现有消息中，而不是创建新的系统消息
            try:
                # 在autogen 0.6.1中，为了避免多个系统消息的问题，
                # 我们将记忆信息添加到用户消息的开头
                updated_messages = list(messages)

                if updated_messages and AUTOGEN_AVAILABLE:
                    # 找到最后一条用户消息并在其内容前添加记忆信息
                    for i in range(len(updated_messages) - 1, -1, -1):
                        message = updated_messages[i]
                        if hasattr(message, 'source') and message.source == 'user':
                            # 在用户消息内容前添加记忆上下文
                            enhanced_content = f"[记忆信息]\n{memory_context}\n\n[用户问题]\n{message.content}"

                            # 创建新的用户消息，包含记忆信息
                            enhanced_message = TextMessage(
                                source="user",
                                content=enhanced_content
                            )
                            updated_messages[i] = enhanced_message
                            logger.debug(f"已将记忆上下文注入到用户消息中，总消息数量: {len(updated_messages)}")
                            break

                return updated_messages

            except Exception as msg_error:
                logger.warning(f"注入记忆信息失败: {msg_error}")
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

    async def clear(self) -> None:
        """
        清空所有记忆内容（实现AutoGen Memory接口）
        """
        try:
            self.operation_stats["clear_operations"] += 1

            # 清空所有记忆服务
            await self.chat_memory.clear()
            await self.private_memory.clear()
            # 注意：通常不清空公共记忆，因为它是共享的

            logger.info(f"已清空用户 {self.user_id} 的所有记忆")

        except Exception as e:
            self.operation_stats["error_count"] += 1
            logger.error(f"清空记忆失败: {e}")
            raise

    async def close(self) -> None:
        """
        关闭记忆适配器，释放资源（实现AutoGen Memory接口）
        """
        try:
            # 关闭所有记忆服务
            await self.memory_factory.close_all_services()
            logger.info(f"AutoGen记忆适配器已关闭 (用户: {self.user_id})")

        except Exception as e:
            logger.error(f"关闭记忆适配器失败: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        Returns:
            健康检查结果
        """
        try:
            factory_health = await self.memory_factory.health_check()

            return {
                "adapter_status": "healthy",
                "user_id": self.user_id,
                "operation_stats": self.operation_stats.copy(),
                "autogen_available": AUTOGEN_AVAILABLE,
                "context_update_enabled": self.context_update_enabled,
                "factory_health": factory_health
            }

        except Exception as e:
            return {
                "adapter_status": "error",
                "user_id": self.user_id,
                "error": str(e),
                "operation_stats": self.operation_stats.copy()
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取适配器统计信息

        Returns:
            统计信息
        """
        return {
            "user_id": self.user_id,
            "operation_stats": self.operation_stats.copy(),
            "autogen_available": AUTOGEN_AVAILABLE,
            "context_update_enabled": self.context_update_enabled,
            "max_context_retries": self.max_context_retries,
            "default_query_limit": self.default_query_limit
        }
