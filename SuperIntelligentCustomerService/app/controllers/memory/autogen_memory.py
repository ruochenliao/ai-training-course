"""
AutoGen Memory 适配器
将基于向量数据库的记忆服务适配为AutoGen的Memory协议
支持高质量的语义检索和重排
"""
import logging
from datetime import datetime
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
            logger.info("聊天记忆服务初始化成功")

            # 尝试初始化向量记忆服务，如果失败则禁用
            try:
                self.private_memory = self.memory_factory.get_private_memory_service(user_id)
                logger.info("私有记忆服务初始化成功")
            except Exception as private_error:
                logger.warning(f"私有记忆服务初始化失败，将禁用: {private_error}")
                self.private_memory = None

            try:
                self.public_memory = self.memory_factory.get_public_memory_service()
                logger.info("公共记忆服务初始化成功")
            except Exception as public_error:
                logger.warning(f"公共记忆服务初始化失败，将禁用: {public_error}")
                self.public_memory = None

        except Exception as e:
            logger.error(f"初始化记忆服务失败: {e}")
            raise

        # 配置参数
        self.context_update_enabled = True
        self.max_context_retries = 3
        self.default_query_limit = 5
        self.memory_enabled = True  # 记忆功能启用状态

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

        根据Microsoft AutoGen官方文档，这个方法会被框架自动调用
        来存储对话中的消息和其他相关信息

        Args:
            memory_content: 记忆内容对象
        """
        try:
            self.operation_stats["add_operations"] += 1

            content = memory_content.content
            metadata = memory_content.metadata or {}

            # 智能检测内容类型和来源
            # AutoGen框架会自动传入对话消息，我们需要智能分类
            memory_type = self._detect_memory_type(content, metadata)

            # 增强元数据
            enhanced_metadata = {
                **metadata,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "auto_detected_type": memory_type
            }

            if memory_type == "chat":
                # 存储到聊天记忆
                session_id = enhanced_metadata.get("session_id", "default")
                role = enhanced_metadata.get("role", "user")
                await self.chat_memory.add(content, {
                    **enhanced_metadata,
                    "session_id": session_id,
                    "role": role
                })

            elif memory_type == "public" and self.public_memory:
                # 存储到公共记忆（如果可用）
                await self.public_memory.add(content, enhanced_metadata)

            elif self.private_memory:
                # 默认存储到私有记忆（如果可用）
                await self.private_memory.add(content, enhanced_metadata)
            else:
                # 如果向量记忆不可用，存储到聊天记忆
                logger.warning("向量记忆服务不可用，将内容存储到聊天记忆")
                await self.chat_memory.add(content, enhanced_metadata)

            logger.debug(f"成功添加记忆内容到 {memory_type} 存储: {content[:50]}...")

        except Exception as e:
            self.operation_stats["error_count"] += 1
            logger.error(f"添加记忆内容失败: {e}")
            # 不抛出异常，避免中断AutoGen框架的正常流程

    def _detect_memory_type(self, content: str, metadata: dict) -> str:
        """智能检测记忆类型"""
        # 如果元数据中已指定类型，优先使用
        if "memory_type" in metadata:
            return metadata["memory_type"]

        # 根据内容和元数据智能判断
        role = metadata.get("role", "")

        # 如果是对话消息，存储到聊天记忆
        if role in ["user", "assistant"]:
            return "chat"

        # 如果包含用户偏好或设置信息，存储到私有记忆
        preference_keywords = ["偏好", "设置", "配置", "喜欢", "不喜欢", "习惯"]
        if any(keyword in content for keyword in preference_keywords):
            return "private"

        # 默认存储到私有记忆
        return "private"
    
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

            # 只有在服务可用时才查询向量记忆
            if self.private_memory:
                private_query_result = await self.private_memory.query(query, limit=private_limit)
            else:
                from .base import QueryResult
                private_query_result = QueryResult(items=[], total_count=0, query_time=0.0)

            if self.public_memory:
                public_query_result = await self.public_memory.query(query, limit=public_limit)
            else:
                from .base import QueryResult
                public_query_result = QueryResult(items=[], total_count=0, query_time=0.0)

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
                    "source_weight": 1.5,  # 私有记忆权重大幅提高，确保优先级
                    "query_time": private_query_result.query_time
                })
                all_results.append(item)

            for item in public_query_result.items:
                item.metadata.update({
                    "memory_source": "public",
                    "source_weight": 0.6,  # 公共记忆权重降低
                    "query_time": public_query_result.query_time
                })
                all_results.append(item)  # 修复：添加公共记忆结果到总结果列表

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

        根据Microsoft AutoGen官方文档实现Memory协议的update_context方法
        这个方法会在AssistantAgent处理消息前被调用，用于注入相关的记忆信息
        参考: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
        """
        try:
            if not AUTOGEN_AVAILABLE:
                logger.debug("AutoGen不可用，跳过上下文更新")
                return messages

            if not messages:
                logger.debug("消息序列为空，跳过上下文更新")
                return messages

            # 根据官方文档，update_context方法应该查询相关记忆并添加到上下文中
            return await self._update_context_with_memory(messages)

        except Exception as e:
            logger.error(f"更新上下文失败: {e}")
            # 返回原始消息，确保不中断流程
            return messages

    async def _update_context_with_memory(self, messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        """使用记忆更新上下文

        根据Microsoft AutoGen官方文档的最佳实践实现
        参考: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
        """
        try:
            # 获取最后一条用户消息作为查询
            if not hasattr(messages, '__len__') or len(messages) == 0:
                logger.debug("消息序列为空或无法获取长度")
                return messages

            # 查找最后一条用户消息
            query_content = ""
            for message in reversed(messages):
                if hasattr(message, 'source') and message.source == 'user':
                    query_content = getattr(message, 'content', '')
                    break

            if not query_content or not isinstance(query_content, str):
                logger.debug("没有找到有效的用户消息内容")
                return messages

            # 查询相关记忆
            logger.debug(f"查询记忆: {query_content[:50]}...")
            relevant_memories = await self.query(query_content, limit=3)

            if not relevant_memories:
                logger.debug("没有找到相关记忆")
                return messages

            # 构建记忆上下文字符串
            memory_context = self._build_memory_context(relevant_memories)
            if not memory_context:
                logger.debug("记忆上下文构建失败")
                return messages

            # 根据AutoGen官方文档，创建系统消息来注入记忆信息
            try:
                from autogen_agentchat.messages import SystemMessage

                # 创建包含记忆信息的系统消息，强调知识库内容的重要性
                memory_system_message = SystemMessage(
                    content=f"""
## 重要：以下是与用户问题相关的记忆内容

{memory_context}

**使用指导：**
1. 如果上述内容包含"相关知识库内容"，这是最权威的信息来源，必须优先使用
2. 严格基于知识库内容回答，不要添加或修改信息
3. 如果知识库内容不完整，可以结合其他记忆内容补充
4. 在回答中明确标注信息来源（知识库/个人信息/对话历史）
""",
                    type="SystemMessage"
                )

                # 将系统消息插入到消息序列中
                # 根据官方文档，系统消息应该在用户消息之后添加
                updated_messages = list(messages)
                updated_messages.append(memory_system_message)

                logger.debug(f"已添加记忆系统消息，总消息数量: {len(updated_messages)}")
                return updated_messages

            except ImportError:
                # 如果无法导入SystemMessage，使用TextMessage作为替代
                logger.warning("无法导入SystemMessage，使用TextMessage替代")

                memory_message = TextMessage(
                    source="system",
                    content=f"""
## 重要：以下是与用户问题相关的记忆内容

{memory_context}

**使用指导：**
1. 如果上述内容包含"相关知识库内容"，这是最权威的信息来源，必须优先使用
2. 严格基于知识库内容回答，不要添加或修改信息
3. 如果知识库内容不完整，可以结合其他记忆内容补充
4. 在回答中明确标注信息来源（知识库/个人信息/对话历史）
"""
                )

                updated_messages = list(messages)
                updated_messages.append(memory_message)

                logger.debug(f"已添加记忆文本消息，总消息数量: {len(updated_messages)}")
                return updated_messages

        except Exception as e:
            logger.error(f"更新上下文失败: {e}")
            return messages
    
    def _build_memory_context(self, memories: List[MemoryContent]) -> str:
        """构建记忆上下文字符串

        根据Microsoft AutoGen官方文档的格式构建记忆上下文
        增强知识库内容的处理和展示
        """
        if not memories:
            return ""

        # 分类记忆内容
        knowledge_base_memories = []
        chat_memories = []
        private_memories = []

        try:
            for memory in memories:
                if not memory:
                    continue

                # 安全地获取内容和元数据
                content = getattr(memory, 'content', '') if hasattr(memory, 'content') else str(memory)
                metadata = getattr(memory, 'metadata', {}) if hasattr(memory, 'metadata') else {}

                if not isinstance(metadata, dict):
                    metadata = {}

                # 根据来源分类记忆
                source = metadata.get('source', 'unknown')
                memory_type = metadata.get('content_type', 'unknown')

                memory_info = {
                    'content': content,
                    'metadata': metadata,
                    'source': source,
                    'type': memory_type,
                    'relevance_score': metadata.get('relevance_score', 0)
                }

                # 分类存储
                if 'knowledge' in memory_type.lower() or 'document' in source.lower():
                    knowledge_base_memories.append(memory_info)
                elif 'chat' in source.lower() or 'conversation' in source.lower():
                    chat_memories.append(memory_info)
                else:
                    private_memories.append(memory_info)

            # 构建分类的上下文
            context_parts = []

            # 1. 知识库内容（最重要，放在前面）
            if knowledge_base_memories:
                context_parts.append("## 相关知识库内容（重要参考）：")
                for i, memory in enumerate(knowledge_base_memories, 1):
                    title = memory['metadata'].get('title', f'知识条目{i}')
                    category = memory['metadata'].get('category', '通用')
                    score = memory['relevance_score']

                    context_part = f"### {i}. {title} (分类: {category}, 相关度: {score:.3f})\n{memory['content']}"
                    context_parts.append(context_part)
                context_parts.append("")  # 添加空行分隔

            # 2. 个人相关信息
            if private_memories:
                context_parts.append("## 个人相关信息：")
                for i, memory in enumerate(private_memories, 1):
                    context_part = f"{i}. {memory['content']}"
                    context_parts.append(context_part)
                context_parts.append("")  # 添加空行分隔

            # 3. 对话历史（简化显示）
            if chat_memories:
                context_parts.append("## 相关对话历史：")
                for i, memory in enumerate(chat_memories[:3], 1):  # 只显示最相关的3条
                    context_part = f"{i}. {memory['content'][:100]}..."  # 截断长内容
                    context_parts.append(context_part)

            result = "\n".join(context_parts)

            # 记录构建的上下文信息用于调试
            logger.debug(f"构建记忆上下文完成 - 知识库: {len(knowledge_base_memories)}, 私有: {len(private_memories)}, 聊天: {len(chat_memories)}")

            return result

        except Exception as e:
            logger.error(f"构建记忆上下文失败: {e}")
            return ""
    
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

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_info = {
                "user_id": self.user_id,
                "memory_enabled": self.memory_enabled,
                "operation_stats": self.operation_stats.copy(),
                "services": {}
            }

            # 检查各个记忆服务的健康状态
            if self.chat_memory:
                health_info["services"]["chat_memory"] = await self.chat_memory.health_check()

            if self.private_memory:
                health_info["services"]["private_memory"] = await self.private_memory.health_check()

            if self.public_memory:
                health_info["services"]["public_memory"] = await self.public_memory.health_check()

            return health_info

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "user_id": self.user_id,
                "memory_enabled": False,
                "error": str(e)
            }


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

            if self.private_memory:
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
