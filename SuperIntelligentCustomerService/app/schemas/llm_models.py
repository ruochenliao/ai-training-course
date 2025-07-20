# -*- coding: utf-8 -*-
"""
LLM模型管理相关的Pydantic模型
"""
from datetime import date as DateType, datetime as DateTimeType
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


# ==================== LLM提供商相关 ====================

class LLMProviderBase(BaseModel):
    """LLM提供商基础模型"""
    name: str = Field(..., description="提供商名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="提供商描述")
    base_url: str = Field(..., description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, Any] = Field(default_factory=dict, description="默认请求头")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序顺序")


class LLMProviderCreate(LLMProviderBase):
    """创建LLM提供商"""
    pass


class LLMProviderUpdate(BaseModel):
    """更新LLM提供商"""
    name: Optional[str] = Field(None, description="提供商名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="提供商描述")
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Optional[Dict[str, Any]] = Field(None, description="默认请求头")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class LLMProviderResponse(LLMProviderBase):
    """LLM提供商响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="提供商ID")
    created_at: DateTimeType = Field(..., description="创建时间")
    updated_at: DateTimeType = Field(..., description="更新时间")


# ==================== LLM模型相关 ====================

class LLMModelBase(BaseModel):
    """LLM模型基础模型"""
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="模型描述")
    category: str = Field(..., description="模型分类")
    
    # 模型能力
    vision: bool = Field(False, description="支持视觉功能")
    function_calling: bool = Field(False, description="支持函数调用")
    json_output: bool = Field(False, description="支持JSON输出")
    structured_output: bool = Field(False, description="支持结构化输出")
    multiple_system_messages: bool = Field(False, description="支持多个系统消息")
    model_family: str = Field("unknown", description="模型系列")
    
    # 技术配置
    max_tokens: int = Field(4096, description="最大令牌数")
    temperature: float = Field(0.7, description="默认温度")
    top_p: float = Field(0.9, description="默认top_p")
    
    # 定价信息
    input_price_per_1k: Decimal = Field(0, description="输入价格/1K tokens")
    output_price_per_1k: Decimal = Field(0, description="输出价格/1K tokens")
    
    # 系统配置
    system_prompt: Optional[str] = Field(None, description="默认系统提示词")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="自定义配置参数")
    
    # 状态管理
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认模型")
    sort_order: int = Field(0, description="排序顺序")


class LLMModelCreate(LLMModelBase):
    """创建LLM模型"""
    provider_id: int = Field(..., description="提供商ID")


class LLMModelUpdate(BaseModel):
    """更新LLM模型"""
    provider_id: Optional[int] = Field(None, description="提供商ID")
    model_name: Optional[str] = Field(None, description="模型名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="模型描述")
    category: Optional[str] = Field(None, description="模型分类")
    
    # 模型能力
    vision: Optional[bool] = Field(None, description="支持视觉功能")
    function_calling: Optional[bool] = Field(None, description="支持函数调用")
    json_output: Optional[bool] = Field(None, description="支持JSON输出")
    structured_output: Optional[bool] = Field(None, description="支持结构化输出")
    multiple_system_messages: Optional[bool] = Field(None, description="支持多个系统消息")
    model_family: Optional[str] = Field(None, description="模型系列")
    
    # 技术配置
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    temperature: Optional[float] = Field(None, description="默认温度")
    top_p: Optional[float] = Field(None, description="默认top_p")
    
    # 定价信息
    input_price_per_1k: Optional[Decimal] = Field(None, description="输入价格/1K tokens")
    output_price_per_1k: Optional[Decimal] = Field(None, description="输出价格/1K tokens")
    
    # 系统配置
    system_prompt: Optional[str] = Field(None, description="默认系统提示词")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置参数")
    
    # 状态管理
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认模型")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class LLMModelResponse(LLMModelBase):
    """LLM模型响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="模型ID")
    provider_id: int = Field(..., description="提供商ID")
    created_at: DateTimeType = Field(..., description="创建时间")
    updated_at: DateTimeType = Field(..., description="更新时间")


class LLMModelWithProvider(LLMModelResponse):
    """包含提供商信息的LLM模型"""
    provider: LLMProviderResponse = Field(..., description="提供商信息")


# ==================== 模型使用统计相关 ====================

class LLMModelUsageResponse(BaseModel):
    """LLM模型使用统计响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="统计ID")
    model_id: int = Field(..., description="模型ID")
    total_requests: int = Field(..., description="总请求次数")
    total_input_tokens: int = Field(..., description="总输入令牌数")
    total_output_tokens: int = Field(..., description="总输出令牌数")
    total_cost: Decimal = Field(..., description="总费用")
    avg_response_time: float = Field(..., description="平均响应时间")
    success_rate: float = Field(..., description="成功率")
    date: DateType = Field(..., description="统计日期")


# ==================== 模型预设相关 ====================

class LLMModelPresetBase(BaseModel):
    """LLM模型预设基础模型"""
    name: str = Field(..., description="预设名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="预设描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, description="温度设置")
    top_p: Optional[float] = Field(None, description="top_p设置")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    use_cases: List[str] = Field(default_factory=list, description="适用场景")
    tags: List[str] = Field(default_factory=list, description="标签")
    is_active: bool = Field(True, description="是否启用")
    is_public: bool = Field(True, description="是否公开")
    sort_order: int = Field(0, description="排序顺序")


class LLMModelPresetCreate(LLMModelPresetBase):
    """创建LLM模型预设"""
    model_ids: List[int] = Field(..., description="包含的模型ID列表")


class LLMModelPresetUpdate(BaseModel):
    """更新LLM模型预设"""
    name: Optional[str] = Field(None, description="预设名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="预设描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, description="温度设置")
    top_p: Optional[float] = Field(None, description="top_p设置")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    use_cases: Optional[List[str]] = Field(None, description="适用场景")
    tags: Optional[List[str]] = Field(None, description="标签")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_public: Optional[bool] = Field(None, description="是否公开")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    model_ids: Optional[List[int]] = Field(None, description="包含的模型ID列表")


class LLMModelPresetResponse(LLMModelPresetBase):
    """LLM模型预设响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="预设ID")
    created_at: DateTimeType = Field(..., description="创建时间")
    updated_at: DateTimeType = Field(..., description="更新时间")


# ==================== 通用响应模型 ====================

class LLMModelListResponse(BaseModel):
    """LLM模型列表响应"""
    total: int = Field(..., description="总数量")
    items: List[LLMModelWithProvider] = Field(..., description="模型列表")


class LLMProviderListResponse(BaseModel):
    """LLM提供商列表响应"""
    total: int = Field(..., description="总数量")
    items: List[LLMProviderResponse] = Field(..., description="提供商列表")


class LLMModelPresetListResponse(BaseModel):
    """LLM模型预设列表响应"""
    total: int = Field(..., description="总数量")
    items: List[LLMModelPresetResponse] = Field(..., description="预设列表")


# ==================== 模型客户端配置 ====================

class ModelClientConfig(BaseModel):
    """模型客户端配置"""
    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    model_info: Dict[str, Any] = Field(..., description="模型信息")
    temperature: float = Field(0.7, description="温度")
    top_p: float = Field(0.9, description="top_p")
    max_tokens: int = Field(4096, description="最大令牌数")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="自定义配置")
