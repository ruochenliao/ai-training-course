"""
文档管理API端点
"""

import os
import tempfile
from typing import Any, Optional

from app.core.security import get_current_user
from app.models.knowledge import Document, DocumentChunk, KnowledgeBase
from app.models.user import User
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentUploadResponse,
    DocumentSearchRequest, DocumentSearchResponse, DocumentStats,
    BatchProcessRequest, BatchProcessResponse
)
from app.services.document_processor import document_processor
from app.services.file_storage import file_storage
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/", response_model=DocumentListResponse, summary="获取文档列表")
async def get_documents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    processing_status: Optional[str] = Query(None, description="处理状态"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取文档列表
    """
    # 构建查询
    query = Document.filter(is_deleted=False)

    # 权限过滤
    if not current_user.is_superuser:
        # 获取用户可访问的知识库
        accessible_kbs = await KnowledgeBase.filter(
            owner_id=current_user.id,
            is_deleted=False
        ).union(
            KnowledgeBase.filter(
                visibility="public",
                is_deleted=False
            )
        )
        accessible_kb_ids = [kb.id for kb in accessible_kbs]
        query = query.filter(knowledge_base_id__in=accessible_kb_ids)

    # 应用过滤条件
    if knowledge_base_id:
        query = query.filter(knowledge_base_id=knowledge_base_id)

    if processing_status:
        query = query.filter(processing_status=processing_status)

    if file_type:
        query = query.filter(file_type=file_type)

    if search:
        query = query.filter(name__icontains=search)

    # 计算总数
    total = await query.count()

    # 分页查询
    offset = (page - 1) * size
    documents = await query.offset(offset).limit(size).order_by("-created_at")

    # 转换为响应格式
    doc_list = []
    for doc in documents:
        doc_dict = await doc.to_dict()
        doc_list.append(doc_dict)

    return {
        "documents": doc_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.post("/upload", response_model=DocumentUploadResponse, summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: int = Form(...),
    description: Optional[str] = Form(None),
    language: str = Form("zh"),
    chunk_strategy: str = Form("semantic"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    上传文档
    """
    # 检查知识库权限
    knowledge_base = await KnowledgeBase.get_or_none(
        id=knowledge_base_id,
        is_deleted=False
    )
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )

    # 检查权限
    if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此知识库"
        )

    # 检查文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.docx', '.pptx', '.txt', '.md', '.html', '.csv', '.xlsx', '.json']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}"
        )

    # 检查文件大小
    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过100MB"
        )

    try:
        # 上传文件到存储
        file_info = await file_storage.upload_file(
            file_data=file.file,
            file_name=file.filename,
            folder="documents",
            metadata={
                "knowledge_base_id": str(knowledge_base_id),
                "uploaded_by": str(current_user.id),
                "description": description or ""
            }
        )

        # 创建文档记录
        document = await Document.create(
            knowledge_base_id=knowledge_base_id,
            name=file.filename,
            original_name=file.filename,
            file_path=file_info["object_name"],
            file_size=file_info["file_size"],
            file_type=file_ext,
            file_hash=file_info["etag"],
            content_type=file_info["content_type"],
            language=language,
            chunk_strategy=chunk_strategy,
            uploaded_by=current_user.id,
            processing_status="pending"
        )

        # 异步处理文档（这里应该使用Celery任务队列）
        # 暂时直接调用处理器
        try:
            # 下载文件到临时目录
            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                temp_path = temp_file.name
                await file_storage.download_file_to_path(
                    file_info["object_name"],
                    temp_path
                )

            # 处理文档
            await document_processor.process_document(
                temp_path,
                document.id,
                knowledge_base_id
            )

            # 清理临时文件
            os.unlink(temp_path)

        except Exception as e:
            # 处理失败，更新状态
            await document.fail_processing(str(e))

        return {
            "document_id": document.id,
            "file_id": file_info["file_id"],
            "original_name": file.filename,
            "file_size": file_info["file_size"],
            "processing_status": "processing",
            "message": "文档上传成功，正在处理中"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取文档详情
    """
    document = await Document.get_or_none(id=document_id, is_deleted=False)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 检查权限
    knowledge_base = await KnowledgeBase.get(id=document.knowledge_base_id)
    if not current_user.is_superuser:
        if knowledge_base.owner_id != current_user.id and knowledge_base.visibility != "public":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文档"
            )

    return await document.to_dict()


@router.delete("/{document_id}", summary="删除文档")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除文档
    """
    document = await Document.get_or_none(id=document_id, is_deleted=False)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 检查权限
    knowledge_base = await KnowledgeBase.get(id=document.knowledge_base_id)
    if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此文档"
        )

    # 软删除文档
    await document.soft_delete()

    # 删除文档分块
    await DocumentChunk.filter(document_id=document_id).delete()

    # 删除存储文件
    try:
        await file_storage.delete_file(document.file_path)
    except Exception as e:
        logger.warning(f"删除存储文件失败: {e}")

    return {"message": "文档删除成功"}


@router.get("/{document_id}/chunks", summary="获取文档分块")
async def get_document_chunks(
    document_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取文档分块
    """
    document = await Document.get_or_none(id=document_id, is_deleted=False)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 检查权限
    knowledge_base = await KnowledgeBase.get(id=document.knowledge_base_id)
    if not current_user.is_superuser:
        if knowledge_base.owner_id != current_user.id and knowledge_base.visibility != "public":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文档"
            )

    # 分页查询分块
    total = await DocumentChunk.filter(document_id=document_id).count()
    offset = (page - 1) * size
    chunks = await DocumentChunk.filter(document_id=document_id).offset(offset).limit(size).order_by("chunk_index")

    # 转换为响应格式
    chunk_list = []
    for chunk in chunks:
        chunk_dict = await chunk.to_dict()
        chunk_list.append(chunk_dict)

    return {
        "chunks": chunk_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{document_id}/download", summary="下载文档")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    下载文档
    """
    document = await Document.get_or_none(id=document_id, is_deleted=False)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 检查权限
    knowledge_base = await KnowledgeBase.get(id=document.knowledge_base_id)
    if not current_user.is_superuser:
        if knowledge_base.owner_id != current_user.id and knowledge_base.visibility != "public":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权下载此文档"
            )

    try:
        # 获取文件数据
        file_data = await file_storage.download_file(document.file_path)

        # 返回文件流
        def generate():
            yield file_data

        return StreamingResponse(
            generate(),
            media_type=document.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={document.original_name}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档下载失败: {str(e)}"
        )
