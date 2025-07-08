from fastapi import APIRouter

from .email import router as email_router

resource_router = APIRouter()
resource_router.include_router(email_router, prefix="/email", tags=["资源管理"])

__all__ = ["resource_router"]
