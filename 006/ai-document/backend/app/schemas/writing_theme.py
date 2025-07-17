"""
写作主题相关的数据传输对象
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ThemeFieldBase(BaseModel):
    """主题字段基础模型"""
    field_key: str = Field(..., description="字段键名")
    field_label: str = Field(..., description="字段标签")
    field_type: str = Field(default="text", description="字段类型")
    placeholder: Optional[str] = Field(None, description="占位符文本")
    default_value: Optional[str] = Field(None, description="默认值")
    is_required: bool = Field(default=False, description="是否必填")
    max_length: Optional[int] = Field(None, description="最大长度")
    min_length: Optional[int] = Field(None, description="最小长度")
    options: Optional[Dict[str, Any]] = Field(None, description="选择项配置")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    sort_order: int = Field(default=0, description="显示顺序")
    is_visible: bool = Field(default=True, description="是否显示")
    help_text: Optional[str] = Field(None, description="帮助文本")


class ThemeFieldCreate(ThemeFieldBase):
    """创建主题字段"""
    pass


class ThemeFieldUpdate(BaseModel):
    """更新主题字段"""
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = None
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    options: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None
    help_text: Optional[str] = None


class ThemeField(ThemeFieldBase):
    """主题字段响应模型"""
    id: int
    theme_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromptTemplateBase(BaseModel):
    """提示词模板基础模型"""
    template_name: str = Field(..., description="模板名称")
    template_type: str = Field(default="main", description="模板类型")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    user_prompt_template: str = Field(..., description="用户提示词模板")
    variables: Optional[Dict[str, Any]] = Field(None, description="模板变量配置")
    ai_model: Optional[str] = Field(None, description="推荐AI模型")
    temperature: Optional[str] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    is_active: bool = Field(default=True, description="是否启用")
    version: str = Field(default="1.0", description="模板版本")


class PromptTemplateCreate(PromptTemplateBase):
    """创建提示词模板"""
    pass


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板"""
    template_name: Optional[str] = None
    template_type: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    ai_model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None


class PromptTemplate(PromptTemplateBase):
    """提示词模板响应模型"""
    id: int
    theme_id: int
    usage_count: int
    success_rate: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WritingThemeBase(BaseModel):
    """写作主题基础模型"""
    name: str = Field(..., description="主题名称")
    description: Optional[str] = Field(None, description="主题描述")
    category: str = Field(..., description="主题分类")
    icon: Optional[str] = Field(None, description="主题图标")
    theme_key: str = Field(..., description="主题唯一标识")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序顺序")


class WritingThemeCreate(WritingThemeBase):
    """创建写作主题"""
    fields: List[ThemeFieldCreate] = Field(default=[], description="主题字段")
    prompt_templates: List[PromptTemplateCreate] = Field(default=[], description="提示词模板")


class WritingThemeUpdate(BaseModel):
    """更新写作主题"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class WritingTheme(WritingThemeBase):
    """写作主题响应模型"""
    id: int
    fields: List[ThemeField] = []
    prompt_templates: List[PromptTemplate] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WritingThemeSimple(BaseModel):
    """简化的写作主题模型（用于列表显示）"""
    id: int
    name: str
    description: Optional[str] = None
    category: str
    icon: Optional[str] = None
    theme_key: str
    is_active: bool
    sort_order: int
    field_count: int = Field(default=0, description="字段数量")
    template_count: int = Field(default=0, description="模板数量")
    created_at: datetime

    class Config:
        from_attributes = True


class ThemeCategoryBase(BaseModel):
    """主题分类基础模型"""
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field(None, description="分类颜色")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序顺序")


class ThemeCategoryCreate(ThemeCategoryBase):
    """创建主题分类"""
    pass


class ThemeCategoryUpdate(BaseModel):
    """更新主题分类"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ThemeCategory(ThemeCategoryBase):
    """主题分类响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WritingRequest(BaseModel):
    """写作请求模型"""
    theme_id: int = Field(..., description="主题ID")
    field_values: Dict[str, Any] = Field(..., description="字段值")
    additional_context: Optional[str] = Field(None, description="额外上下文")
    template_id: Optional[int] = Field(None, description="指定模板ID")


class WritingResponse(BaseModel):
    """写作响应模型"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    content: Optional[str] = Field(None, description="生成内容")
    error: Optional[str] = Field(None, description="错误信息")


class TemplatePreviewRequest(BaseModel):
    """模板预览请求"""
    template_id: int = Field(..., description="模板ID")
    field_values: Dict[str, Any] = Field(..., description="字段值")


class TemplatePreviewResponse(BaseModel):
    """模板预览响应"""
    rendered_prompt: str = Field(..., description="渲染后的提示词")
    variables_used: List[str] = Field(..., description="使用的变量")
    estimated_tokens: Optional[int] = Field(None, description="预估令牌数")
