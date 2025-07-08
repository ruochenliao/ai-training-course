from fastapi import APIRouter

from .auth import router

auth_router = APIRouter()
auth_router.include_router(router, tags=["认证管理"])

__all__ = ["auth_router"]
