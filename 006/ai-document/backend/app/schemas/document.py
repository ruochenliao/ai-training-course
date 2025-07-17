from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = ""
    summary: Optional[str] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    is_public: Optional[bool] = None


class Document(DocumentBase):
    id: int
    word_count: int
    user_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    word_count: int
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
