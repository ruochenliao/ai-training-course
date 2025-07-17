"""
智能体配置相关Schema
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# 智能体工具Schema
class AgentToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    function_name: str
    parameters_schema: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AgentToolCreate(AgentToolBase):
    pass


class AgentToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    function_name: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentTool(AgentToolBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 智能体模型Schema
class AgentModelBase(BaseModel):
    name: str
    display_name: str
    provider: str
    api_base: Optional[str] = None
    max_tokens: int = 4000
    supports_tools: bool = True
    is_active: bool = True


class AgentModelCreate(AgentModelBase):
    pass


class AgentModelUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    provider: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_tools: Optional[bool] = None
    is_active: Optional[bool] = None


class AgentModel(AgentModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 智能体配置Schema
class AgentConfigBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    model_name: str = "gpt-4o-mini"
    temperature: str = "0.7"
    max_tokens: int = 2000
    tools: List[str] = []
    tool_choice: str = "auto"
    max_consecutive_auto_reply: int = 3
    human_input_mode: str = "NEVER"
    code_execution_config: Dict[str, Any] = {}
    is_active: bool = True


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    tool_choice: Optional[str] = None
    max_consecutive_auto_reply: Optional[int] = None
    human_input_mode: Optional[str] = None
    code_execution_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentConfig(AgentConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 写作字段配置Schema（更新版）
class WritingFieldConfigBase(BaseModel):
    field_name: str
    field_key: str
    field_type: str = "text"
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    required: bool = False
    ai_enabled: bool = False
    doc_enabled: bool = False
    sort_order: int = 0
    agent_config_id: Optional[int] = None
    is_active: bool = True


class WritingFieldConfigCreate(WritingFieldConfigBase):
    scenario_config_id: int


class WritingFieldConfigUpdate(BaseModel):
    field_name: Optional[str] = None
    field_key: Optional[str] = None
    field_type: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    required: Optional[bool] = None
    ai_enabled: Optional[bool] = None
    doc_enabled: Optional[bool] = None
    sort_order: Optional[int] = None
    agent_config_id: Optional[int] = None
    is_active: Optional[bool] = None


class WritingFieldConfig(WritingFieldConfigBase):
    id: int
    scenario_config_id: int
    agent_config: Optional[AgentConfig] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AI生成请求Schema
class AIGenerateRequest(BaseModel):
    field_key: str
    field_name: str
    context: Dict[str, Any] = {}
    user_input: Optional[str] = None
    template_type_id: int


class AIGenerateDirectRequest(BaseModel):
    user_prompt: str
    context: Dict[str, Any] = {}


class AIGenerateResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
