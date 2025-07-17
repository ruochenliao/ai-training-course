from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate
import re


def count_words(text: str) -> int:
    """统计文字数量（中英文）"""
    if not text:
        return 0
    
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
    # 统计英文单词
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', clean_text))
    
    return chinese_chars + english_words


def create_document(db: Session, document: DocumentCreate, user_id: int) -> Document:
    """创建文档"""
    word_count = count_words(document.content or "")
    
    db_document = Document(
        title=document.title,
        content=document.content,
        summary=document.summary,
        word_count=word_count,
        user_id=user_id,
        is_public=document.is_public
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_document(db: Session, document_id: int, user_id: int) -> Optional[Document]:
    """获取文档"""
    return db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id,
        Document.is_deleted == False
    ).first()


def get_documents(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
    """获取用户文档列表"""
    return db.query(Document).filter(
        Document.user_id == user_id,
        Document.is_deleted == False
    ).order_by(desc(Document.updated_at)).offset(skip).limit(limit).all()


def update_document(db: Session, document_id: int, user_id: int, document_update: DocumentUpdate) -> Optional[Document]:
    """更新文档"""
    db_document = get_document(db, document_id, user_id)
    if not db_document:
        return None
    
    update_data = document_update.dict(exclude_unset=True)
    
    # 如果更新了内容，重新计算字数
    if "content" in update_data:
        update_data["word_count"] = count_words(update_data["content"])
    
    for field, value in update_data.items():
        setattr(db_document, field, value)
    
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int, user_id: int) -> bool:
    """删除文档（软删除）"""
    db_document = get_document(db, document_id, user_id)
    if not db_document:
        return False
    
    db_document.is_deleted = True
    db.commit()
    return True


def search_documents(db: Session, user_id: int, query: str, skip: int = 0, limit: int = 100) -> List[Document]:
    """搜索文档"""
    return db.query(Document).filter(
        Document.user_id == user_id,
        Document.is_deleted == False,
        Document.title.contains(query) | Document.content.contains(query)
    ).order_by(desc(Document.updated_at)).offset(skip).limit(limit).all()
