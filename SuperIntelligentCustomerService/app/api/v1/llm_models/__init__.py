from fastapi import APIRouter

from .llm_models import router

llm_models_router = APIRouter()
llm_models_router.include_router(router, tags=["LLM模型管理"])

__all__ = ["llm_models_router"]
