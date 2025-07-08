from typing import List, Optional, Tuple
from tortoise.expressions import Q
from tortoise.functions import Sum

from app.core.crud import CRUDBase
from app.models.admin import ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageUpdate


class ChatController(CRUDBase[ChatMessage, ChatMessageCreate, ChatMessageUpdate]):
    def __init__(self):
        super().__init__(model=ChatMessage)

    async def get_session_messages(
        self, 
        session_id: int, 
        user_id: int,
        page: int = 1, 
        page_size: int = 50,
        role: Optional[str] = None
    ) -> Tuple[int, List[ChatMessage]]:
        """获取会话的消息列表"""
        q = Q(session_id=session_id, user_id=user_id)
        if role:
            q &= Q(role=role)
        
        return await self.list(page=page, page_size=page_size, search=q, order=["created_at"])

    async def create_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """创建聊天消息"""
        return await self.create(obj_in=message_data)

    async def get_latest_messages(
        self, 
        session_id: int, 
        user_id: int, 
        limit: int = 10
    ) -> List[ChatMessage]:
        """获取会话的最新消息"""
        messages = await self.model.filter(
            session_id=session_id, 
            user_id=user_id
        ).order_by("-created_at").limit(limit)
        return list(reversed(messages))  # 按时间正序返回

    async def delete_session_messages(self, session_id: int, user_id: int) -> int:
        """删除会话的所有消息"""
        deleted_count = await self.model.filter(session_id=session_id, user_id=user_id).delete()
        return deleted_count

    async def get_user_message_stats(self, user_id: int) -> dict:
        """获取用户消息统计"""
        total_messages = await self.model.filter(user_id=user_id).count()
        total_tokens = await self.model.filter(user_id=user_id).aggregate(
            total_tokens_sum=Sum("total_tokens")
        )
        total_cost = await self.model.filter(user_id=user_id).aggregate(
            total_cost_sum=Sum("deduct_cost")
        )
        
        return {
            "total_messages": total_messages,
            "total_tokens": total_tokens.get("total_tokens_sum", 0) or 0,
            "total_cost": float(total_cost.get("total_cost_sum", 0) or 0)
        }


chat_controller = ChatController()
