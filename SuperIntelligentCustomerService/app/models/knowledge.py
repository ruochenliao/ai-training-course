"""
知识库管理数据模型
基于Tortoise ORM的知识库和知识文件模型定义
参考006项目的设计架构
"""
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from tortoise import fields
from tortoise.expressions import Q

from .base import BaseModel, TimestampMixin
from .enums import EmbeddingStatus


class KnowledgeBase(BaseModel, TimestampMixin):
    """
    知识库模型
    管理不同类型的知识库，支持公共和私有访问控制
    """
    
    # 基本信息
    name = fields.CharField(max_length=100, description="知识库名称", index=True)
    description = fields.CharField(max_length=500, null=True, description="知识库描述")
    
    # 访问控制
    is_public = fields.BooleanField(default=False, description="是否为公共知识库", index=True)
    owner_id = fields.IntField(description="所有者ID", index=True)
    
    # 知识库类型
    knowledge_type = fields.CharField(
        max_length=50,
        description="知识库类型",
        default="customer_service",
        index=True
    )
    
    # 配置信息
    config = fields.TextField(default="{}", description="知识库配置JSON")
    embedding_model = fields.CharField(max_length=100, null=True, description="嵌入模型")
    chunk_size = fields.IntField(default=1000, description="分块大小")
    chunk_overlap = fields.IntField(default=200, description="分块重叠")

    # 文件限制
    max_file_size = fields.BigIntField(default=52428800, description="最大文件大小(字节)")  # 50MB
    allowed_file_types = fields.TextField(
        default='["pdf", "docx", "txt", "md"]',
        description="允许的文件类型JSON"
    )
    
    # 统计信息
    file_count = fields.IntField(default=0, description="文件数量")
    total_size = fields.BigIntField(default=0, description="总大小(字节)")
    
    # 处理状态
    status = fields.CharField(max_length=20, default="active", description="知识库状态")
    last_updated_at = fields.DatetimeField(null=True, description="最后更新时间")
    
    # 软删除
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")
    
    class Meta:
        table = "knowledge_bases"
        indexes = [
            ["owner_id", "knowledge_type"],
            ["is_public", "status"],
            ["name"],
            ["created_at"],
        ]

    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        try:
            return json.loads(self.config) if self.config else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_config(self, config: Dict[str, Any]):
        """设置配置信息"""
        self.config = json.dumps(config, ensure_ascii=False)

    def get_allowed_file_types(self) -> List[str]:
        """获取允许的文件类型"""
        try:
            return json.loads(self.allowed_file_types) if self.allowed_file_types else ["pdf", "docx", "txt", "md"]
        except (json.JSONDecodeError, TypeError):
            return ["pdf", "docx", "txt", "md"]

    def set_allowed_file_types(self, file_types: List[str]):
        """设置允许的文件类型"""
        self.allowed_file_types = json.dumps(file_types, ensure_ascii=False)

    async def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "owner_id": self.owner_id,
            "knowledge_type": self.knowledge_type,
            "config": self.get_config(),
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_file_size": self.max_file_size,
            "allowed_file_types": self.get_allowed_file_types(),
            "file_count": self.file_count,
            "total_size": self.total_size,
            "status": self.status,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    async def can_access(self, user_id: int) -> bool:
        """检查用户是否有权限访问此知识库"""
        return self.is_public or self.owner_id == user_id

    async def can_edit(self, user_id: int) -> bool:
        """检查用户是否有权限编辑此知识库"""
        return self.owner_id == user_id

    async def update_stats(self):
        """更新统计信息"""
        files = await self.files.filter(is_deleted=False).all()
        self.file_count = len(files)
        self.total_size = sum(f.file_size for f in files if f.file_size)
        self.last_updated_at = datetime.now()
        await self.save()

    async def soft_delete(self):
        """软删除知识库"""
        self.is_deleted = True
        self.deleted_at = datetime.now()
        await self.save()
        
        # 同时软删除所有文件
        await KnowledgeFile.filter(knowledge_base_id=self.id).update(
            is_deleted=True,
            deleted_at=datetime.now()
        )

    @classmethod
    async def get_accessible_query(cls, user_id: int):
        """获取用户可访问的知识库查询条件"""
        return Q(Q(owner_id=user_id) | Q(is_public=True)) & Q(is_deleted=False)


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
    file_type = fields.CharField(max_length=50, description="文件类型")
    file_hash = fields.CharField(max_length=64, description="文件哈希值", index=True)

    # 关联关系
    knowledge_base = fields.ForeignKeyField(
        "models.KnowledgeBase",
        related_name="files",
        description="所属知识库"
    )

    # 处理状态
    embedding_status = fields.CharField(
        max_length=20,
        default="pending",
        description="嵌入处理状态"
    )
    embedding_error = fields.TextField(null=True, description="嵌入错误信息")
    processed_at = fields.DatetimeField(null=True, description="处理完成时间")

    # 分块信息
    chunk_count = fields.IntField(default=0, description="分块数量")
    vector_ids = fields.TextField(default="[]", description="向量ID列表JSON")

    # 软删除
    is_deleted = fields.BooleanField(default=False, description="是否已删除")
    deleted_at = fields.DatetimeField(null=True, description="删除时间")

    class Meta:
        table = "knowledge_files"
        indexes = [
            ["knowledge_base_id", "embedding_status"],
            ["file_hash"],
            ["created_at"],
        ]

    def get_vector_ids(self) -> List[str]:
        """获取向量ID列表"""
        try:
            return json.loads(self.vector_ids) if self.vector_ids else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_vector_ids(self, vector_ids: List[str]):
        """设置向量ID列表"""
        self.vector_ids = json.dumps(vector_ids, ensure_ascii=False)

    async def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "file_hash": self.file_hash,
            "knowledge_base_id": self.knowledge_base_id,
            "embedding_status": self.embedding_status,
            "embedding_error": self.embedding_error,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "chunk_count": self.chunk_count,
            "vector_ids": self.get_vector_ids(),
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.sha256(file_content).hexdigest()

    async def update_embedding_status(self, status: str, error: str = None):
        """更新嵌入状态"""
        self.embedding_status = status
        if error:
            self.embedding_error = error
        if status == EmbeddingStatus.COMPLETED:
            self.processed_at = datetime.now()
        await self.save()

    async def soft_delete(self):
        """软删除文件"""
        self.is_deleted = True
        self.deleted_at = datetime.now()
        await self.save()

        # 更新知识库统计信息
        kb = await self.knowledge_base
        await kb.update_stats()

    async def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return os.path.splitext(self.original_name)[1].lower()

    async def is_supported_type(self, allowed_types: List[str]) -> bool:
        """检查文件类型是否支持"""
        ext = await self.get_file_extension()
        return ext.lstrip('.') in allowed_types

    @classmethod
    async def check_duplicate(cls, knowledge_base_id: int, file_hash: str) -> Optional['KnowledgeFile']:
        """检查是否存在重复文件"""
        return await cls.filter(
            knowledge_base_id=knowledge_base_id,
            file_hash=file_hash,
            is_deleted=False
        ).first()

    @classmethod
    async def get_processing_stats(cls, knowledge_base_id: int) -> Dict[str, int]:
        """获取文件处理状态统计"""
        files = await cls.filter(knowledge_base_id=knowledge_base_id, is_deleted=False).all()

        stats = {
            EmbeddingStatus.PENDING: 0,
            EmbeddingStatus.PROCESSING: 0,
            EmbeddingStatus.COMPLETED: 0,
            EmbeddingStatus.FAILED: 0,
        }

        for file in files:
            if file.embedding_status in stats:
                stats[file.embedding_status] += 1

        return stats
