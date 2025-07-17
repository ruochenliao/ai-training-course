"""
智能体配置模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class AgentConfig(Base):
    """智能体配置"""
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="智能体名称")
    description = Column(Text, comment="智能体描述")
    
    # 智能体配置
    system_prompt = Column(Text, nullable=False, comment="系统提示词")
    user_prompt_template = Column(Text, comment="用户提示词模板")
    model_name = Column(String(100), default="gpt-4o-mini", comment="使用的大模型")
    temperature = Column(String(10), default="0.7", comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大token数")
    
    # 工具配置
    tools = Column(JSON, default=list, comment="可用工具列表")
    tool_choice = Column(String(50), default="auto", comment="工具选择策略")
    
    # 高级配置
    max_consecutive_auto_reply = Column(Integer, default=3, comment="最大连续自动回复次数")
    human_input_mode = Column(String(20), default="NEVER", comment="人工输入模式")
    code_execution_config = Column(JSON, default=dict, comment="代码执行配置")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联字段配置
    field_configs = relationship("WritingFieldConfig", back_populates="agent_config")


class AgentTool(Base):
    """智能体工具"""
    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="工具名称")
    description = Column(Text, comment="工具描述")
    function_name = Column(String(100), nullable=False, comment="函数名称")
    parameters_schema = Column(JSON, comment="参数schema")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentModel(Base):
    """可用的大模型配置"""
    __tablename__ = "agent_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    provider = Column(String(50), nullable=False, comment="提供商")
    api_base = Column(String(200), comment="API基础URL")
    max_tokens = Column(Integer, default=4000, comment="最大token数")
    supports_tools = Column(Boolean, default=True, comment="是否支持工具调用")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
