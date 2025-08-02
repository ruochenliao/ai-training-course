"""
知识库相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class KnowledgeBaseBase(BaseModel):
    """知识库基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库描述")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """创建知识库的请求模型"""
    is_public: Optional[bool] = Field(default=False, description="是否公开")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="知识库设置")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=1000, description="知识库描述")
    is_public: Optional[bool] = Field(None, description="是否公开")
    settings: Optional[Dict[str, Any]] = Field(None, description="知识库设置")


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """知识库响应模型"""
    id: int
    owner_id: str
    is_public: bool
    settings: Optional[Dict[str, Any]]
    document_count: str
    total_size: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="文档标题")


class DocumentCreate(DocumentBase):
    """创建文档的请求模型"""
    content: Optional[str] = Field(None, description="文档内容")
    file_url: Optional[str] = Field(None, description="文件URL")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="文档元数据")


class DocumentUpdate(BaseModel):
    """更新文档的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: int
    file_name: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    file_url: Optional[str]
    content: Optional[str]
    knowledge_base_id: int
    status: str
    chunk_count: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkBase(BaseModel):
    """文档块基础模型"""
    content: str = Field(..., min_length=1, description="文档块内容")


class DocumentChunkCreate(DocumentChunkBase):
    """创建文档块的请求模型"""
    chunk_index: int = Field(..., ge=0, description="块索引")
    start_char: Optional[int] = Field(None, ge=0, description="起始字符位置")
    end_char: Optional[int] = Field(None, ge=0, description="结束字符位置")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="块元数据")


class DocumentChunkResponse(DocumentChunkBase):
    """文档块响应模型"""
    id: int
    document_id: int
    chunk_index: int
    start_char: Optional[int]
    end_char: Optional[int]
    vector_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="返回结果数量")
    score_threshold: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤条件")


class SearchResult(BaseModel):
    """搜索结果项"""
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相似度分数")
    document_id: int = Field(..., description="文档ID")
    chunk_id: int = Field(..., description="文档块ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str = Field(..., description="搜索查询")
    results: List[SearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., description="结果总数")


class KnowledgeBaseStats(BaseModel):
    """知识库统计信息"""
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    total_size: int
    public_knowledge_bases: int


class ProcessingTask(BaseModel):
    """处理任务模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: float = Field(..., ge=0.0, le=100.0, description="处理进度")
    message: Optional[str] = Field(None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    created_at: datetime
    updated_at: datetime


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    file_urls: List[str] = Field(..., min_items=1, max_items=10, description="文件URL列表")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="处理选项")


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    task_id: str = Field(..., description="批量处理任务ID")
    total_files: int = Field(..., description="文件总数")
    message: str = Field(..., description="响应消息")


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query_vector: List[float] = Field(..., description="查询向量")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤条件")


class VectorSearchResponse(BaseModel):
    """向量搜索响应"""
    results: List[SearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., description="结果总数")


class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="文本列表")
    model: Optional[str] = Field(default="text-embedding-ada-002", description="嵌入模型")


class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    embeddings: List[List[float]] = Field(..., description="嵌入向量列表")
    model: str = Field(..., description="使用的模型")
    usage: Dict[str, int] = Field(..., description="使用统计")
