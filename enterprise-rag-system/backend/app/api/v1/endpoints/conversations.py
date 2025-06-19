"""
对话管理API端点
"""

from typing import Any
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", summary="获取对话列表")
async def get_conversations(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取对话列表
    """
    return {"message": "对话列表功能待实现"}


@router.post("/", summary="创建对话")
async def create_conversation(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建对话
    """
    return {"message": "创建对话功能待实现"}
