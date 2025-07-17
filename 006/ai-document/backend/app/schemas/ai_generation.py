"""
AI生成相关Schema定义
统一的字段内容生成请求和响应模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class FieldType(str, Enum):
    """字段类型枚举"""
    CONFIGURED = "configured"  # 使用配置的智能体
    SMART = "smart"           # 智能选择智能体
    DEFAULT = "default"       # 使用默认智能体


class GenerationContext(BaseModel):
    """生成上下文"""
    # 基础信息
    category: Optional[str] = None          # 文档分类
    type: Optional[str] = None              # 文档类型
    content_type: Optional[str] = None      # 完整内容类型
    
    # 已有内容
    title: Optional[str] = None             # 标题
    keywords: Optional[str] = None          # 关键词
    content: Optional[str] = None           # 主要内容
    reason: Optional[str] = None            # 原因
    purpose: Optional[str] = None           # 目的
    
    # 模板信息
    template_type_id: Optional[int] = None  # 模板类型ID
    scenario_config_id: Optional[int] = None # 场景配置ID
    
    # 扩展信息
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class FieldGenerateRequest(BaseModel):
    """单个字段生成请求"""
    field_key: str = Field(..., description="字段键名")
    field_name: str = Field(..., description="字段显示名称")
    field_type: FieldType = Field(default=FieldType.SMART, description="字段类型")
    
    # 生成配置
    agent_id: Optional[int] = Field(None, description="指定的智能体ID")
    user_input: Optional[str] = Field(None, description="用户输入内容")
    
    # 上下文信息
    context: Dict[str, Any] = Field(default_factory=dict, description="生成上下文")
    
    # 生成选项
    max_length: Optional[int] = Field(None, description="最大长度限制")
    style: Optional[str] = Field(None, description="生成风格")
    temperature: Optional[float] = Field(None, description="生成温度")


class FieldGenerateResponse(BaseModel):
    """单个字段生成响应"""
    success: bool = Field(..., description="是否成功")
    content: Optional[str] = Field(None, description="生成的内容")
    error: Optional[str] = Field(None, description="错误信息")
    
    # 字段信息
    field_key: str = Field(..., description="字段键名")
    
    # 生成信息
    agent_used: Optional[str] = Field(None, description="使用的智能体名称")
    generation_time: Optional[float] = Field(None, description="生成耗时（秒）")
    token_count: Optional[int] = Field(None, description="生成的token数量")
    
    # 质量评估
    quality_score: Optional[float] = Field(None, description="内容质量分数")
    confidence: Optional[float] = Field(None, description="生成置信度")


class BatchGenerateRequest(BaseModel):
    """批量字段生成请求"""
    fields: List[FieldGenerateRequest] = Field(..., description="要生成的字段列表")
    global_context: Dict[str, Any] = Field(default_factory=dict, description="全局上下文")
    
    # 批量选项
    parallel: bool = Field(default=False, description="是否并行生成")
    stop_on_error: bool = Field(default=False, description="遇到错误是否停止")
    max_concurrent: int = Field(default=3, description="最大并发数")


class BatchGenerateResponse(BaseModel):
    """批量字段生成响应"""
    success: bool = Field(..., description="整体是否成功")
    results: List[FieldGenerateResponse] = Field(..., description="各字段生成结果")
    
    # 统计信息
    success_count: int = Field(..., description="成功生成的字段数")
    total_count: int = Field(..., description="总字段数")
    total_time: Optional[float] = Field(None, description="总耗时（秒）")
    
    # 错误信息
    error: Optional[str] = Field(None, description="整体错误信息")


class SmartGenerateRequest(BaseModel):
    """智能生成请求"""
    prompt: str = Field(..., description="生成提示")
    context: GenerationContext = Field(..., description="生成上下文")
    
    # 智能选项
    auto_select_agent: bool = Field(default=True, description="自动选择智能体")
    optimize_prompt: bool = Field(default=True, description="优化提示词")
    quality_threshold: float = Field(default=0.7, description="质量阈值")
    
    # 生成约束
    max_tokens: Optional[int] = Field(None, description="最大token数")
    target_length: Optional[int] = Field(None, description="目标长度")
    required_keywords: List[str] = Field(default_factory=list, description="必须包含的关键词")


class SmartGenerateResponse(BaseModel):
    """智能生成响应"""
    success: bool = Field(..., description="是否成功")
    content: Optional[str] = Field(None, description="生成的内容")
    error: Optional[str] = Field(None, description="错误信息")
    
    # 智能信息
    strategy_used: str = Field(..., description="使用的生成策略")
    agent_used: str = Field(..., description="使用的智能体")
    confidence_score: float = Field(..., description="置信度分数")
    
    # 性能信息
    generation_time: float = Field(..., description="生成耗时（秒）")
    optimization_applied: List[str] = Field(default_factory=list, description="应用的优化")
    
    # 质量信息
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="质量指标")


class GenerationTemplate(BaseModel):
    """生成模板"""
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    
    # 模板配置
    field_configs: List[Dict[str, Any]] = Field(..., description="字段配置")
    default_agents: Dict[str, int] = Field(default_factory=dict, description="默认智能体映射")
    generation_order: List[str] = Field(default_factory=list, description="生成顺序")
    
    # 模板选项
    parallel_fields: List[str] = Field(default_factory=list, description="可并行生成的字段")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="字段依赖关系")


class GenerationHistory(BaseModel):
    """生成历史记录"""
    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    
    # 请求信息
    request_type: str = Field(..., description="请求类型")
    field_key: Optional[str] = Field(None, description="字段键名")
    prompt: str = Field(..., description="生成提示")
    context: Dict[str, Any] = Field(..., description="生成上下文")
    
    # 响应信息
    success: bool = Field(..., description="是否成功")
    content: Optional[str] = Field(None, description="生成内容")
    error: Optional[str] = Field(None, description="错误信息")
    
    # 元信息
    agent_used: Optional[str] = Field(None, description="使用的智能体")
    generation_time: Optional[float] = Field(None, description="生成耗时")
    created_at: datetime = Field(..., description="创建时间")


class GenerationStats(BaseModel):
    """生成统计信息"""
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    
    # 性能统计
    avg_generation_time: float = Field(..., description="平均生成时间")
    total_tokens_generated: int = Field(..., description="总生成token数")
    
    # 使用统计
    most_used_agents: List[Dict[str, Any]] = Field(..., description="最常用智能体")
    most_generated_fields: List[Dict[str, Any]] = Field(..., description="最常生成字段")
    
    # 质量统计
    avg_quality_score: float = Field(..., description="平均质量分数")
    quality_distribution: Dict[str, int] = Field(..., description="质量分布")


# 兼容性Schema（保持向后兼容）
class LegacyAIGenerateRequest(BaseModel):
    """旧版AI生成请求（兼容性）"""
    field_key: str
    field_name: str
    context: Dict[str, Any] = {}
    user_input: Optional[str] = None
    template_type_id: int


class LegacyAIGenerateDirectRequest(BaseModel):
    """旧版直接AI生成请求（兼容性）"""
    user_prompt: str
    context: Dict[str, Any] = {}


class LegacyAIGenerateResponse(BaseModel):
    """旧版AI生成响应（兼容性）"""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
