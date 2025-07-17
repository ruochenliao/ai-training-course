from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class KnowledgeTypeEnum(str, Enum):
    """Knowledge type enum"""
    CUSTOMER_SERVICE = "customer_service"  # 智能客服知识库
    TEXT_SQL = "text_sql"  # TextSQL知识库
    RAG = "rag"  # RAG知识库
    CONTENT_CREATION = "content_creation"  # 文案创作知识库


class BaseKnowledgeBase(BaseModel):
    """Base knowledge base schema"""
    name: str = Field(..., description="知识库名称", example="技术文档")
    description: str = Field("", description="知识库描述", example="技术文档知识库")
    is_public: bool = Field(False, description="是否为公共知识库")
    knowledge_type: KnowledgeTypeEnum = Field(
        KnowledgeTypeEnum.CUSTOMER_SERVICE,
        description="知识库类型"
    )


class KnowledgeBaseCreate(BaseKnowledgeBase):
    """Knowledge base creation schema"""
    pass


class KnowledgeBaseUpdate(BaseKnowledgeBase):
    """Knowledge base update schema"""
    id: int = Field(..., description="知识库ID")


class KnowledgeBaseResponse(BaseKnowledgeBase):
    """Knowledge base response schema"""
    id: int
    owner_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    files_count: Optional[int] = 0
    knowledge_type: KnowledgeTypeEnum


class EmbeddingStatusEnum(str, Enum):
    """Embedding status enum"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class BaseKnowledgeFile(BaseModel):
    """Base knowledge file schema"""
    name: str = Field(..., description="文件名称", example="技术文档.pdf")
    file_size: int = Field(..., description="文件大小(字节)")
    file_type: str = Field(..., description="文件类型", example="application/pdf")
    embedding_status: Optional[EmbeddingStatusEnum] = Field(EmbeddingStatusEnum.PENDING, description="嵌入状态")
    embedding_error: Optional[str] = Field(None, description="嵌入错误信息")


class KnowledgeFileCreate(BaseKnowledgeFile):
    """Knowledge file creation schema"""
    file_path: str = Field(..., description="文件路径")
    knowledge_base_id: int = Field(..., description="知识库ID")


class KnowledgeFileUpdate(BaseModel):
    """Knowledge file update schema"""
    id: int = Field(..., description="文件ID")
    name: str = Field(..., description="文件名称")


class KnowledgeFileResponse(BaseKnowledgeFile):
    """Knowledge file response schema"""
    id: int
    file_path: str
    knowledge_base_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    download_url: Optional[str] = None
