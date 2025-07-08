from fastapi import APIRouter

from .chat import router

chat_router = APIRouter()
chat_router.include_router(router, tags=["聊天功能"])

__all__ = ["chat_router"]
