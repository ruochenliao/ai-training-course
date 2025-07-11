from fastapi import APIRouter

from .messages import router as messages_router
from .models import router as models_router
from .sessions import router as sessions_router

system_router = APIRouter()
system_router.include_router(models_router, prefix="/model", tags=["模型管理"])
system_router.include_router(sessions_router, prefix="/session", tags=["会话管理"])
system_router.include_router(messages_router, prefix="/message", tags=["消息管理"])

__all__ = ["system_router"]
