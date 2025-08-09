"""
# Copyright (c) 2025 左岚. All rights reserved.

模板相关的Pydantic模型
"""

# # Standard library imports
from enum import Enum
from typing import List, Optional

# # Third-party imports
from pydantic import BaseModel, Field


class TemplateCategory(str, Enum):
    """模板分类"""
    GENERAL = "general"
    PROGRAMMING = "programming"
    CREATIVE = "creative"
    BUSINESS = "business"
    EDUCATION = "education"
    LANGUAGE = "language"


class AgentTemplateResponse(BaseModel):
    """智能体模板响应"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    avatar_url: str = Field(..., description="头像URL")
    prompt_template: str = Field(..., description="提示词模板")
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(..., description="温度参数")
    max_tokens: int = Field(..., description="最大Token数")
    tags: List[str] = Field(..., description="标签列表")
    usage_count: Optional[int] = Field(None, description="使用次数")
    rating: Optional[float] = Field(None, description="评分")


class TemplateCategoryResponse(BaseModel):
    """模板分类响应"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    description: str = Field(..., description="分类描述")


class CreateAgentFromTemplateRequest(BaseModel):
    """从模板创建智能体请求"""
    name: Optional[str] = Field(None, description="智能体名称，如果为空则使用模板名称")
    description: Optional[str] = Field(None, description="智能体描述，如果为空则使用模板描述")
    is_public: Optional[bool] = Field(False, description="是否公开")


class CreateAgentFromTemplateResponse(BaseModel):
    """从模板创建智能体响应"""
    message: str = Field(..., description="创建结果消息")
    agent_id: int = Field(..., description="创建的智能体ID")
    agent_name: str = Field(..., description="智能体名称")
    template_id: str = Field(..., description="使用的模板ID")


class TrendingTemplateResponse(AgentTemplateResponse):
    """热门模板响应"""
    usage_count: int = Field(..., description="使用次数")
    rating: float = Field(..., description="评分")


class TemplateSearchRequest(BaseModel):
    """模板搜索请求"""
    category: Optional[str] = Field(None, description="分类筛选")
    search: Optional[str] = Field(None, description="搜索关键词")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    limit: Optional[int] = Field(20, ge=1, le=100, description="返回数量限制")
