"""
知识库管理API模块
"""
from fastapi import APIRouter

from .knowledge_base import router as kb_router
from .knowledge_file import router as file_router

knowledge_router = APIRouter()
knowledge_router.include_router(kb_router, prefix="/bases", tags=["知识库管理"])
knowledge_router.include_router(file_router, prefix="/files", tags=["知识文件管理"])

__all__ = ["knowledge_router"]
