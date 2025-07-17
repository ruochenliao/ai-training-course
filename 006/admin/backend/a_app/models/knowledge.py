from tortoise import fields

from a_app.models.base import BaseModel, TimestampMixin


class KnowledgeType(str):
    """Knowledge type enum"""
    CUSTOMER_SERVICE = "customer_service"  # 智能客服知识库
    TEXT_SQL = "text_sql"  # TextSQL知识库
    RAG = "rag"  # RAG知识库
    CONTENT_CREATION = "content_creation"  # 文案创作知识库


class KnowledgeBase(BaseModel, TimestampMixin):
    """Knowledge base model"""
    name = fields.CharField(max_length=100, description="知识库名称", index=True)
    description = fields.CharField(max_length=500, null=True, description="知识库描述")
    is_public = fields.BooleanField(default=False, description="是否为公共知识库", index=True)
    owner_id = fields.IntField(description="所有者ID", index=True)
    knowledge_type = fields.CharField(
        max_length=50,
        description="知识库类型",
        default=KnowledgeType.CUSTOMER_SERVICE,
        index=True
    )

    class Meta:
        table = "knowledge_base"


class EmbeddingStatus(str):
    """Embedding status enum"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class KnowledgeFile(BaseModel, TimestampMixin):
    """Knowledge file model"""
    name = fields.CharField(max_length=255, description="文件名称", index=True)
    file_path = fields.CharField(max_length=500, description="文件路径")
    file_size = fields.BigIntField(description="文件大小(字节)")
    file_type = fields.CharField(max_length=100, description="文件类型", index=True)
    embedding_status = fields.CharField(
        max_length=20,
        description="嵌入状态",
        default=EmbeddingStatus.PENDING,
        index=True
    )
    embedding_error = fields.TextField(description="嵌入错误信息", null=True)
    knowledge_base = fields.ForeignKeyField(
        "models.KnowledgeBase", related_name="files", on_delete=fields.CASCADE
    )

    class Meta:
        table = "knowledge_file"
