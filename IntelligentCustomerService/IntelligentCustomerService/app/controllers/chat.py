"""
聊天控制器
基于autogen 0.6.1和Deepseek模型实现智能客服功能
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


class ChatController:
    """聊天控制器"""

    def __init__(self):
        # 初始化Deepseek助手
        self.assistant = deepseek_config.get_assistant()
        # 对话历史缓存: {conversation_id: message_list}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        # 设置模型请求超时时间（秒）
        self.model_timeout = 120

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
        """发送消息并返回流式响应（使用Deepseek模型）"""
        start_time = time.time()

        # 获取或创建对话
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = await self.create_conversation(user_id)
        
        # 准备对话历史
        await self._prepare_conversation_history(conversation.conversation_id, user_id)

        # 保存用户消息
        user_message = await self.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            content=request.message,
            sender="user"
        )

        # 更新对话历史
        if conversation.conversation_id not in self.conversation_history:
            self.conversation_history[conversation.conversation_id] = []
        self.conversation_history[conversation.conversation_id].append({
            "role": "user",
            "content": request.message
        })

        # 发送用户消息的回声响应
        yield StreamMessageChunk(
            conversation_id=conversation.conversation_id,
            message_id=user_message.message_id,
            content=request.message,
            is_complete=False,
            timestamp=datetime.now()
        )

        # 创建用户消息对象
        user_task = TextMessage(source="user", content=request.message)
        
        # 生成消息ID
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        response_content = ""
        total_tokens_used = 0
        
        try:
            # 获取流式响应
            stream = self.assistant.run_stream(task=user_task)
            
            # 处理流式响应
            async for event in stream:
                try:
                    # 检查是否为最终结果
                    if isinstance(event, TaskResult):
                        # 计算响应时间
                        response_time = int((time.time() - start_time) * 1000)
                        
                        # 保存完整的助手回复
                        await self.save_message(
                            conversation_id=conversation.conversation_id,
                            user_id=user_id,
                            content=response_content,
                            sender="assistant",
                            response_time=response_time,
                            tokens_used=total_tokens_used
                        )
                        
                        # 更新会话历史
                        self.conversation_history[conversation.conversation_id].append({
                            "role": "assistant",
                            "content": response_content
                        })
                        
                        # 发送完成标志
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content="",
                            is_complete=True,
                            timestamp=datetime.now()
                        )
                    
                    elif isinstance(event, ModelClientStreamingChunkEvent):
                        # 流式输出文本块
                        chunk_content = event.content
                        response_content += chunk_content
                        
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content=chunk_content,
                            is_complete=False,
                            timestamp=datetime.now()
                        )
                    
                    elif isinstance(event, TextMessage):
                        # 完整文本消息
                        msg_content = event.content
                        response_content = msg_content  # 覆盖之前累积的内容
                        
                        if event.models_usage and hasattr(event.models_usage, 'prompt_tokens'):
                            total_tokens_used += event.models_usage.prompt_tokens + (event.models_usage.completion_tokens or 0)
                        
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content=msg_content,
                            is_complete=False,
                            timestamp=datetime.now()
                        )
                    
                    elif isinstance(event, ToolCallRequestEvent):
                        # 工具调用请求
                        tool_calls = event.content
                        tool_call_msg = "正在查询相关信息..."
                        
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content=tool_call_msg,
                            is_complete=False,
                            timestamp=datetime.now()
                        )
                    
                    elif isinstance(event, ToolCallExecutionEvent):
                        # 工具调用结果
                        execution_results = event.content
                        result_msg = "获取到信息，正在为您整理回复..."
                        
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content=result_msg,
                            is_complete=False,
                            timestamp=datetime.now()
                        )
                    
                    elif isinstance(event, ToolCallSummaryMessage):
                        # 工具调用摘要
                        summary_content = event.content
                        
                        yield StreamMessageChunk(
                            conversation_id=conversation.conversation_id,
                            message_id=message_id,
                            content=f"找到相关信息：{summary_content}",
                            is_complete=False,
                            timestamp=datetime.now()
                        )
                        
                except asyncio.TimeoutError:
                    raise Exception("单步处理超时。")
                except Exception as e:
                    raise Exception(f"处理事件时出错: {str(e)}")
                    
        except Exception as e:
            # 错误处理
            error_message = f"抱歉，我遇到了一些技术问题，请稍后重试或联系人工客服。错误详情：{str(e)}"

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
                timestamp=datetime.now()
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
