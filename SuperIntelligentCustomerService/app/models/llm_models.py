# -*- coding: utf-8 -*-
"""
LLM模型管理数据库模型
基于 llms.py 设计的动态模型配置系统
"""
from typing import Dict, Any

from tortoise import fields

from .base import BaseModel, TimestampMixin


class LLMProvider(BaseModel, TimestampMixin):
    """LLM提供商配置"""
    name = fields.CharField(max_length=50, unique=True, description="提供商名称", index=True)
    display_name = fields.CharField(max_length=100, description="显示名称")
    description = fields.TextField(null=True, description="提供商描述")
    base_url = fields.CharField(max_length=255, description="API基础URL")
    api_key = fields.CharField(max_length=500, null=True, description="API密钥（加密存储）")
    headers = fields.JSONField(default=dict, description="默认请求头")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    sort_order = fields.IntField(default=0, description="排序顺序")
    
    class Meta:
        table = "llm_provider"
        ordering = ["sort_order", "name"]


class LLMModel(BaseModel, TimestampMixin):
    """LLM模型配置"""
    provider = fields.ForeignKeyField("models.LLMProvider", related_name="models", description="所属提供商")
    
    # 基本信息
    model_name = fields.CharField(max_length=100, description="模型名称", index=True)
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
        unique_together = (("provider", "model_name"),)
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
        provider = await self.provider
        
        config = {
            "model": self.model_name,
            "base_url": provider.base_url,
            "api_key": provider.api_key,
            "model_info": await self.to_model_info(),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        
        # 添加自定义配置
        if self.custom_config:
            config.update(self.custom_config)
            
        return config


class LLMModelUsage(BaseModel, TimestampMixin):
    """LLM模型使用统计"""
    model = fields.ForeignKeyField("models.LLMModel", related_name="usage_stats", description="关联模型")
    
    # 使用统计
    total_requests = fields.BigIntField(default=0, description="总请求次数")
    total_input_tokens = fields.BigIntField(default=0, description="总输入令牌数")
    total_output_tokens = fields.BigIntField(default=0, description="总输出令牌数")
    total_cost = fields.DecimalField(max_digits=15, decimal_places=6, default=0, description="总费用")
    
    # 性能统计
    avg_response_time = fields.FloatField(default=0, description="平均响应时间（秒）")
    success_rate = fields.FloatField(default=100, description="成功率（%）")
    
    # 时间维度
    date = fields.DateField(description="统计日期", index=True)
    
    class Meta:
        table = "llm_model_usage"
        unique_together = (("model", "date"),)
        ordering = ["-date"]


class LLMModelPreset(BaseModel, TimestampMixin):
    """LLM模型预设配置"""
    name = fields.CharField(max_length=100, unique=True, description="预设名称", index=True)
    display_name = fields.CharField(max_length=100, description="显示名称")
    description = fields.TextField(null=True, description="预设描述")
    
    # 关联模型
    models = fields.ManyToManyField("models.LLMModel", related_name="presets", description="包含的模型")
    
    # 预设配置
    system_prompt = fields.TextField(null=True, description="系统提示词")
    temperature = fields.FloatField(null=True, description="温度设置")
    top_p = fields.FloatField(null=True, description="top_p设置")
    max_tokens = fields.IntField(null=True, description="最大令牌数")
    
    # 使用场景
    use_cases = fields.JSONField(default=list, description="适用场景")
    tags = fields.JSONField(default=list, description="标签")
    
    # 状态管理
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    is_public = fields.BooleanField(default=True, description="是否公开")
    sort_order = fields.IntField(default=0, description="排序顺序")
    
    class Meta:
        table = "llm_model_preset"
        ordering = ["sort_order", "display_name"]


class LLMModelConfig(BaseModel, TimestampMixin):
    """LLM模型运行时配置"""
    model = fields.ForeignKeyField("models.LLMModel", related_name="runtime_configs", description="关联模型")
    
    # 配置标识
    config_name = fields.CharField(max_length=100, description="配置名称", index=True)
    config_type = fields.CharField(max_length=50, description="配置类型", index=True)  # system, user, preset
    
    # 配置内容
    config_data = fields.JSONField(description="配置数据")
    
    # 状态管理
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    priority = fields.IntField(default=0, description="优先级")
    
    class Meta:
        table = "llm_model_config"
        unique_together = (("model", "config_name", "config_type"),)
        ordering = ["-priority", "config_name"]
