"""
记忆服务工厂类
"""
from typing import Dict, Optional

from .chat_memory import ChatMemoryService
from .private_memory import PrivateMemoryService
from .public_memory import PublicMemoryService


class MemoryServiceFactory:
    """记忆服务工厂类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._chat_memory_services: Dict[str, ChatMemoryService] = {}
        self._private_memory_services: Dict[str, PrivateMemoryService] = {}
        self._public_memory_service: Optional[PublicMemoryService] = None
    
    def get_chat_memory_service(self, user_id: str) -> ChatMemoryService:
        """获取聊天记忆服务"""
        if user_id not in self._chat_memory_services:
            self._chat_memory_services[user_id] = ChatMemoryService(
                user_id=user_id,
                db_path=self.db_path
            )
        return self._chat_memory_services[user_id]
    
    def get_private_memory_service(self, user_id: str) -> PrivateMemoryService:
        """获取私有记忆服务"""
        if user_id not in self._private_memory_services:
            self._private_memory_services[user_id] = PrivateMemoryService(user_id=user_id)
        return self._private_memory_services[user_id]

    def get_public_memory_service(self) -> PublicMemoryService:
        """获取公共记忆服务"""
        if self._public_memory_service is None:
            self._public_memory_service = PublicMemoryService()
        return self._public_memory_service
    
    def clear_cache(self):
        """清理缓存的服务实例"""
        self._chat_memory_services.clear()
        self._private_memory_services.clear()
        self._public_memory_service = None
