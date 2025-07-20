from fastapi import APIRouter

from .llm_models import router as llm_models_router

system_router = APIRouter()
system_router.include_router(llm_models_router, prefix="/llm", tags=["LLM模型管理"])

__all__ = ["system_router"]
