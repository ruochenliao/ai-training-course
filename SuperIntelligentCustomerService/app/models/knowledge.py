"""
知识库管理数据模型
基于Tortoise ORM的知识库和知识文件模型定义
"""
from tortoise import fields
from tortoise.models import Model

from .base import BaseModel, TimestampMixin
from .enums import KnowledgeType, EmbeddingStatus, FileType


class KnowledgeBase(BaseModel, TimestampMixin):
    """
    知识库模型
    管理不同类型的知识库，支持公共和私有访问控制
    """
    
    # 基本信息
    name = fields.CharField(max_length=200, description="知识库名称")
    description = fields.TextField(null=True, description="知识库描述")
    
    # 访问控制
    is_public = fields.BooleanField(default=False, description="是否公开访问")
    owner_id = fields.BigIntField(description="所有者用户ID")
    
    # 知识库类型
    knowledge_type = fields.CharEnumField(
        KnowledgeType, 
        default=KnowledgeType.GENERAL,
        description="知识库类型"
    )
    
    # 统计信息
    file_count = fields.IntField(default=0, description="文件数量")
    total_size = fields.BigIntField(default=0, description="总文件大小(字节)")
    
    # 配置信息
    max_file_size = fields.BigIntField(default=52428800, description="最大文件大小(字节)，默认50MB")
    allowed_file_types = fields.JSONField(
        default=lambda: [ft.value for ft in FileType],
        description="允许的文件类型"
    )
    
    # 嵌入配置
    embedding_model = fields.CharField(
        max_length=100, 
        default="BAAI/bge-small-zh-v1.5",
        description="嵌入模型"
    )
    chunk_size = fields.IntField(default=1024, description="文本分块大小")
    chunk_overlap = fields.IntField(default=100, description="分块重叠大小")
    
    # 状态信息
    is_active = fields.BooleanField(default=True, description="是否激活")
    last_updated_by = fields.BigIntField(null=True, description="最后更新者ID")
    
    # 关联关系
    files: fields.ReverseRelation["KnowledgeFile"]
    
    class Meta:
        table = "knowledge_bases"
        indexes = [
            ["name"],
            ["is_public"],
            ["owner_id"],
            ["knowledge_type"],
            ["is_active"],
            ["created_at"],
        ]
    
    def __str__(self):
        return f"KnowledgeBase(id={self.id}, name={self.name}, type={self.knowledge_type})"
    
    async def update_statistics(self):
        """更新统计信息"""
        files = await self.files.all()
        self.file_count = len(files)
        self.total_size = sum(file.file_size for file in files if file.file_size)
        await self.save(update_fields=["file_count", "total_size", "updated_at"])
    
    async def can_access(self, user_id: int) -> bool:
        """检查用户是否可以访问此知识库"""
        return self.is_public or self.owner_id == user_id
    
    async def can_modify(self, user_id: int) -> bool:
        """检查用户是否可以修改此知识库"""
        return self.owner_id == user_id
    
    def get_allowed_extensions(self) -> list[str]:
        """获取允许的文件扩展名列表"""
        return [f".{file_type}" for file_type in self.allowed_file_types]


class KnowledgeFile(BaseModel, TimestampMixin):
    """
    知识文件模型
    存储上传到知识库的文件信息和处理状态
    """
    
    # 基本信息
    name = fields.CharField(max_length=255, description="文件名")
    original_name = fields.CharField(max_length=255, description="原始文件名")
    file_path = fields.CharField(max_length=500, description="文件存储路径")
    
    # 文件属性
    file_size = fields.BigIntField(description="文件大小(字节)")
    file_type = fields.CharEnumField(FileType, description="文件类型")
    mime_type = fields.CharField(max_length=100, null=True, description="MIME类型")
    
    # 文件哈希（用于去重）
    file_hash = fields.CharField(max_length=64, null=True, description="文件SHA256哈希")
    
    # 处理状态
    embedding_status = fields.CharEnumField(
        EmbeddingStatus,
        default=EmbeddingStatus.PENDING,
        description="嵌入处理状态"
    )
    
    # 处理信息
    processed_at = fields.DatetimeField(null=True, description="处理完成时间")
    error_message = fields.TextField(null=True, description="错误信息")
    retry_count = fields.IntField(default=0, description="重试次数")
    
    # 内容信息
    content_preview = fields.TextField(null=True, description="内容预览")
    page_count = fields.IntField(null=True, description="页数（PDF等）")
    word_count = fields.IntField(null=True, description="字数")
    
    # 嵌入信息
    chunk_count = fields.IntField(default=0, description="分块数量")
    embedding_model = fields.CharField(max_length=100, null=True, description="使用的嵌入模型")
    
    # 元数据
    metadata = fields.JSONField(default=dict, description="文件元数据")
    
    # 上传信息
    uploaded_by = fields.BigIntField(description="上传者用户ID")
    
    # 外键关系
    knowledge_base: fields.ForeignKeyRelation[KnowledgeBase] = fields.ForeignKeyField(
        "models.KnowledgeBase",
        related_name="files",
        on_delete=fields.CASCADE,
        description="所属知识库"
    )
    
    class Meta:
        table = "knowledge_files"
        indexes = [
            ["name"],
            ["file_type"],
            ["embedding_status"],
            ["knowledge_base_id"],
            ["uploaded_by"],
            ["created_at"],
            ["file_hash"],
        ]
        unique_together = [
            ["knowledge_base_id", "file_hash"]  # 同一知识库内文件哈希唯一
        ]
    
    def __str__(self):
        return f"KnowledgeFile(id={self.id}, name={self.name}, status={self.embedding_status})"
    
    @property
    def file_extension(self) -> str:
        """获取文件扩展名"""
        return f".{self.file_type}"
    
    @property
    def is_image(self) -> bool:
        """判断是否为图片文件"""
        image_types = [FileType.JPG, FileType.JPEG, FileType.PNG, FileType.GIF, FileType.WEBP]
        return self.file_type in image_types
    
    @property
    def is_document(self) -> bool:
        """判断是否为文档文件"""
        doc_types = [FileType.PDF, FileType.DOCX, FileType.DOC, FileType.TXT, FileType.MD, FileType.HTML]
        return self.file_type in doc_types
    
    def get_display_size(self) -> str:
        """获取人类可读的文件大小"""
        if self.file_size is None:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    async def can_access(self, user_id: int) -> bool:
        """检查用户是否可以访问此文件"""
        kb = await self.knowledge_base
        return await kb.can_access(user_id)
    
    async def can_modify(self, user_id: int) -> bool:
        """检查用户是否可以修改此文件"""
        kb = await self.knowledge_base
        return await kb.can_modify(user_id)
    
    async def mark_processing(self):
        """标记为处理中"""
        self.embedding_status = EmbeddingStatus.PROCESSING
        await self.save(update_fields=["embedding_status", "updated_at"])
    
    async def mark_completed(self, chunk_count: int = 0, embedding_model: str = None):
        """标记为处理完成"""
        from datetime import datetime
        
        self.embedding_status = EmbeddingStatus.COMPLETED
        self.processed_at = datetime.now()
        self.chunk_count = chunk_count
        if embedding_model:
            self.embedding_model = embedding_model
        self.error_message = None
        
        await self.save(update_fields=[
            "embedding_status", "processed_at", "chunk_count", 
            "embedding_model", "error_message", "updated_at"
        ])
    
    async def mark_failed(self, error_message: str):
        """标记为处理失败"""
        self.embedding_status = EmbeddingStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        
        await self.save(update_fields=[
            "embedding_status", "error_message", "retry_count", "updated_at"
        ])
