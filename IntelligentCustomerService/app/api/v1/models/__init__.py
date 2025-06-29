from fastapi import APIRouter

from .models import router

models_router = APIRouter()
models_router.include_router(router, tags=["模型管理"])

__all__ = ["models_router"]
