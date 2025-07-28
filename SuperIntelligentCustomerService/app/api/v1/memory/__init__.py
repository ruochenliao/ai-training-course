from fastapi import APIRouter

from .memory import router

memory_router = APIRouter()
memory_router.include_router(router, tags=["mcp模块"])

__all__ = ["memory_router"]
