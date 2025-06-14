"""
聊天控制器
基于autogen 0.6.1和Deepseek模型实现智能客服功能
"""
import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Optional, AsyncGenerator, Tuple
from fastapi import HTTPException

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat

from app.core.crud import CRUDBase
from app.core.llm_config import get_deepseek_client, get_system_prompt
from app.models.admin import ChatConversation, ChatMessage
from app.schemas.chat import (
    ChatConversationCreate,
    ChatMessageCreate,
    SendMessageRequest,
    ChatMessageResponse,
    ChatConversationResponse,
    StreamMessageChunk
)


class ChatController:
    """聊天控制器"""
    
    def __init__(self):
        self.model_client = get_deepseek_client()
        self.system_prompt = get_system_prompt()
    
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
        return await ChatMessage.filter(
            conversation_id=conversation_id,
            user_id=user_id
        ).order_by('created_at').limit(limit)
    
    async def send_message_stream(
        self,
        request: SendMessageRequest,
        user_id: int
    ) -> AsyncGenerator[StreamMessageChunk, None]:
        """发送消息并返回流式响应（暂时使用模拟实现）"""
        start_time = time.time()

        # 获取或创建对话
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = await self.create_conversation(user_id)

        # 保存用户消息
        user_message = await self.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            content=request.message,
            sender="user"
        )

        try:
            # 生成消息ID
            message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # 模拟智能回复（后续替换为真实的LLM调用）
            response_text = await self._generate_mock_response(request.message)

            # 模拟流式输出
            words = response_text.split()
            for i, word in enumerate(words):
                content = word + " " if i < len(words) - 1 else word

                yield StreamMessageChunk(
                    conversation_id=conversation.conversation_id,
                    message_id=message_id,
                    content=content,
                    is_complete=False,
                    timestamp=datetime.now()
                )

                # 模拟延迟
                await asyncio.sleep(0.1)

            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)

            # 保存助手回复
            await self.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                content=response_text,
                sender="assistant",
                response_time=response_time
            )

            # 发送完成标志
            yield StreamMessageChunk(
                conversation_id=conversation.conversation_id,
                message_id=message_id,
                content="",
                is_complete=True,
                timestamp=datetime.now()
            )

        except Exception as e:
            # 错误处理
            error_message = f"抱歉，我遇到了一些技术问题，请稍后重试或联系人工客服。"

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
    
    async def _generate_mock_response(self, message: str) -> str:
        """生成模拟回复（后续替换为真实的LLM调用）"""
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ['价格', '费用', '多少钱', '收费']):
            return "关于价格信息，我们有多种套餐可供选择。基础版每月99元，专业版每月299元，企业版每月599元。每个版本都有不同的功能特性，您可以根据需求选择合适的套餐。"
        elif any(keyword in message_lower for keyword in ['功能', '特性', '能做什么', '介绍']):
            return "我们的智能客服系统具有以下主要功能：1. 24小时在线客服支持 2. 智能问答和知识库检索 3. 多渠道接入支持 4. 客户数据分析 5. 工单管理系统 6. 自定义机器人配置。"
        elif any(keyword in message_lower for keyword in ['技术支持', '技术问题', 'bug', '故障']):
            return "我已经为您转接到技术支持团队。我们的技术专家会在30分钟内与您联系，请保持电话畅通。同时，您也可以通过邮箱 tech-support@company.com 联系我们。"
        elif any(keyword in message_lower for keyword in ['退款', '取消', '不满意', '申请退款']):
            return "我理解您的担忧。我们提供7天无理由退款服务。如需申请退款，请提供您的订单号，我会立即为您处理。我们也很希望了解您不满意的原因，以便我们改进服务。"
        elif any(keyword in message_lower for keyword in ['联系', '电话', '地址', '客服']):
            return "您可以通过以下方式联系我们：\n客服热线：400-123-4567（工作日9:00-18:00）\n邮箱：service@company.com\n地址：北京市朝阳区科技园区123号\n微信客服：扫描官网二维码添加"
        elif any(keyword in message_lower for keyword in ['你好', 'hello', 'hi', '您好']):
            return "您好！欢迎使用我们的智能客服系统。我是您的专属客服助手，很高兴为您服务。请问有什么可以帮助您的吗？"
        elif any(keyword in message_lower for keyword in ['谢谢', '感谢', 'thank']):
            return "不客气！能够帮助到您是我的荣幸。如果您还有其他问题，请随时告诉我。祝您使用愉快！"
        else:
            return f"感谢您的咨询：「{message}」。我正在为您查找相关信息，请稍候。如果您有紧急问题，请联系我们的人工客服：400-123-4567。"

    async def send_message(
        self,
        request: SendMessageRequest,
        user_id: int
    ) -> dict:
        """发送消息（非流式）"""
        start_time = time.time()

        # 获取或创建对话
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = await self.create_conversation(user_id)

        # 保存用户消息
        user_message = await self.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            content=request.message,
            sender="user"
        )

        try:
            # 生成回复（使用模拟回复，后续替换为真实的LLM调用）
            assistant_content = await self._generate_mock_response(request.message)

            # 计算响应时间
            response_time = int((time.time() - start_time) * 1000)

            # 保存助手回复
            assistant_message = await self.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                content=assistant_content,
                sender="assistant",
                response_time=response_time
            )

            return {
                "conversation_id": conversation.conversation_id,
                "user_message": {
                    "id": user_message.message_id,
                    "content": user_message.content,
                    "sender": user_message.sender,
                    "timestamp": user_message.created_at.isoformat()
                },
                "assistant_message": {
                    "id": assistant_message.message_id,
                    "content": assistant_message.content,
                    "sender": assistant_message.sender,
                    "timestamp": assistant_message.created_at.isoformat(),
                    "response_time": response_time
                }
            }

        except Exception as e:
            # 错误处理
            error_message = f"抱歉，我遇到了一些技术问题，请稍后重试或联系人工客服。"

            assistant_message = await self.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                content=error_message,
                sender="assistant",
                response_time=int((time.time() - start_time) * 1000)
            )

            return {
                "conversation_id": conversation.conversation_id,
                "user_message": {
                    "id": user_message.message_id,
                    "content": user_message.content,
                    "sender": user_message.sender,
                    "timestamp": user_message.created_at.isoformat()
                },
                "assistant_message": {
                    "id": assistant_message.message_id,
                    "content": error_message,
                    "sender": assistant_message.sender,
                    "timestamp": assistant_message.created_at.isoformat()
                }
            }
    
    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        """删除对话"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        # 删除对话相关的所有消息
        await ChatMessage.filter(conversation_id=conversation_id).delete()
        
        # 删除对话
        await conversation.delete()
        
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
