"""
聊天控制器
基于autogen 0.6.1和Deepseek模型实现智能客服功能
集成记忆服务提供上下文感知能力
"""
import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Optional, AsyncGenerator, Tuple, Dict, Any

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent, \
    ModelClientStreamingChunkEvent, ToolCallSummaryMessage
from fastapi import HTTPException

from app.core.llm_config import deepseek_config
from app.models.admin import ChatConversation, ChatMessage
from app.schemas.chat import (
    SendMessageRequest,
    StreamMessageChunk
)
from app.services.memory import ConversationMemoryAdapter


class ChatController:
    """聊天控制器"""

    def __init__(self):
        # 对话历史缓存: {conversation_id: message_list}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        # 记忆适配器缓存: {conversation_id: memory_adapter}
        self.memory_adapters: Dict[str, ConversationMemoryAdapter] = {}
        # 设置模型请求超时时间（秒）
        self.model_timeout = 120

    def get_assistant_with_memory(self, user_id: int, conversation_id: str):
        """获取带记忆功能的助手实例"""
        # 创建或获取记忆适配器
        if conversation_id not in self.memory_adapters:
            self.memory_adapters[conversation_id] = ConversationMemoryAdapter(
                user_id=str(user_id),
                session_id=conversation_id
            )

        memory_adapter = self.memory_adapters[conversation_id]

        # 创建带记忆功能的助手
        assistant = deepseek_config.get_assistant(memory_adapters=[memory_adapter])

        return assistant, memory_adapter

    async def create_conversation(self, user_id: int, title: str = "") -> ChatConversation:
        """创建新对话"""
        conversation_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        conversation = await ChatConversation.create(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title or "新对话",
            is_active=True,
            last_message_at=datetime.now()
        )
        
        # 初始化会话历史
        self.conversation_history[conversation_id] = []

        return conversation

    async def get_conversation(self, conversation_id: str, user_id: int) -> Optional[ChatConversation]:
        """获取对话"""
        return await ChatConversation.filter(
            conversation_id=conversation_id,
            user_id=user_id
        ).first()

    async def get_user_conversations(
            self,
            user_id: int,
            page: int = 1,
            page_size: int = 20
    ) -> Tuple[int, List[ChatConversation]]:
        """获取用户对话列表"""
        offset = (page - 1) * page_size

        total = await ChatConversation.filter(user_id=user_id).count()
        conversations = await ChatConversation.filter(
            user_id=user_id
        ).order_by('-last_message_at').offset(offset).limit(page_size)

        return total, conversations

    async def save_message(
            self,
            conversation_id: str,
            user_id: int,
            content: str,
            sender: str,
            message_type: str = "text",
            tokens_used: int = 0,
            response_time: int = 0
    ) -> ChatMessage:
        """保存消息"""
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        message = await ChatMessage.create(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            sender=sender,
            content=content,
            message_type=message_type,
            tokens_used=tokens_used,
            response_time=response_time
        )

        # 更新对话的最后消息时间
        await ChatConversation.filter(
            conversation_id=conversation_id
        ).update(last_message_at=datetime.now())

        return message

    async def get_conversation_messages(
            self,
            conversation_id: str,
            user_id: int,
            limit: int = 50
    ) -> List[ChatMessage]:
        """获取对话消息历史"""
        messages = await ChatMessage.filter(
            conversation_id=conversation_id,
            user_id=user_id
        ).order_by('created_at').limit(limit)
        
        # 如果不在内存缓存中，则加载历史记录到缓存
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
            for msg in messages:
                self.conversation_history[conversation_id].append({
                    "role": msg.sender,
                    "content": msg.content
                })
                
        return messages

    async def _prepare_conversation_history(self, conversation_id: str, user_id: int) -> None:
        """准备对话历史以供模型使用"""
        if conversation_id not in self.conversation_history:
            await self.get_conversation_messages(conversation_id, user_id)

    async def send_message_stream(
            self,
            request: SendMessageRequest,
            user_id: int
    ) -> AsyncGenerator[StreamMessageChunk, None]:
        """发送消息并返回流式响应（使用Deepseek模型和记忆服务）"""
        start_time = time.time()

        # 获取或创建对话
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = await self.create_conversation(user_id)

        # 获取带记忆功能的助手
        assistant, memory_adapter = self.get_assistant_with_memory(user_id, conversation.conversation_id)

        # 准备对话历史
        await self._prepare_conversation_history(conversation.conversation_id, user_id)

        # 保存用户消息
        user_message = await self.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            content=request.message,
            sender="user"
        )

        # 添加用户消息到记忆服务
        await memory_adapter.add_conversation_message(
            role="user",
            content=request.message,
            metadata={"message_id": user_message.message_id}
        )

        # 更新对话历史
        if conversation.conversation_id not in self.conversation_history:
            self.conversation_history[conversation.conversation_id] = []
        self.conversation_history[conversation.conversation_id].append({
            "role": "user",
            "content": request.message
        })

        # 不发送用户消息回显，避免重复显示

        # 创建用户消息对象
        user_task = TextMessage(source="user", content=request.message)

        # 生成助手消息ID
        assistant_message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # 流式响应处理变量
        response_content = ""
        total_tokens_used = 0
        tool_call_status_sent = False

        # 内容缓冲区，用于优化分块
        content_buffer = ""
        buffer_size_threshold = 10  # 缓冲区大小阈值（字符数）
        word_boundary_chars = {' ', '，', '。', '！', '？', '；', '：', '\n', '\t'}  # 词语边界字符
        
        async def flush_buffer():
            """刷新缓冲区，发送累积的内容"""
            nonlocal content_buffer
            if content_buffer:
                yield StreamMessageChunk(
                    conversation_id=conversation.conversation_id,
                    message_id=assistant_message_id,
                    content=content_buffer,
                    is_complete=False,
                    timestamp=datetime.now(),
                    sender="assistant"
                )
                content_buffer = ""

        async def add_to_buffer(text: str):
            """添加文本到缓冲区，智能分块"""
            nonlocal content_buffer
            content_buffer += text

            # 检查是否应该刷新缓冲区
            should_flush = False

            # 条件1: 缓冲区达到大小阈值
            if len(content_buffer) >= buffer_size_threshold:
                should_flush = True

            # 条件2: 遇到词语边界字符
            if text and text[-1] in word_boundary_chars:
                should_flush = True

            # 条件3: 遇到完整的句子结束
            if any(char in text for char in {'。', '！', '？', '\n'}):
                should_flush = True

            if should_flush:
                async for chunk in flush_buffer():
                    yield chunk

        try:
            # 获取流式响应（使用带记忆的助手）
            stream = assistant.run_stream(task=user_task)

            # 处理流式响应
            async for event in stream:
                try:
                    # 通用过滤：跳过任何包含用户消息内容的事件
                    if hasattr(event, 'content') and isinstance(event.content, str):
                        if event.content.strip() == request.message.strip():
                            continue
                    
                    # 检查是否为最终结果
                    if isinstance(event, TaskResult):
                        # 刷新剩余缓冲区内容
                        async for chunk in flush_buffer():
                            yield chunk

                        # 计算响应时间
                        response_time = int((time.time() - start_time) * 1000)

                        # 保存完整的助手回复
                        assistant_message = await self.save_message(
                            conversation_id=conversation.conversation_id,
                            user_id=user_id,
                            content=response_content,
                            sender="assistant",
                            response_time=response_time,
                            tokens_used=total_tokens_used
                        )

                        # 添加助手回复到记忆服务
                        await memory_adapter.add_conversation_message(
                            role="assistant",
                            content=response_content,
                            metadata={
                                "message_id": assistant_message.message_id,
                                "response_time": response_time,
                                "tokens_used": total_tokens_used
                            }
                        )

                        # 更新会话历史
                        self.conversation_history[conversation.conversation_id].append({
                            "role": "assistant",
                            "content": response_content
                        })

                        # 发送完成标志
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=assistant_message_id,
                            content="",
                            is_complete=True,
                            timestamp=datetime.now(),
                            sender="assistant"
                        )

                    elif isinstance(event, ModelClientStreamingChunkEvent):
                        # 流式输出文本块 - 这是主要的流式内容
                        chunk_content = event.content
                        if chunk_content:  # 只处理非空内容
                            response_content += chunk_content
                            # 使用智能缓冲区处理
                            async for buffered_chunk in add_to_buffer(chunk_content):
                                yield buffered_chunk

                    elif isinstance(event, TextMessage):
                        # 完整文本消息 - 通常在工具调用后出现
                        # 严格过滤：只处理来自助手的消息，避免用户消息回显
                        if hasattr(event, 'source') and event.source == 'user':
                            # 跳过用户消息，避免回显
                            continue
                            
                        msg_content = event.content
                        if msg_content:
                            # 检查内容是否与用户输入相同，如果相同则跳过
                            if msg_content.strip() == request.message.strip():
                                continue
                                
                            # 如果已经有流式内容，不再发送完整消息，避免重复
                            if not response_content:
                                response_content = msg_content
                                # 使用智能缓冲区处理完整消息
                                async for buffered_chunk in add_to_buffer(msg_content):
                                    yield buffered_chunk

                        # 处理token使用统计
                        if hasattr(event, 'models_usage') and event.models_usage:
                            if hasattr(event.models_usage, 'prompt_tokens'):
                                total_tokens_used += event.models_usage.prompt_tokens + (event.models_usage.completion_tokens or 0)
                    
                    elif isinstance(event, ToolCallRequestEvent):
                        # 工具调用请求 - 只发送一次状态提示
                        if not tool_call_status_sent:
                            tool_calls = event.content
                            tool_names = []
                            for call in tool_calls:
                                if hasattr(call, 'name'):
                                    tool_names.append(call.name)

                            if tool_names:
                                tool_call_msg = f"🔍 正在查询相关信息（{', '.join(tool_names)}）..."
                            else:
                                tool_call_msg = "🔍 正在查询相关信息..."

                            # 工具调用状态作为独立的chunk发送
                            yield StreamMessageChunk(
                                conversation_id=conversation.conversation_id,
                                message_id=assistant_message_id,
                                content=tool_call_msg,
                                is_complete=False,
                                timestamp=datetime.now(),
                                sender="assistant"
                            )
                            tool_call_status_sent = True

                    elif isinstance(event, ToolCallExecutionEvent):
                        # 工具调用结果 - 不再发送执行结果概要，避免重复内容
                        # 让AI在最终回复中整合所有信息
                        pass

                    elif isinstance(event, ToolCallSummaryMessage):
                        # 工具调用摘要 - 通常包含工具调用的汇总信息
                        # 这里不再单独发送摘要，让AI在最终回复中整合信息
                        pass
                        
                except asyncio.TimeoutError:
                    raise Exception("单步处理超时。")
                except Exception as e:
                    raise Exception(f"处理事件时出错: {str(e)}")
                    
        except Exception as e:
            # 刷新任何剩余的缓冲区内容
            try:
                async for chunk in flush_buffer():
                    yield chunk
            except:
                pass

            # 错误处理
            error_message = f"😔 抱歉，我遇到了一些技术问题，请稍后重试或联系人工客服。\n\n错误详情：{str(e)}"

            await self.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                content=error_message,
                sender="assistant",
                response_time=int((time.time() - start_time) * 1000)
            )

            yield StreamMessageChunk(
                conversation_id=conversation.conversation_id,
                message_id=f"error_{int(time.time())}",
                content=error_message,
                is_complete=True,
                timestamp=datetime.now(),
                sender="assistant"
            )

    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        """删除对话"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        # 删除对话相关的所有消息
        await ChatMessage.filter(conversation_id=conversation_id).delete()

        # 删除对话
        await conversation.delete()
        
        # 删除内存中的会话历史
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]

        # 清理记忆适配器
        if conversation_id in self.memory_adapters:
            await self.memory_adapters[conversation_id].close()
            del self.memory_adapters[conversation_id]

        return True

    async def update_conversation_title(
            self,
            conversation_id: str,
            user_id: int,
            title: str
    ) -> bool:
        """更新对话标题"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        conversation.title = title
        await conversation.save()

        return True


# 全局聊天控制器实例
chat_controller = ChatController()
