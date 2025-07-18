"""
知识库管理相关的数据模型定义
参考006项目的设计架构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from app.models.enums import KnowledgeType, EmbeddingStatus


class BaseKnowledgeBase(BaseModel):
    """知识库基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    knowledge_type: str = Field(KnowledgeType.CUSTOMER_SERVICE, description="知识库类型")
    is_public: bool = Field(False, description="是否公开")


class KnowledgeBaseCreate(BaseKnowledgeBase):
    """创建知识库请求模型"""
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="知识库配置")
    embedding_model: Optional[str] = Field("BAAI/bge-small-zh-v1.5", description="嵌入模型")
    chunk_size: int = Field(1000, ge=100, le=5000, description="分块大小")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="分块重叠")
    max_file_size: int = Field(52428800, ge=1024, description="最大文件大小(字节)")
    allowed_file_types: List[str] = Field(
        default=["pdf", "docx", "txt", "md"],
        description="允许的文件类型"
    )


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    knowledge_type: Optional[str] = Field(None, description="知识库类型")
    is_public: Optional[bool] = Field(None, description="是否公开")
    config: Optional[Dict[str, Any]] = Field(None, description="知识库配置")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    chunk_size: Optional[int] = Field(None, ge=100, le=5000, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="分块重叠")
    max_file_size: Optional[int] = Field(None, ge=1024, description="最大文件大小(字节)")
    allowed_file_types: Optional[List[str]] = Field(None, description="允许的文件类型")


class KnowledgeBaseResponse(BaseKnowledgeBase):
    """知识库响应模型"""
    id: int = Field(..., description="知识库ID")
    owner_id: int = Field(..., description="所有者ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="知识库配置")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    chunk_size: int = Field(1000, description="分块大小")
    chunk_overlap: int = Field(200, description="分块重叠")
    max_file_size: int = Field(52428800, description="最大文件大小(字节)")
    allowed_file_types: List[str] = Field(default_factory=list, description="允许的文件类型")
    file_count: int = Field(0, description="文件数量")
    total_size: int = Field(0, description="总大小(字节)")
    status: str = Field("active", description="知识库状态")
    last_updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    is_deleted: bool = Field(False, description="是否已删除")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    status_stats: Optional[Dict[str, int]] = Field(None, description="文件状态统计")

    class Config:
        from_attributes = True


class BaseKnowledgeFile(BaseModel):
    """知识文件基础模型"""
    name: str = Field(..., description="文件名称")
    original_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    file_type: str = Field(..., description="文件类型")


class KnowledgeFileCreate(BaseKnowledgeFile):
    """创建知识文件请求模型"""
    file_path: str = Field(..., description="文件路径")
    file_hash: str = Field(..., description="文件哈希值")
    knowledge_base_id: int = Field(..., description="知识库ID")


class KnowledgeFileResponse(BaseKnowledgeFile):
    """知识文件响应模型"""
    id: int = Field(..., description="文件ID")
    file_path: str = Field(..., description="文件路径")
    file_hash: str = Field(..., description="文件哈希值")
    knowledge_base_id: int = Field(..., description="知识库ID")
    embedding_status: str = Field(EmbeddingStatus.PENDING, description="嵌入处理状态")
    embedding_error: Optional[str] = Field(None, description="嵌入错误信息")
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")
    chunk_count: int = Field(0, description="分块数量")
    vector_ids: List[str] = Field(default_factory=list, description="向量ID列表")
    is_deleted: bool = Field(False, description="是否已删除")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class KnowledgeFileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: int = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="上传状态")
    message: str = Field(..., description="响应消息")


class KnowledgeBaseListQuery(BaseModel):
    """知识库列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    knowledge_type: Optional[str] = Field(None, description="知识库类型过滤")
    is_public: Optional[bool] = Field(None, description="公开状态过滤")
    search: Optional[str] = Field(None, description="搜索关键词")


class KnowledgeFileListQuery(BaseModel):
    """知识文件列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    status: Optional[str] = Field(None, description="状态过滤")


class KnowledgeTypeOption(BaseModel):
    """知识库类型选项"""
    value: str = Field(..., description="类型值")
    label: str = Field(..., description="类型标签")


class KnowledgeBaseStats(BaseModel):
    """知识库统计信息"""
    total_knowledge_bases: int = Field(0, description="总知识库数")
    public_knowledge_bases: int = Field(0, description="公开知识库数")
    private_knowledge_bases: int = Field(0, description="私有知识库数")
    total_files: int = Field(0, description="总文件数")
    total_size: int = Field(0, description="总大小")
    processing_files: int = Field(0, description="处理中文件数")
    completed_files: int = Field(0, description="已完成文件数")
    failed_files: int = Field(0, description="失败文件数")


class FileProcessingStatus(BaseModel):
    """文件处理状态"""
    file_id: int = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    status: str = Field(..., description="处理状态")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="处理进度")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    knowledge_base_ids: Optional[List[int]] = Field(None, description="指定知识库ID列表")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量限制")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="相似度阈值")


class KnowledgeSearchResult(BaseModel):
    """知识搜索结果"""
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相似度分数")
    file_id: int = Field(..., description="文件ID")
    file_name: str = Field(..., description="文件名")
    knowledge_base_id: int = Field(..., description="知识库ID")
    knowledge_base_name: str = Field(..., description="知识库名称")
    chunk_index: int = Field(..., description="分块索引")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class KnowledgeSearchResponse(BaseModel):
    """知识搜索响应"""
    query: str = Field(..., description="搜索查询")
    results: List[KnowledgeSearchResult] = Field(default_factory=list, description="搜索结果")
    total: int = Field(0, description="总结果数")
    took: float = Field(0.0, description="搜索耗时(秒)")


class BatchFileUploadRequest(BaseModel):
    """批量文件上传请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    file_names: List[str] = Field(..., description="文件名列表")


class BatchFileUploadResponse(BaseModel):
    """批量文件上传响应"""
    success_count: int = Field(0, description="成功上传数量")
    failed_count: int = Field(0, description="失败上传数量")
    success_files: List[KnowledgeFileUploadResponse] = Field(default_factory=list, description="成功文件列表")
    failed_files: List[Dict[str, str]] = Field(default_factory=list, description="失败文件列表")
