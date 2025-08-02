"""
智能体相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.agent import AgentType, AgentStatus


class AgentBase(BaseModel):
    """智能体基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=1000, description="智能体描述")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    type: AgentType = Field(default=AgentType.CHAT, description="智能体类型")


class AgentCreate(AgentBase):
    """创建智能体的请求模型"""
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="智能体配置")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    model_name: Optional[str] = Field(default="gpt-3.5-turbo", description="使用的模型名称")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=8000, description="最大token数")
    knowledge_base_ids: Optional[List[int]] = Field(default_factory=list, description="关联的知识库ID列表")
    is_public: Optional[bool] = Field(default=False, description="是否公开")


class AgentUpdate(BaseModel):
    """更新智能体的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="智能体名称")
    description: Optional[str] = Field(None, max_length=1000, description="智能体描述")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    config: Optional[Dict[str, Any]] = Field(None, description="智能体配置")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    model_name: Optional[str] = Field(None, description="使用的模型名称")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, le=8000, description="最大token数")
    knowledge_base_ids: Optional[List[int]] = Field(None, description="关联的知识库ID列表")
    is_public: Optional[bool] = Field(None, description="是否公开")
    status: Optional[AgentStatus] = Field(None, description="状态")


class AgentResponse(AgentBase):
    """智能体响应模型"""
    id: int
    status: AgentStatus
    config: Optional[Dict[str, Any]]
    prompt_template: Optional[str]
    model_name: Optional[str]
    temperature: str
    max_tokens: str
    owner_id: str
    knowledge_base_ids: Optional[List[int]]
    chat_count: str
    like_count: str
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentTemplateBase(BaseModel):
    """智能体模板基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class AgentTemplateCreate(AgentTemplateBase):
    """创建智能体模板的请求模型"""
    template_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板配置")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    sort_order: Optional[int] = Field(default=0, description="排序顺序")
    is_featured: Optional[bool] = Field(default=False, description="是否推荐")


class AgentTemplateUpdate(BaseModel):
    """更新智能体模板的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    template_config: Optional[Dict[str, Any]] = Field(None, description="模板配置")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_featured: Optional[bool] = Field(None, description="是否推荐")


class AgentTemplateResponse(AgentTemplateBase):
    """智能体模板响应模型"""
    id: int
    template_config: Optional[Dict[str, Any]]
    prompt_template: Optional[str]
    tags: Optional[List[str]]
    sort_order: str
    is_active: bool
    is_featured: bool
    use_count: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentStats(BaseModel):
    """智能体统计信息"""
    total_agents: int
    active_agents: int
    public_agents: int
    total_conversations: int
    total_messages: int


class AgentSearchRequest(BaseModel):
    """智能体搜索请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    type: Optional[AgentType] = Field(None, description="智能体类型")
    is_public: Optional[bool] = Field(None, description="是否公开")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    skip: int = Field(default=0, ge=0, description="跳过数量")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")


class AgentSearchResponse(BaseModel):
    """智能体搜索响应"""
    agents: List[AgentResponse]
    total: int
    skip: int
    limit: int
