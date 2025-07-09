"""
知识文件管理API路由
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends, UploadFile, File, HTTPException

from ....core.dependency import DependAuth
from ....models.admin import User
from ....controllers.knowledge_file import KnowledgeFileController

router = APIRouter()


@router.post("/{kb_id}/upload", summary="上传文件")
async def upload_file(
    kb_id: int,
    file: UploadFile = File(..., description="要上传的文件"),
    current_user: User = DependAuth
):
    """上传文件到指定知识库"""
    return await KnowledgeFileController.upload_file(
        kb_id=kb_id,
        file=file,
        user_id=current_user.id
    )


@router.get("/{kb_id}", summary="获取知识库文件列表")
async def list_files(
    kb_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    status: Optional[str] = Query(None, description="处理状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = DependAuth
):
    """获取指定知识库的文件列表"""
    return await KnowledgeFileController.list_files(
        kb_id=kb_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        file_type=file_type,
        status=status,
        search=search
    )


@router.get("/{kb_id}/statistics", summary="获取文件处理统计")
async def get_processing_statistics(
    kb_id: int,
    current_user: User = DependAuth
):
    """获取指定知识库的文件处理统计信息"""
    return await KnowledgeFileController.get_processing_statistics(kb_id, current_user.id)


@router.get("/types", summary="获取支持的文件类型")
async def get_file_types():
    """获取所有支持的文件类型"""
    return await KnowledgeFileController.get_file_types()


@router.get("/detail/{file_id}", summary="获取文件详情")
async def get_file(
    file_id: int,
    current_user: User = DependAuth
):
    """获取指定文件的详细信息"""
    return await KnowledgeFileController.get_file(file_id, current_user.id)


@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    current_user: User = DependAuth
):
    """删除指定文件"""
    return await KnowledgeFileController.delete_file(file_id, current_user.id)


@router.post("/{file_id}/retry", summary="重试文件处理")
async def retry_processing(
    file_id: int,
    current_user: User = DependAuth
):
    """重试处理失败的文件"""
    return await KnowledgeFileController.retry_processing(file_id, current_user.id)
