"""
知识库管理API模块
"""
from fastapi import APIRouter

from .knowledge_base import router as kb_router

knowledge_router = APIRouter()
knowledge_router.include_router(kb_router, tags=["知识库管理"])

__all__ = ["knowledge_router"]
