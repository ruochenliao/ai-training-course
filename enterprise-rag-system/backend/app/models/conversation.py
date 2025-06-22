"""
对话相关数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List

from tortoise import fields

from .base import (
    BaseModel,
    TimestampMixin,
    StatusMixin,
    SoftDeleteMixin,
    OwnershipMixin,
    MetadataMixin
)


class Conversation(BaseModel, TimestampMixin, StatusMixin, SoftDeleteMixin, OwnershipMixin, MetadataMixin):
    """对话会话模型"""
    
    # 基本信息
    title = fields.CharField(max_length=200, null=True, description="对话标题")
    
    # 配置信息
    knowledge_base_ids = fields.JSONField(default=list, description="使用的知识库ID列表")
    retrieval_config = fields.JSONField(default=dict, description="检索配置")
    model_config = fields.JSONField(default=dict, description="模型配置")
    
    # 统计信息
    message_count = fields.IntField(default=0, description="消息数量")
    total_tokens = fields.IntField(default=0, description="总Token数")
    
    # 会话状态
    is_active = fields.BooleanField(default=True, description="是否活跃")
    last_message_at = fields.DatetimeField(null=True, description="最后消息时间")
    
    # 评价信息
    rating = fields.FloatField(null=True, description="用户评分")
    feedback = fields.TextField(null=True, description="用户反馈")
    
    class Meta:
        table = "conversations"
        indexes = [
            ["owner_id", "is_active"],
            ["last_message_at"],
            ["created_at"],
            ["status"],
        ]
    
    async def get_messages(self, limit: int = None) -> List["Message"]:
        """获取消息列表"""
        query = Message.filter(conversation_id=self.id).order_by("created_at")
        if limit:
            query = query.limit(limit)
        return await query.all()
    
    async def get_latest_messages(self, limit: int = 10) -> List["Message"]:
        """获取最新消息"""
        return await Message.filter(conversation_id=self.id).order_by("-created_at").limit(limit)
    
    async def add_message(self, role: str, content: str, **kwargs) -> "Message":
        """添加消息"""
        message = await Message.create(
            conversation_id=self.id,
            role=role,
            content=content,
            **kwargs
        )
        
        # 更新会话统计
        self.message_count += 1
        self.last_message_at = datetime.now()
        if kwargs.get("token_count"):
            self.total_tokens += kwargs["token_count"]
        
        await self.save(update_fields=["message_count", "last_message_at", "total_tokens"])
        
        return message
    
    async def update_title(self, title: str = None):
        """更新标题"""
        if not title:
            # 自动生成标题（基于第一条用户消息）
            first_user_message = await Message.filter(
                conversation_id=self.id, 
                role="user"
            ).first()
            
            if first_user_message:
                # 截取前50个字符作为标题
                title = first_user_message.content[:50]
                if len(first_user_message.content) > 50:
                    title += "..."
        
        if title:
            self.title = title
            await self.save(update_fields=["title"])
    
    def get_retrieval_config(self, key: str, default=None):
        """获取检索配置"""
        return self.retrieval_config.get(key, default)
    
    def set_retrieval_config(self, key: str, value):
        """设置检索配置"""
        if not isinstance(self.retrieval_config, dict):
            self.retrieval_config = {}
        self.retrieval_config[key] = value
    
    def get_model_config(self, key: str, default=None):
        """获取模型配置"""
        return self.model_config.get(key, default)
    
    def set_model_config(self, key: str, value):
        """设置模型配置"""
        if not isinstance(self.model_config, dict):
            self.model_config = {}
        self.model_config[key] = value


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    MULTIMODAL = "multimodal"


class Message(BaseModel, TimestampMixin, MetadataMixin):
    """消息模型"""
    
    # 关联关系
    conversation = fields.ForeignKeyField(
        "models.Conversation", 
        related_name="messages", 
        on_delete=fields.CASCADE,
        description="所属对话"
    )
    
    # 消息内容
    role = fields.CharEnumField(MessageRole, description="消息角色", index=True)
    message_type = fields.CharEnumField(MessageType, default=MessageType.TEXT, description="消息类型")
    content = fields.TextField(description="消息内容")
    
    # 多模态内容
    images = fields.JSONField(default=list, description="图片列表")
    files = fields.JSONField(default=list, description="文件列表")
    
    # 处理信息
    token_count = fields.IntField(null=True, description="Token数量")
    processing_time = fields.FloatField(null=True, description="处理时间(秒)")
    
    # 检索信息
    retrieval_results = fields.JSONField(default=list, description="检索结果")
    sources = fields.JSONField(default=list, description="来源信息")
    
    # 模型信息
    model_name = fields.CharField(max_length=100, null=True, description="使用的模型")
    model_config = fields.JSONField(default=dict, description="模型配置")
    
    # 质量评估
    quality_score = fields.FloatField(null=True, description="质量评分")
    relevance_score = fields.FloatField(null=True, description="相关性评分")
    
    # 用户反馈
    user_rating = fields.IntField(null=True, description="用户评分(1-5)")
    user_feedback = fields.TextField(null=True, description="用户反馈")
    
    # 状态信息
    is_streaming = fields.BooleanField(default=False, description="是否流式输出")
    is_completed = fields.BooleanField(default=True, description="是否完成")
    
    class Meta:
        table = "messages"
        indexes = [
            ["conversation_id", "created_at"],
            ["role"],
            ["message_type"],
            ["is_completed"],
        ]
    
    async def get_conversation(self) -> "Conversation":
        """获取所属对话"""
        return await self.conversation
    
    def is_user_message(self) -> bool:
        """是否为用户消息"""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """是否为助手消息"""
        return self.role == MessageRole.ASSISTANT

    def is_multimodal(self) -> bool:
        """是否为多模态消息"""
        return self.message_type == MessageType.MULTIMODAL or bool(self.images) or bool(self.files)
    
    def has_images(self) -> bool:
        """是否包含图片"""
        return bool(self.images)
    
    def has_files(self) -> bool:
        """是否包含文件"""
        return bool(self.files)
    
    def has_sources(self) -> bool:
        """是否有来源信息"""
        return bool(self.sources)
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """获取内容预览"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    async def add_source(self, source_info: dict):
        """添加来源信息"""
        if not isinstance(self.sources, list):
            self.sources = []
        self.sources.append(source_info)
        await self.save(update_fields=["sources"])
    
    async def set_user_feedback(self, rating: int, feedback: str = None):
        """设置用户反馈"""
        self.user_rating = rating
        self.user_feedback = feedback
        await self.save(update_fields=["user_rating", "user_feedback"])


class FeedbackType(str, Enum):
    """反馈类型枚举"""
    LIKE = "like"
    DISLIKE = "dislike"
    REPORT = "report"


class MessageFeedback(BaseModel, TimestampMixin):
    """消息反馈模型"""
    
    # 关联关系
    message = fields.ForeignKeyField(
        "models.Message", 
        related_name="feedbacks", 
        on_delete=fields.CASCADE,
        description="相关消息"
    )
    
    # 反馈信息
    feedback_type = fields.CharEnumField(FeedbackType, description="反馈类型")
    rating = fields.IntField(null=True, description="评分(1-5)")
    comment = fields.TextField(null=True, description="评论")
    
    # 反馈者信息
    user_id = fields.IntField(description="反馈用户ID", index=True)
    ip_address = fields.CharField(max_length=45, null=True, description="IP地址")
    
    # 处理状态
    is_processed = fields.BooleanField(default=False, description="是否已处理")
    processed_by = fields.IntField(null=True, description="处理人ID")
    processed_at = fields.DatetimeField(null=True, description="处理时间")
    
    class Meta:
        table = "message_feedbacks"
        indexes = [
            ["message_id", "feedback_type"],
            ["user_id"],
            ["is_processed"],
            ["created_at"],
        ]
        unique_together = [["message", "user_id"]]  # 每个用户对每条消息只能反馈一次
