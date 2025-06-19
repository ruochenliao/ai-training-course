"""
文档相关数据模式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator


class DocumentBase(BaseModel):
    """文档基础模式"""
    name: str
    description: Optional[str] = None
    file_type: str
    language: str = "zh"


class DocumentCreate(DocumentBase):
    """文档创建模式"""
    knowledge_base_id: int
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('文档名称不能为空')
        return v.strip()


class DocumentUpdate(BaseModel):
    """文档更新模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None


class DocumentResponse(BaseModel):
    """文档响应模式"""
    id: int
    name: str
    original_name: str
    description: Optional[str] = None
    file_path: str
    file_size: int
    file_type: str
    file_hash: str
    processing_status: str
    processing_error: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    content_type: Optional[str] = None
    language: str
    encoding: str
    chunk_count: int
    chunk_strategy: str
    uploaded_by: int
    upload_ip: Optional[str] = None
    knowledge_base_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应模式"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


class DocumentChunkResponse(BaseModel):
    """文档分块响应模式"""
    id: int
    document_id: int
    chunk_index: int
    content: str
    content_hash: str
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    page_number: Optional[int] = None
    char_count: int
    word_count: int
    token_count: Optional[int] = None
    vector_id: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    entities: List[Dict] = []
    relations: List[Dict] = []
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProcessingResult(BaseModel):
    """处理结果模式"""
    success: bool
    content: str
    metadata: Dict[str, Any] = {}
    chunks: int
    tables: List[Dict] = []
    images: List[Dict] = []
    error: Optional[str] = None


class DocumentMetadata(BaseModel):
    """文档元数据模式"""
    pages: Optional[int] = None
    paragraphs: Optional[int] = None
    tables: Optional[int] = None
    images: Optional[int] = None
    file_info: Dict[str, Any] = {}
    processing_method: str
    extraction_time: Optional[datetime] = None


class DocumentUploadRequest(BaseModel):
    """文档上传请求模式"""
    knowledge_base_id: int
    description: Optional[str] = None
    language: str = "zh"
    chunk_strategy: str = "semantic"
    
    @validator('knowledge_base_id')
    def knowledge_base_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('知识库ID必须为正数')
        return v


class DocumentUploadResponse(BaseModel):
    """文档上传响应模式"""
    document_id: int
    file_id: str
    original_name: str
    file_size: int
    upload_url: Optional[str] = None
    processing_status: str = "pending"
    message: str = "文档上传成功，正在处理中"


class DocumentSearchRequest(BaseModel):
    """文档搜索请求模式"""
    query: str
    knowledge_base_ids: Optional[List[int]] = None
    file_types: Optional[List[str]] = None
    processing_status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    size: int = 20
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('搜索查询不能为空')
        return v.strip()
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('页码必须为正数')
        return v
    
    @validator('size')
    def size_must_be_valid(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('每页数量必须在1-100之间')
        return v


class DocumentSearchResponse(BaseModel):
    """文档搜索响应模式"""
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int
    query: str
    search_time: float


class ChunkSearchRequest(BaseModel):
    """分块搜索请求模式"""
    query: str
    document_ids: Optional[List[int]] = None
    knowledge_base_ids: Optional[List[int]] = None
    min_score: float = 0.0
    max_score: float = 1.0
    page: int = 1
    size: int = 20
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('搜索查询不能为空')
        return v.strip()


class ChunkSearchResponse(BaseModel):
    """分块搜索响应模式"""
    chunks: List[DocumentChunkResponse]
    total: int
    page: int
    size: int
    pages: int
    query: str
    search_time: float


class DocumentStats(BaseModel):
    """文档统计模式"""
    total_documents: int
    processing_documents: int
    completed_documents: int
    failed_documents: int
    total_chunks: int
    total_size: int
    file_type_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    upload_trend: List[Dict[str, Any]]


class BatchProcessRequest(BaseModel):
    """批量处理请求模式"""
    document_ids: List[int]
    operation: str  # reprocess, delete, update_status
    parameters: Dict[str, Any] = {}
    
    @validator('document_ids')
    def document_ids_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('文档ID列表不能为空')
        return v
    
    @validator('operation')
    def operation_must_be_valid(cls, v):
        valid_operations = ['reprocess', 'delete', 'update_status', 'extract_entities']
        if v not in valid_operations:
            raise ValueError(f'操作必须是以下之一: {", ".join(valid_operations)}')
        return v


class BatchProcessResponse(BaseModel):
    """批量处理响应模式"""
    total_documents: int
    successful_documents: int
    failed_documents: int
    results: List[Dict[str, Any]]
    operation: str
    started_at: datetime
    completed_at: Optional[datetime] = None
