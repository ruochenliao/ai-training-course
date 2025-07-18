from fastapi import APIRouter

from .models import router as models_router

system_router = APIRouter()
system_router.include_router(models_router, prefix="/model", tags=["模型管理"])

__all__ = ["system_router"]
