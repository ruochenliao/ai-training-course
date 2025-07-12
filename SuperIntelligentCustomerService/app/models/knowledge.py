"""
知识库管理数据模型
基于Tortoise ORM的知识库和知识文件模型定义
"""
from tortoise import fields

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
    
    # 元数据
    last_updated_by = fields.BigIntField(null=True, description="最后更新者ID")
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    
    class Meta:
        table = "knowledge_bases"
        table_description = "知识库表"
    
    async def can_access(self, user_id: int) -> bool:
        """检查用户是否可以访问此知识库"""
        return self.is_public or self.owner_id == user_id
    
    async def can_modify(self, user_id: int) -> bool:
        """检查用户是否可以修改此知识库"""
        return self.owner_id == user_id
    
    async def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "owner_id": self.owner_id,
            "knowledge_type": self.knowledge_type.value if self.knowledge_type else None,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "max_file_size": self.max_file_size,
            "allowed_file_types": self.allowed_file_types,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_updated_by": self.last_updated_by,
            "is_deleted": self.is_deleted
        }


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
    file_hash = fields.CharField(max_length=64, description="文件哈希值")
    
    # 关联关系
    knowledge_base = fields.ForeignKeyField(
        "models.KnowledgeBase", 
        related_name="files",
        description="所属知识库"
    )
    
    # 处理状态
    embedding_status = fields.CharEnumField(
        EmbeddingStatus,
        default=EmbeddingStatus.PENDING,
        description="嵌入处理状态"
    )
    
    # 处理结果
    chunk_count = fields.IntField(default=0, description="分块数量")
    embedding_count = fields.IntField(default=0, description="嵌入向量数量")
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 元数据
    metadata = fields.JSONField(default=dict, description="文件元数据")
    uploaded_by = fields.BigIntField(description="上传者用户ID")
    processed_at = fields.DatetimeField(null=True, description="处理完成时间")
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    
    class Meta:
        table = "knowledge_files"
        table_description = "知识文件表"
        unique_together = [("knowledge_base", "file_hash")]
    
    async def can_access(self, user_id: int) -> bool:
        """检查用户是否可以访问此文件"""
        kb = await self.knowledge_base
        return await kb.can_access(user_id)
    
    async def can_modify(self, user_id: int) -> bool:
        """检查用户是否可以修改此文件"""
        kb = await self.knowledge_base
        return await kb.can_modify(user_id)
    
    async def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type.value if self.file_type else None,
            "file_hash": self.file_hash,
            "knowledge_base_id": self.knowledge_base_id,
            "embedding_status": self.embedding_status.value if self.embedding_status else None,
            "chunk_count": self.chunk_count,
            "embedding_count": self.embedding_count,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "uploaded_by": self.uploaded_by,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted
        }
