from typing import List, Optional, Tuple

from tortoise.expressions import Q

from ..core.crud import CRUDBase
from ..models.admin import ChatSession
from ..schemas.session import SessionCreate, SessionUpdate


class SessionController(CRUDBase[ChatSession, SessionCreate, SessionUpdate]):
    def __init__(self):
        super().__init__(model=ChatSession)

    async def get_user_sessions(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 10,
        session_title: Optional[str] = None
    ) -> Tuple[int, List[ChatSession]]:
        """获取用户的会话列表"""
        q = Q(user_id=user_id)
        if session_title:
            q &= Q(session_title__contains=session_title)
        
        return await self.list(page=page, page_size=page_size, search=q, order=["-created_at"])

    async def get_user_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        """获取用户的特定会话"""
        return await self.model.filter(id=session_id, user_id=user_id).first()

    async def delete_user_sessions(self, session_ids: List[int], user_id: int) -> int:
        """删除用户的会话"""
        deleted_count = await self.model.filter(id__in=session_ids, user_id=user_id).delete()
        return deleted_count

    async def create_user_session(self, session_data: SessionCreate) -> ChatSession:
        """创建用户会话"""
        return await self.create(obj_in=session_data)

    async def update_user_session(self, session_id: int, user_id: int, session_data: SessionUpdate) -> Optional[ChatSession]:
        """更新用户会话"""
        session = await self.get_user_session(session_id, user_id)
        if not session:
            return None
        
        await self.update(id=session_id, obj_in=session_data)
        return await self.get(id=session_id)


session_controller = SessionController()
