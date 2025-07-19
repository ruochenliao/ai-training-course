"""
知识库管理API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from app.controllers.knowledge import knowledge_base_controller
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListQuery,
    KnowledgeTypeOption
)
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


@router.post("/", summary="创建知识库", response_model=dict)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    current_user: User = DependAuth
):
    """创建新的知识库"""
    result = await knowledge_base_controller.create_knowledge_base(
        name=request.name,
        description=request.description,
        knowledge_type=request.knowledge_type,
        is_public=request.is_public,
        owner_id=current_user.id,
        config=request.config,
        embedding_model=request.embedding_model,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        max_file_size=request.max_file_size,
        allowed_file_types=request.allowed_file_types
    )

    return result


@router.get("/", summary="获取知识库列表", response_model=dict)
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    knowledge_type: Optional[str] = Query(None, description="知识库类型过滤"),
    is_public: Optional[bool] = Query(None, description="公开状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = DependAuth
):
    """获取知识库列表"""
    result = await knowledge_base_controller.list_knowledge_bases(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        is_public=is_public,
        search=search
    )

    return result


@router.get("/types", summary="获取知识库类型", response_model=dict)
async def get_knowledge_types():
    """获取所有可用的知识库类型"""
    result = await knowledge_base_controller.get_knowledge_types()

    # Success 对象直接返回，不需要检查 success 字段
    return result


@router.get("/{kb_id}", summary="获取知识库详情", response_model=dict)
async def get_knowledge_base(
    kb_id: int,
    current_user: User = DependAuth
):
    """获取知识库详情"""
    result = await knowledge_base_controller.get_knowledge_base(kb_id, current_user.id)

    return result


@router.put("/{kb_id}", summary="更新知识库", response_model=dict)
async def update_knowledge_base(
    kb_id: int,
    request: KnowledgeBaseUpdate,
    current_user: User = DependAuth
):
    """更新知识库信息"""
    # 过滤None值
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    result = await knowledge_base_controller.update_knowledge_base(
        kb_id=kb_id,
        user_id=current_user.id,
        **update_data
    )

    return result


@router.delete("/{kb_id}", summary="删除知识库", response_model=dict)
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = DependAuth
):
    """删除知识库（软删除）"""
    result = await knowledge_base_controller.delete_knowledge_base(kb_id, current_user.id)

    return result


@router.get("/{kb_id}/stats", summary="获取知识库统计信息", response_model=dict)
async def get_knowledge_base_stats(
    kb_id: int,
    current_user: User = DependAuth
):
    """获取知识库统计信息"""
    # 获取知识库详情（包含统计信息）
    result = await knowledge_base_controller.get_knowledge_base(kb_id, current_user.id)

    return result
