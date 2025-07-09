"""
知识库管理API路由
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field

from ....core.dependency import DependAuth
from ....models.admin import User
from ....controllers.knowledge_base import KnowledgeBaseController

router = APIRouter()


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求模型"""
    name: str = Field(..., description="知识库名称", max_length=200)
    description: str = Field("", description="知识库描述")
    knowledge_type: str = Field(..., description="知识库类型")
    is_public: bool = Field(False, description="是否公开")
    max_file_size: Optional[int] = Field(None, description="最大文件大小(字节)")
    allowed_file_types: Optional[list[str]] = Field(None, description="允许的文件类型")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    chunk_size: Optional[int] = Field(None, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, description="分块重叠")


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求模型"""
    name: Optional[str] = Field(None, description="知识库名称", max_length=200)
    description: Optional[str] = Field(None, description="知识库描述")
    knowledge_type: Optional[str] = Field(None, description="知识库类型")
    is_public: Optional[bool] = Field(None, description="是否公开")
    max_file_size: Optional[int] = Field(None, description="最大文件大小(字节)")
    allowed_file_types: Optional[list[str]] = Field(None, description="允许的文件类型")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    chunk_size: Optional[int] = Field(None, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, description="分块重叠")


@router.post("/", summary="创建知识库")
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: User = DependAuth
):
    """创建新的知识库"""
    return await KnowledgeBaseController.create_knowledge_base(
        name=request.name,
        description=request.description,
        knowledge_type=request.knowledge_type,
        is_public=request.is_public,
        owner_id=current_user.id,
        max_file_size=request.max_file_size,
        allowed_file_types=request.allowed_file_types,
        embedding_model=request.embedding_model,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap
    )


@router.get("/", summary="获取知识库列表")
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    knowledge_type: Optional[str] = Query(None, description="知识库类型过滤"),
    is_public: Optional[bool] = Query(None, description="公开状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = DependAuth
):
    """获取知识库列表"""
    return await KnowledgeBaseController.list_knowledge_bases(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        is_public=is_public,
        search=search
    )


@router.get("/types", summary="获取知识库类型")
async def get_knowledge_types():
    """获取所有可用的知识库类型"""
    return await KnowledgeBaseController.get_knowledge_types()


@router.get("/statistics", summary="获取用户统计信息")
async def get_user_statistics(current_user: User = DependAuth):
    """获取当前用户的知识库统计信息"""
    return await KnowledgeBaseController.get_user_statistics(current_user.id)


@router.get("/{kb_id}", summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: int,
    current_user: User = DependAuth
):
    """获取指定知识库的详细信息"""
    return await KnowledgeBaseController.get_knowledge_base(kb_id, current_user.id)


@router.put("/{kb_id}", summary="更新知识库")
async def update_knowledge_base(
    kb_id: int,
    request: UpdateKnowledgeBaseRequest,
    current_user: User = DependAuth
):
    """更新知识库信息"""
    # 过滤None值
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    return await KnowledgeBaseController.update_knowledge_base(
        kb_id=kb_id,
        user_id=current_user.id,
        **update_data
    )


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = DependAuth
):
    """删除知识库（软删除）"""
    return await KnowledgeBaseController.delete_knowledge_base(kb_id, current_user.id)
