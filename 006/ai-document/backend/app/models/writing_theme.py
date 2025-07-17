"""
写作主题相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class WritingTheme(Base):
    """写作主题模型"""
    __tablename__ = "writing_themes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="主题名称")
    description = Column(Text, comment="主题描述")
    category = Column(String(50), nullable=False, comment="主题分类")
    icon = Column(String(50), comment="主题图标")
    theme_key = Column(String(50), unique=True, nullable=False, comment="主题唯一标识")
    
    # 状态和排序
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    fields = relationship("ThemeField", back_populates="theme", cascade="all, delete-orphan")
    prompt_templates = relationship("PromptTemplate", back_populates="theme", cascade="all, delete-orphan")


class ThemeField(Base):
    """主题字段模型"""
    __tablename__ = "theme_fields"

    id = Column(Integer, primary_key=True, index=True)
    theme_id = Column(Integer, ForeignKey("writing_themes.id"), nullable=False)
    
    # 字段基本信息
    field_key = Column(String(50), nullable=False, comment="字段键名")
    field_label = Column(String(100), nullable=False, comment="字段标签")
    field_type = Column(String(20), nullable=False, default="text", comment="字段类型")
    
    # 字段配置
    placeholder = Column(String(200), comment="占位符文本")
    default_value = Column(Text, comment="默认值")
    is_required = Column(Boolean, default=False, comment="是否必填")
    max_length = Column(Integer, comment="最大长度")
    min_length = Column(Integer, comment="最小长度")
    
    # 选择项配置 (用于select类型)
    options = Column(JSON, comment="选择项配置")
    
    # 验证规则
    validation_rules = Column(JSON, comment="验证规则")
    
    # 显示配置
    sort_order = Column(Integer, default=0, comment="显示顺序")
    is_visible = Column(Boolean, default=True, comment="是否显示")
    help_text = Column(Text, comment="帮助文本")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    theme = relationship("WritingTheme", back_populates="fields")


class PromptTemplate(Base):
    """提示词模板模型"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    theme_id = Column(Integer, ForeignKey("writing_themes.id"), nullable=False)
    
    # 模板基本信息
    template_name = Column(String(100), nullable=False, comment="模板名称")
    template_type = Column(String(20), nullable=False, default="main", comment="模板类型")
    
    # 提示词内容
    system_prompt = Column(Text, comment="系统提示词")
    user_prompt_template = Column(Text, nullable=False, comment="用户提示词模板")
    
    # 模板配置
    variables = Column(JSON, comment="模板变量配置")
    ai_model = Column(String(50), comment="推荐AI模型")
    temperature = Column(String(10), comment="温度参数")
    max_tokens = Column(Integer, comment="最大令牌数")
    
    # 状态和版本
    is_active = Column(Boolean, default=True, comment="是否启用")
    version = Column(String(20), default="1.0", comment="模板版本")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_rate = Column(String(10), comment="成功率")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    theme = relationship("WritingTheme", back_populates="prompt_templates")


class ThemeCategory(Base):
    """主题分类模型"""
    __tablename__ = "theme_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(50), comment="分类图标")
    color = Column(String(20), comment="分类颜色")
    
    # 状态和排序
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WritingHistory(Base):
    """写作历史记录模型"""
    __tablename__ = "writing_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    theme_id = Column(Integer, ForeignKey("writing_themes.id"), nullable=False)
    
    # 写作内容
    input_data = Column(JSON, comment="输入数据")
    generated_content = Column(Text, comment="生成的内容")
    final_content = Column(Text, comment="最终内容")
    
    # 质量评估
    quality_score = Column(String(10), comment="质量评分")
    user_rating = Column(Integer, comment="用户评分")
    feedback = Column(Text, comment="用户反馈")
    
    # 生成信息
    generation_time = Column(Integer, comment="生成耗时(秒)")
    token_usage = Column(Integer, comment="令牌使用量")
    model_used = Column(String(50), comment="使用的模型")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
