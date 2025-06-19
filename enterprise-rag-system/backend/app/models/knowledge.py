"""
知识库相关数据模型
"""

from datetime import datetime
from typing import List, Optional

from tortoise import fields

from .base import (
    BaseModel, 
    TimestampMixin, 
    StatusMixin, 
    SoftDeleteMixin, 
    OwnershipMixin,
    VisibilityMixin,
    MetadataMixin
)


class KnowledgeBase(BaseModel, TimestampMixin, StatusMixin, SoftDeleteMixin, OwnershipMixin, VisibilityMixin, MetadataMixin):
    """知识库模型"""
    
    class KnowledgeType:
        """知识库类型"""
        CUSTOMER_SERVICE = "customer_service"
        TEXT_SQL = "text_sql"
        RAG = "rag"
        CONTENT_CREATION = "content_creation"
        GENERAL = "general"
        
        CHOICES = [
            (CUSTOMER_SERVICE, "智能客服"),
            (TEXT_SQL, "Text2SQL"),
            (RAG, "RAG问答"),
            (CONTENT_CREATION, "内容创作"),
            (GENERAL, "通用知识库"),
        ]
    
    # 基本信息
    name = fields.CharField(max_length=100, description="知识库名称", index=True)
    description = fields.TextField(null=True, description="知识库描述")
    
    # 类型和配置
    knowledge_type = fields.CharEnumField(
        KnowledgeType,
        default=KnowledgeType.GENERAL,
        description="知识库类型",
        index=True
    )
    
    # 配置信息
    config = fields.JSONField(default=dict, description="知识库配置")
    
    # 统计信息
    document_count = fields.IntField(default=0, description="文档数量")
    chunk_count = fields.IntField(default=0, description="分块数量")
    total_size = fields.BigIntField(default=0, description="总大小(字节)")
    
    # 索引信息
    vector_collection_name = fields.CharField(max_length=100, null=True, description="向量集合名称")
    graph_namespace = fields.CharField(max_length=100, null=True, description="图谱命名空间")
    
    # 处理状态
    last_indexed_at = fields.DatetimeField(null=True, description="最后索引时间")
    indexing_status = fields.CharField(max_length=20, default="ready", description="索引状态")
    
    class Meta:
        table = "knowledge_bases"
        indexes = [
            ["owner_id", "knowledge_type"],
            ["visibility", "status"],
            ["name"],
            ["created_at"],
        ]
    
    async def get_documents(self, status: str = None) -> List["Document"]:
        """获取文档列表"""
        query = Document.filter(knowledge_base_id=self.id)
        if status:
            query = query.filter(processing_status=status)
        return await query.all()
    
    async def get_document_count(self, status: str = None) -> int:
        """获取文档数量"""
        query = Document.filter(knowledge_base_id=self.id)
        if status:
            query = query.filter(processing_status=status)
        return await query.count()
    
    async def update_statistics(self):
        """更新统计信息"""
        documents = await self.get_documents()
        
        self.document_count = len(documents)
        self.chunk_count = sum(doc.chunk_count for doc in documents)
        self.total_size = sum(doc.file_size for doc in documents)
        
        await self.save(update_fields=["document_count", "chunk_count", "total_size"])
    
    def get_config(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value):
        """设置配置值"""
        if not isinstance(self.config, dict):
            self.config = {}
        self.config[key] = value
    
    def is_indexing(self) -> bool:
        """是否正在索引"""
        return self.indexing_status == "indexing"
    
    def is_ready(self) -> bool:
        """是否就绪"""
        return self.indexing_status == "ready"


class Document(BaseModel, TimestampMixin, StatusMixin, SoftDeleteMixin, MetadataMixin):
    """文档模型"""
    
    class ProcessingStatus:
        """处理状态"""
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
        
        CHOICES = [
            (PENDING, "待处理"),
            (PROCESSING, "处理中"),
            (COMPLETED, "已完成"),
            (FAILED, "失败"),
            (CANCELLED, "已取消"),
        ]
    
    # 关联关系
    knowledge_base = fields.ForeignKeyField(
        "models.KnowledgeBase", 
        related_name="documents", 
        on_delete=fields.CASCADE,
        description="所属知识库"
    )
    
    # 文件信息
    name = fields.CharField(max_length=255, description="文件名称", index=True)
    original_name = fields.CharField(max_length=255, description="原始文件名")
    file_path = fields.CharField(max_length=500, description="文件路径")
    file_size = fields.BigIntField(description="文件大小(字节)")
    file_type = fields.CharField(max_length=50, description="文件类型", index=True)
    file_hash = fields.CharField(max_length=64, description="文件哈希", index=True)
    
    # 处理信息
    processing_status = fields.CharEnumField(
        ProcessingStatus,
        default=ProcessingStatus.PENDING,
        description="处理状态",
        index=True
    )
    processing_error = fields.TextField(null=True, description="处理错误信息")
    processing_started_at = fields.DatetimeField(null=True, description="处理开始时间")
    processing_completed_at = fields.DatetimeField(null=True, description="处理完成时间")
    
    # 内容信息
    content_type = fields.CharField(max_length=100, null=True, description="内容类型")
    language = fields.CharField(max_length=10, default="zh", description="语言")
    encoding = fields.CharField(max_length=20, default="utf-8", description="编码")
    
    # 分块信息
    chunk_count = fields.IntField(default=0, description="分块数量")
    chunk_strategy = fields.CharField(max_length=20, default="semantic", description="分块策略")
    
    # 提取信息
    extracted_text = fields.TextField(null=True, description="提取的文本")
    extracted_tables = fields.JSONField(default=list, description="提取的表格")
    extracted_images = fields.JSONField(default=list, description="提取的图片")
    
    # 上传信息
    uploaded_by = fields.IntField(description="上传者ID", index=True)
    upload_ip = fields.CharField(max_length=45, null=True, description="上传IP")
    
    class Meta:
        table = "documents"
        indexes = [
            ["knowledge_base_id", "processing_status"],
            ["file_hash"],
            ["uploaded_by"],
            ["created_at"],
            ["name"],
        ]
    
    async def get_chunks(self) -> List["DocumentChunk"]:
        """获取文档分块"""
        return await DocumentChunk.filter(document_id=self.id).order_by("chunk_index")
    
    async def get_uploader(self):
        """获取上传者"""
        from .user import User
        return await User.get_or_none(id=self.uploaded_by)
    
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self.processing_status == self.ProcessingStatus.PROCESSING
    
    def is_completed(self) -> bool:
        """是否处理完成"""
        return self.processing_status == self.ProcessingStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """是否处理失败"""
        return self.processing_status == self.ProcessingStatus.FAILED
    
    async def start_processing(self):
        """开始处理"""
        self.processing_status = self.ProcessingStatus.PROCESSING
        self.processing_started_at = datetime.now()
        self.processing_error = None
        await self.save(update_fields=["processing_status", "processing_started_at", "processing_error"])
    
    async def complete_processing(self, chunk_count: int = 0):
        """完成处理"""
        self.processing_status = self.ProcessingStatus.COMPLETED
        self.processing_completed_at = datetime.now()
        self.chunk_count = chunk_count
        await self.save(update_fields=["processing_status", "processing_completed_at", "chunk_count"])
    
    async def fail_processing(self, error_message: str):
        """处理失败"""
        self.processing_status = self.ProcessingStatus.FAILED
        self.processing_completed_at = datetime.now()
        self.processing_error = error_message
        await self.save(update_fields=["processing_status", "processing_completed_at", "processing_error"])


class DocumentChunk(BaseModel, TimestampMixin, MetadataMixin):
    """文档分块模型"""
    
    # 关联关系
    document = fields.ForeignKeyField(
        "models.Document", 
        related_name="chunks", 
        on_delete=fields.CASCADE,
        description="所属文档"
    )
    
    # 分块信息
    chunk_index = fields.IntField(description="分块索引", index=True)
    content = fields.TextField(description="分块内容")
    content_hash = fields.CharField(max_length=64, description="内容哈希", index=True)
    
    # 位置信息
    start_position = fields.IntField(null=True, description="开始位置")
    end_position = fields.IntField(null=True, description="结束位置")
    page_number = fields.IntField(null=True, description="页码")
    
    # 内容统计
    char_count = fields.IntField(description="字符数")
    word_count = fields.IntField(description="词数")
    token_count = fields.IntField(null=True, description="Token数")
    
    # 向量信息
    vector_id = fields.CharField(max_length=100, null=True, description="向量ID", index=True)
    embedding_model = fields.CharField(max_length=50, null=True, description="嵌入模型")
    embedding_dimension = fields.IntField(null=True, description="嵌入维度")
    
    # 图谱信息
    entities = fields.JSONField(default=list, description="实体列表")
    relations = fields.JSONField(default=list, description="关系列表")
    
    # 质量评分
    quality_score = fields.FloatField(null=True, description="质量评分")
    relevance_score = fields.FloatField(null=True, description="相关性评分")
    
    class Meta:
        table = "document_chunks"
        indexes = [
            ["document_id", "chunk_index"],
            ["content_hash"],
            ["vector_id"],
            ["quality_score"],
        ]
        unique_together = [["document", "chunk_index"]]
    
    async def get_knowledge_base(self):
        """获取所属知识库"""
        document = await self.document
        return await document.knowledge_base
    
    def get_preview(self, max_length: int = 100) -> str:
        """获取内容预览"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def has_vector(self) -> bool:
        """是否有向量"""
        return self.vector_id is not None
    
    def has_entities(self) -> bool:
        """是否有实体"""
        return bool(self.entities)
    
    def has_relations(self) -> bool:
        """是否有关系"""
        return bool(self.relations)
