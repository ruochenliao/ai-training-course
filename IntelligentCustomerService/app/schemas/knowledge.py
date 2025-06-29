"""
知识库相关的数据模型
"""
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class KnowledgeAddRequest(BaseModel):
    """添加知识请求模型"""
    content: str = Field(..., description="知识内容", min_length=1, max_length=10000)
    user_id: Optional[str] = Field(None, description="用户ID（个人知识库必需）")
    category: Optional[str] = Field("general", description="知识分类")
    title: Optional[str] = Field(None, description="知识标题")
    tags: Optional[List[str]] = Field([], description="标签列表")
    priority: Optional[int] = Field(1, description="优先级（1-5）", ge=1, le=5)
    source: Optional[str] = Field("manual", description="知识来源")
    author: Optional[str] = Field(None, description="作者")
    metadata: Optional[Dict[str, Any]] = Field({}, description="额外元数据")


class KnowledgeUpdateRequest(BaseModel):
    """更新知识请求模型"""
    content: Optional[str] = Field(None, description="知识内容", max_length=10000)
    category: Optional[str] = Field(None, description="知识分类")
    title: Optional[str] = Field(None, description="知识标题")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    priority: Optional[int] = Field(None, description="优先级（1-5）", ge=1, le=5)
    is_active: Optional[bool] = Field(None, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class KnowledgeSearchRequest(BaseModel):
    """搜索知识请求模型"""
    query: str = Field(..., description="搜索查询", min_length=1, max_length=500)
    user_id: Optional[str] = Field(None, description="用户ID")
    search_public: bool = Field(True, description="是否搜索公共知识库")
    search_private: bool = Field(False, description="是否搜索个人知识库")
    category: Optional[str] = Field(None, description="限制搜索分类")
    limit: Optional[int] = Field(10, description="返回结果数量", ge=1, le=50)
    min_score: Optional[float] = Field(0.0, description="最小相关性分数", ge=0.0, le=1.0)


class KnowledgeItem(BaseModel):
    """知识项模型"""
    id: str = Field(..., description="知识ID")
    content: str = Field(..., description="知识内容")
    source: str = Field(..., description="来源（public/private）")
    category: str = Field(..., description="分类")
    title: str = Field(..., description="标题")
    tags: List[str] = Field(..., description="标签列表")
    priority: int = Field(..., description="优先级")
    relevance_score: float = Field(..., description="相关性分数")
    similarity_score: float = Field(..., description="相似度分数")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class KnowledgeResponse(BaseModel):
    """知识响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="响应数据")


class KnowledgeListResponse(BaseModel):
    """知识列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="响应数据")


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="统计数据")


class KnowledgeBatchAddRequest(BaseModel):
    """批量添加知识请求模型"""
    knowledge_items: List[KnowledgeAddRequest] = Field(..., description="知识项列表", min_items=1, max_items=100)
    user_id: Optional[str] = Field(None, description="用户ID（个人知识库必需）")
    is_public: bool = Field(True, description="是否添加到公共知识库")


class KnowledgeImportRequest(BaseModel):
    """知识导入请求模型"""
    file_content: str = Field(..., description="文件内容")
    file_type: str = Field(..., description="文件类型（json/csv/txt）")
    user_id: Optional[str] = Field(None, description="用户ID")
    is_public: bool = Field(True, description="是否导入到公共知识库")
    default_category: str = Field("imported", description="默认分类")
    default_tags: List[str] = Field([], description="默认标签")


class KnowledgeExportRequest(BaseModel):
    """知识导出请求模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    export_public: bool = Field(True, description="是否导出公共知识库")
    export_private: bool = Field(False, description="是否导出个人知识库")
    categories: Optional[List[str]] = Field(None, description="导出的分类列表")
    format: str = Field("json", description="导出格式（json/csv）")


class ModelDownloadRequest(BaseModel):
    """模型下载请求模型"""
    model_type: str = Field(..., description="模型类型（embedding/reranker）")
    force_download: bool = Field(False, description="是否强制重新下载")


class ModelStatusResponse(BaseModel):
    """模型状态响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="模型状态数据")


class KnowledgeAnalyticsRequest(BaseModel):
    """知识库分析请求模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    analyze_public: bool = Field(True, description="是否分析公共知识库")
    analyze_private: bool = Field(False, description="是否分析个人知识库")
    time_range: str = Field("30d", description="时间范围（7d/30d/90d/1y）")


class KnowledgeRecommendationRequest(BaseModel):
    """知识推荐请求模型"""
    user_id: str = Field(..., description="用户ID")
    context: Optional[str] = Field(None, description="上下文信息")
    limit: int = Field(5, description="推荐数量", ge=1, le=20)
    categories: Optional[List[str]] = Field(None, description="限制推荐分类")


class KnowledgeSimilarityRequest(BaseModel):
    """知识相似性请求模型"""
    knowledge_id: str = Field(..., description="知识ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    limit: int = Field(5, description="相似知识数量", ge=1, le=20)
    threshold: float = Field(0.5, description="相似度阈值", ge=0.0, le=1.0)
