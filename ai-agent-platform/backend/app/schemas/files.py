"""
# Copyright (c) 2025 左岚. All rights reserved.

文件相关的Pydantic模型
"""

# # Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Optional

# # Third-party imports
from pydantic import BaseModel, Field


class FileBase(BaseModel):
    """文件基础模型"""
    original_filename: str = Field(..., description="原始文件名")
    description: Optional[str] = Field(None, max_length=500, description="文件描述")


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: Optional[int] = Field(None, description="文件ID")
    original_filename: str = Field(..., description="原始文件名")
    file_size: Optional[int] = Field(None, description="文件大小")
    content_type: Optional[str] = Field(None, description="文件类型")
    upload_url: Optional[str] = Field(None, description="上传URL")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")


class FileResponse(FileBase):
    """文件响应模型"""
    id: int
    stored_filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileSearchRequest(BaseModel):
    """文件搜索请求"""
    filename: Optional[str] = Field(None, description="文件名搜索")
    content_type: Optional[str] = Field(None, description="文件类型筛选")
    size_min: Optional[int] = Field(None, ge=0, description="最小文件大小")
    size_max: Optional[int] = Field(None, ge=0, description="最大文件大小")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    skip: int = Field(default=0, ge=0, description="跳过数量")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")


class FileSearchResponse(BaseModel):
    """文件搜索响应"""
    files: List[FileResponse]
    total: int
    skip: int
    limit: int


class FileStats(BaseModel):
    """文件统计信息"""
    total_files: int
    total_size: int
    file_types: Dict[str, int]
    upload_trend: List[Dict[str, Any]]


class FileProcessingTask(BaseModel):
    """文件处理任务"""
    task_id: str = Field(..., description="任务ID")
    file_id: int = Field(..., description="文件ID")
    task_type: str = Field(..., description="任务类型")
    status: str = Field(..., description="任务状态")
    progress: float = Field(..., ge=0.0, le=100.0, description="处理进度")
    message: Optional[str] = Field(None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    created_at: datetime
    updated_at: datetime


class FileProcessingRequest(BaseModel):
    """文件处理请求"""
    file_id: int = Field(..., description="文件ID")
    task_type: str = Field(..., description="处理类型")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="处理选项")


class FileProcessingResponse(BaseModel):
    """文件处理响应"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")


class SupportedFileTypes(BaseModel):
    """支持的文件类型"""
    supported_types: Dict[str, List[str]]
    max_file_size: int
    max_file_size_mb: float


class FileMetadata(BaseModel):
    """文件元数据"""
    filename: str
    size: int
    content_type: str
    checksum: Optional[str] = None
    encoding: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    extracted_text: Optional[str] = None
    extracted_images: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class FileAnalysisRequest(BaseModel):
    """文件分析请求"""
    file_id: int = Field(..., description="文件ID")
    analysis_types: List[str] = Field(..., description="分析类型列表")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="分析选项")


class FileAnalysisResponse(BaseModel):
    """文件分析响应"""
    file_id: int
    analysis_results: Dict[str, Any]
    metadata: FileMetadata
    created_at: datetime


class BulkFileOperation(BaseModel):
    """批量文件操作"""
    file_ids: List[int] = Field(..., min_items=1, max_items=100, description="文件ID列表")
    operation: str = Field(..., description="操作类型")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作选项")


class BulkFileOperationResponse(BaseModel):
    """批量文件操作响应"""
    task_id: str = Field(..., description="批量操作任务ID")
    total_files: int = Field(..., description="文件总数")
    message: str = Field(..., description="响应消息")


class FileShareRequest(BaseModel):
    """文件分享请求"""
    file_id: int = Field(..., description="文件ID")
    share_type: str = Field(..., description="分享类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    password: Optional[str] = Field(None, description="访问密码")
    download_limit: Optional[int] = Field(None, ge=1, description="下载次数限制")


class FileShareResponse(BaseModel):
    """文件分享响应"""
    share_id: str = Field(..., description="分享ID")
    share_url: str = Field(..., description="分享链接")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime
