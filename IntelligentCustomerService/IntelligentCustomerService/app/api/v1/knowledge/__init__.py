from fastapi import APIRouter

from .knowledge import router

knowledge_router = APIRouter()
knowledge_router.include_router(router, tags=["知识库管理"])

__all__ = ["knowledge_router"]
