"""
系统API端点
"""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/info", summary="获取系统信息")
async def get_system_info() -> Any:
    """
    获取系统信息
    """
    return {
        "name": "企业级Agent+RAG知识库系统",
        "version": "1.0.0",
        "description": "基于多智能体协作的企业级知识库系统"
    }


@router.get("/health", summary="健康检查")
async def health_check() -> Any:
    """
    健康检查
    """
    return {"status": "healthy"}
