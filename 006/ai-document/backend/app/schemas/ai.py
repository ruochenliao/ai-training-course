from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AIRequest(BaseModel):
    ai_type: str  # "ai_writer", "ai_polish", "deepseek", etc.
    prompt: str
    document_id: Optional[int] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    session_id: str
    status: str
    response: Optional[str] = None
    error: Optional[str] = None


class AISession(BaseModel):
    id: int
    session_id: str
    user_id: int
    document_id: Optional[int] = None
    ai_type: str
    prompt: str
    response: Optional[str] = None
    status: str
    session_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AIStreamResponse(BaseModel):
    session_id: str
    content: str
    is_complete: bool = False
    error: Optional[str] = None
