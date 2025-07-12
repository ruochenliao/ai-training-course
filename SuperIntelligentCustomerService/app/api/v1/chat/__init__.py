from fastapi import APIRouter

from .chat_service_api import router as chat_service_router

chat_router = APIRouter()
chat_router.include_router(chat_service_router, tags=["智能聊天服务"])

__all__ = ["chat_router"]
