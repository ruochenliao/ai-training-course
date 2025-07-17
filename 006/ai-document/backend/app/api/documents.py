from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.document import Document, DocumentCreate, DocumentUpdate, DocumentList
from app.schemas.user import User
from app.services.document import (
    create_document,
    get_document,
    get_documents,
    update_document,
    delete_document,
    search_documents
)
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/", response_model=Document)
def create_new_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新文档"""
    return create_document(db=db, document=document, user_id=current_user.id)


@router.get("/", response_model=List[DocumentList])
def read_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取文档列表"""
    if search:
        documents = search_documents(
            db=db, user_id=current_user.id, query=search, skip=skip, limit=limit
        )
    else:
        documents = get_documents(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
    return documents


@router.get("/{document_id}", response_model=Document)
def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个文档"""
    document = get_document(db=db, document_id=document_id, user_id=current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=Document)
def update_existing_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新文档"""
    document = update_document(
        db=db, document_id=document_id, user_id=current_user.id, document_update=document_update
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}")
def delete_existing_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除文档"""
    success = delete_document(db=db, document_id=document_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
