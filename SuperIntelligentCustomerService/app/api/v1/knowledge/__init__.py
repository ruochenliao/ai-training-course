"""
知识库管理API模块
"""
from fastapi import APIRouter

from .batch import router as batch_router
from .knowledge_base import router as kb_router
from .knowledge_file import router as kf_router
from .monitor import router as monitor_router
from .search import router as search_router
from .statistics import router as statistics_router
from .validation import router as validation_router

knowledge_router = APIRouter()
knowledge_router.include_router(kb_router, prefix="/bases", tags=["知识库管理"])
knowledge_router.include_router(kf_router, prefix="/files", tags=["知识文件管理"])
knowledge_router.include_router(search_router, prefix="", tags=["知识库搜索"])
knowledge_router.include_router(monitor_router, prefix="/monitor", tags=["文件处理监控"])
knowledge_router.include_router(batch_router, prefix="/batch", tags=["批量操作"])
knowledge_router.include_router(validation_router, prefix="/validation", tags=["文件验证"])
knowledge_router.include_router(statistics_router, prefix="/statistics", tags=["统计分析"])

__all__ = ["knowledge_router"]
