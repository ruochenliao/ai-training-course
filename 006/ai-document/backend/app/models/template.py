from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class TemplateCategory(Base):
    """模板分类表"""
    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    template_types = relationship("TemplateType", back_populates="category", cascade="all, delete-orphan")


class TemplateType(Base):
    """模板类型表"""
    __tablename__ = "template_types"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("template_categories.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="类型名称")
    description = Column(Text, comment="类型描述")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    category = relationship("TemplateCategory", back_populates="template_types")
    template_files = relationship("TemplateFile", back_populates="template_type", cascade="all, delete-orphan")
    writing_scenario_config = relationship("WritingScenarioConfig", back_populates="template_type", uselist=False, cascade="all, delete-orphan")


class TemplateFile(Base):
    """模板文件表"""
    __tablename__ = "template_files"

    id = Column(Integer, primary_key=True, index=True)
    template_type_id = Column(Integer, ForeignKey("template_types.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_type = Column(String(50), comment="文件类型")
    content = Column(Text, comment="模板内容")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    is_active = Column(Boolean, default=True, comment="是否启用")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    template_type = relationship("TemplateType", back_populates="template_files")
    creator = relationship("User", foreign_keys=[created_by])


class WritingScenarioConfig(Base):
    """写作场景配置表"""
    __tablename__ = "writing_scenario_configs"

    id = Column(Integer, primary_key=True, index=True)
    template_type_id = Column(Integer, ForeignKey("template_types.id"), nullable=False, unique=True)
    config_name = Column(String(200), nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")

    # 写作场景字段配置 - JSON格式存储
    # 格式: [{"field_name": "标题", "field_key": "title", "required": true, "ai_enabled": false, "doc_enabled": false}, ...]
    field_configs = Column(JSON, comment="字段配置")

    # 默认配置模板
    default_config = Column(JSON, comment="默认配置模板")

    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    template_type = relationship("TemplateType", back_populates="writing_scenario_config")
    field_configs_rel = relationship("WritingFieldConfig", back_populates="scenario_config", cascade="all, delete-orphan")


class WritingFieldConfig(Base):
    """写作字段配置表"""
    __tablename__ = "writing_field_configs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_config_id = Column(Integer, ForeignKey("writing_scenario_configs.id"), nullable=False)

    # 字段基本信息
    field_name = Column(String(100), nullable=False, comment="字段名称")
    field_key = Column(String(100), nullable=False, comment="字段键名")
    field_type = Column(String(50), default="text", comment="字段类型: text, textarea, select")
    placeholder = Column(String(200), comment="占位符文本")
    options = Column(JSON, comment="选择框选项")

    # 字段属性
    required = Column(Boolean, default=False, comment="是否必填")
    ai_enabled = Column(Boolean, default=False, comment="是否启用AI生成")
    doc_enabled = Column(Boolean, default=False, comment="是否启用文档选择")
    sort_order = Column(Integer, default=0, comment="排序")

    # 智能体配置关联
    agent_config_id = Column(Integer, ForeignKey("agent_configs.id"), nullable=True, comment="关联的智能体配置")

    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    scenario_config = relationship("WritingScenarioConfig", back_populates="field_configs_rel")
    agent_config = relationship("AgentConfig", back_populates="field_configs")
