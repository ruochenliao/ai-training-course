# -*- coding: utf-8 -*-
"""
LLM模型管理数据库模型
简化版本：只保留核心的LLM模型配置表
"""
from typing import Dict, Any

from tortoise import fields

from .base import BaseModel, TimestampMixin


class LLMModel(BaseModel, TimestampMixin):
    """LLM模型配置"""
    # 提供商信息（直接存储，不使用外键）
    provider_name = fields.CharField(max_length=50, description="提供商名称", index=True)
    provider_display_name = fields.CharField(max_length=100, description="提供商显示名称")
    base_url = fields.CharField(max_length=255, description="API基础URL")
    api_key = fields.CharField(max_length=500, null=True, description="API密钥（加密存储）")

    # 基本信息
    model_name = fields.CharField(max_length=100, description="模型名称", index=True, unique=True)
    display_name = fields.CharField(max_length=100, description="显示名称")
    description = fields.TextField(null=True, description="模型描述")
    category = fields.CharField(max_length=50, description="模型分类", index=True)

    # 模型能力配置（基于 ModelInfo）
    vision = fields.BooleanField(default=False, description="支持视觉功能")
    function_calling = fields.BooleanField(default=False, description="支持函数调用")
    json_output = fields.BooleanField(default=False, description="支持JSON输出")
    structured_output = fields.BooleanField(default=False, description="支持结构化输出")
    multiple_system_messages = fields.BooleanField(default=False, description="支持多个系统消息")
    model_family = fields.CharField(max_length=50, default="unknown", description="模型系列")

    # 技术配置
    max_tokens = fields.IntField(default=4096, description="最大令牌数")
    temperature = fields.FloatField(default=0.7, description="默认温度")
    top_p = fields.FloatField(default=0.9, description="默认top_p")

    # 定价信息
    input_price_per_1k = fields.DecimalField(max_digits=10, decimal_places=6, default=0, description="输入价格/1K tokens")
    output_price_per_1k = fields.DecimalField(max_digits=10, decimal_places=6, default=0, description="输出价格/1K tokens")

    # 系统配置
    system_prompt = fields.TextField(null=True, description="默认系统提示词")
    custom_config = fields.JSONField(default=dict, description="自定义配置参数")

    # 状态管理
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    is_default = fields.BooleanField(default=False, description="是否为默认模型")
    sort_order = fields.IntField(default=0, description="排序顺序")

    class Meta:
        table = "llm_model"
        ordering = ["sort_order", "display_name"]

    async def to_model_info(self) -> Dict[str, Any]:
        """转换为 AutoGen ModelInfo 格式"""
        return {
            "vision": self.vision,
            "function_calling": self.function_calling,
            "json_output": self.json_output,
            "structured_output": self.structured_output,
            "multiple_system_messages": self.multiple_system_messages,
            "family": self.model_family
        }

    async def to_client_config(self) -> Dict[str, Any]:
        """转换为模型客户端配置"""
        config = {
            "model": self.model_name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model_info": await self.to_model_info(),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        # 添加自定义配置
        if self.custom_config:
            config.update(self.custom_config)

        return config
