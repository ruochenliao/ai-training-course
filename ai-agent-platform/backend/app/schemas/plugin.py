# Copyright (c) 2025 左岚. All rights reserved.
"""
插件相关的Pydantic模式
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PluginBase(BaseModel):
    """插件基础模式"""
    name: str = Field(..., description="插件名称")
    version: str = Field(..., description="插件版本")
    description: Optional[str] = Field(None, description="插件描述")
    author: Optional[str] = Field(None, description="插件作者")
    type: str = Field(..., description="插件类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="插件配置")
    dependencies: List[str] = Field(default_factory=list, description="依赖列表")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class PluginCreate(PluginBase):
    """创建插件模式"""
    pass


class PluginUpdate(BaseModel):
    """更新插件模式"""
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class PluginResponse(PluginBase):
    """插件响应模式"""
    id: int
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    install_count: int = 0
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PluginExecuteRequest(BaseModel):
    """插件执行请求"""
    action: str = Field(..., description="执行动作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")


class PluginExecuteResponse(BaseModel):
    """插件执行响应"""
    id: int
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PluginInstallRequest(BaseModel):
    """插件安装请求"""
    source: str = Field(..., description="安装源：file/url/marketplace")
    url: Optional[str] = Field(None, description="下载URL")
    marketplace_id: Optional[str] = Field(None, description="市场插件ID")
    auto_activate: bool = Field(True, description="是否自动激活")
    overwrite: bool = Field(False, description="是否覆盖已存在的插件")


class PluginMarketplaceResponse(BaseModel):
    """插件市场响应"""
    id: int
    plugin_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    download_url: Optional[str] = None
    homepage_url: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    download_count: int = 0
    rating: int = 0
    rating_count: int = 0
    is_verified: bool = False
    is_featured: bool = False
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PluginStatsResponse(BaseModel):
    """插件统计响应"""
    total_plugins: int
    active_plugins: int
    inactive_plugins: int
    total_executions: int
    total_downloads: int
    popular_plugins: List[Dict[str, Any]]
    recent_executions: List[Dict[str, Any]]


class PluginValidationResult(BaseModel):
    """插件验证结果"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PluginSearchRequest(BaseModel):
    """插件搜索请求"""
    keyword: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class PluginSearchResponse(BaseModel):
    """插件搜索响应"""
    items: List[PluginResponse]
    total: int
    skip: int
    limit: int
