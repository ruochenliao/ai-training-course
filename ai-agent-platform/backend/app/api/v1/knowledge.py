"""
知识库管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.knowledge import KnowledgeBase, Document, DocumentChunk
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    DocumentResponse,
    DocumentChunkResponse,
    SearchRequest,
    SearchResponse
)

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建知识库
    """
    knowledge_base = KnowledgeBase(
        name=kb_data.name,
        description=kb_data.description,
        owner_id=current_user.id,
        is_public=kb_data.is_public or False,
        settings=kb_data.settings or {}
    )
    
    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    
    return knowledge_base


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取知识库列表
    """
    query = db.query(KnowledgeBase).filter(
        (KnowledgeBase.owner_id == current_user.id) | (KnowledgeBase.is_public == True)
    )
    
    if search:
        query = query.filter(
            (KnowledgeBase.name.contains(search)) |
            (KnowledgeBase.description.contains(search))
        )
    
    if is_public is not None:
        query = query.filter(KnowledgeBase.is_public == is_public)
    
    knowledge_bases = query.order_by(
        KnowledgeBase.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return knowledge_bases


@router.get("/my", response_model=List[KnowledgeBaseResponse])
async def get_my_knowledge_bases(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取我的知识库列表
    """
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.owner_id == current_user.id
    ).order_by(KnowledgeBase.updated_at.desc()).offset(skip).limit(limit).all()
    
    return knowledge_bases


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定知识库详情
    """
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查权限
    if not knowledge_base.is_public and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return knowledge_base


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_update: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新知识库
    """
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.owner_id == current_user.id
    ).first()
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或权限不足"
        )
    
    # 更新知识库信息
    update_data = kb_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(knowledge_base, field, value)
    
    knowledge_base.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(knowledge_base)
    
    return knowledge_base


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除知识库
    """
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.owner_id == current_user.id
    ).first()
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或权限不足"
        )
    
    db.delete(knowledge_base)
    db.commit()
    
    return {"message": "知识库删除成功"}


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def get_documents(
    kb_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取知识库文档列表
    """
    # 验证知识库权限
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    if not knowledge_base.is_public and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    documents = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return documents


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传文档到知识库
    """
    # 验证知识库权限
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.owner_id == current_user.id
    ).first()
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或权限不足"
        )
    
    # 验证文件类型
    allowed_types = [
        "text/plain",  # txt
        "text/markdown",  # md
        "application/pdf",  # pdf
        "application/msword",  # doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.ms-powerpoint",  # ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
        "application/vnd.ms-excel",  # xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # xlsx
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型"
        )
    
    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > 500 * 1024 * 1024:  # 500MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过 500MB"
        )

    # 创建文档记录
    document = Document(
        title=file.filename,
        file_name=file.filename,
        file_type=file.content_type,
        file_size=len(content),
        knowledge_base_id=kb_id,
        status="processing"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # TODO: 这里应该启动异步任务处理文档
    # 目前先简单处理为文本
    if file.content_type == "text/plain":
        document.content = content.decode('utf-8')
        document.status = "completed"
        db.commit()
    
    return {
        "message": "文档上传成功",
        "document_id": document.id,
        "status": document.status
    }


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除文档
    """
    # 验证知识库权限
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.owner_id == current_user.id
    ).first()
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在或权限不足"
        )
    
    # 查找文档
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.knowledge_base_id == kb_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    db.delete(document)
    db.commit()
    
    return {"message": "文档删除成功"}


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    kb_id: int,
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    在知识库中搜索
    """
    # 验证知识库权限
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    if not knowledge_base.is_public and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # TODO: 实现向量搜索
    # 目前先实现简单的文本搜索
    query = db.query(DocumentChunk).join(Document).filter(
        Document.knowledge_base_id == kb_id,
        DocumentChunk.content.contains(search_request.query)
    ).limit(search_request.top_k or 5)
    
    chunks = query.all()
    
    results = []
    for chunk in chunks:
        results.append({
            "content": chunk.content,
            "score": 0.8,  # 模拟相似度分数
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "metadata": chunk.metadata or {}
        })
    
    return {
        "query": search_request.query,
        "results": results,
        "total": len(results)
    }
