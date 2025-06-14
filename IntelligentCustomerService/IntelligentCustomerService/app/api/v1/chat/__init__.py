# 聊天模块初始化文件
from fastapi import APIRouter

from .chat import router

chats_router = APIRouter()
chats_router.include_router(router, tags=["智能客服模块"])

__all__ = ["chats_router"]
