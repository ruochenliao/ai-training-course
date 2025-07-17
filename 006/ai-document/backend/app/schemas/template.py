from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class TemplateCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class TemplateCategoryCreate(TemplateCategoryBase):
    pass


class TemplateCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TemplateCategory(TemplateCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateTypeBase(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class TemplateTypeCreate(TemplateTypeBase):
    pass


class TemplateTypeUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TemplateType(TemplateTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[TemplateCategory] = None

    class Config:
        from_attributes = True


class TemplateFileBase(BaseModel):
    template_type_id: int
    name: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    content: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class TemplateFileCreate(TemplateFileBase):
    pass


class TemplateFileUpdate(BaseModel):
    template_type_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class TemplateFile(TemplateFileBase):
    id: int
    usage_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    template_type: Optional[TemplateType] = None

    class Config:
        from_attributes = True


# 组合响应模型
class TemplateCategoryWithTypes(TemplateCategory):
    template_types: List[TemplateType] = []


class TemplateTypeWithFiles(TemplateType):
    template_files: List[TemplateFile] = []


class TemplateTreeNode(BaseModel):
    """模板树节点"""
    id: int
    name: str
    type: str  # 'category' | 'type' | 'file'
    description: Optional[str] = None
    children: List['TemplateTreeNode'] = []
    is_active: bool = True
    sort_order: int = 0

    class Config:
        from_attributes = True


# 写作场景配置相关Schema
class WritingFieldConfig(BaseModel):
    """写作字段配置"""
    field_name: str  # 字段显示名称
    field_key: str   # 字段键名
    field_type: str = "text"  # 字段类型: text, textarea, select
    required: bool = False    # 是否必填
    ai_enabled: bool = False  # 是否支持AI生成
    doc_enabled: bool = False # 是否支持选择文档
    placeholder: Optional[str] = None  # 占位符
    options: Optional[List[str]] = None  # 选择项（用于select类型）


class WritingScenarioConfigBase(BaseModel):
    template_type_id: int
    config_name: str
    description: Optional[str] = None
    field_configs: List[WritingFieldConfig] = []
    default_config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class WritingScenarioConfigCreate(WritingScenarioConfigBase):
    pass


class WritingScenarioConfigUpdate(BaseModel):
    template_type_id: Optional[int] = None
    config_name: Optional[str] = None
    description: Optional[str] = None
    field_configs: Optional[List[WritingFieldConfig]] = None
    default_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WritingScenarioConfig(WritingScenarioConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 初始化数据模型
class TemplateInitData(BaseModel):
    categories: List[TemplateCategoryCreate]
    types: List[TemplateTypeCreate]
    files: List[TemplateFileCreate] = []

# 解决自引用问题
TemplateTreeNode.model_rebuild()
