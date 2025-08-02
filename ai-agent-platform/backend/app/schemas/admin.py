"""
管理员相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserStats(BaseModel):
    """用户统计"""
    total: int = Field(..., description="总用户数")
    active: int = Field(..., description="活跃用户数")
    new_today: int = Field(..., description="今日新增用户数")


class AgentStats(BaseModel):
    """智能体统计"""
    total: int = Field(..., description="总智能体数")
    public: int = Field(..., description="公开智能体数")
    active: int = Field(..., description="活跃智能体数")


class KnowledgeStats(BaseModel):
    """知识库统计"""
    total_knowledge_bases: int = Field(..., description="总知识库数")
    total_documents: int = Field(..., description="总文档数")


class ConversationTrend(BaseModel):
    """对话趋势"""
    date: str = Field(..., description="日期")
    count: int = Field(..., description="对话数量")


class ConversationStats(BaseModel):
    """对话统计"""
    total: int = Field(..., description="总对话数")
    total_messages: int = Field(..., description="总消息数")
    today: int = Field(..., description="今日对话数")
    trend: List[ConversationTrend] = Field(..., description="7天趋势")


class AdminStatsResponse(BaseModel):
    """管理员统计响应"""
    user_stats: UserStats
    agent_stats: AgentStats
    knowledge_stats: KnowledgeStats
    conversation_stats: ConversationStats


class UserManagementResponse(BaseModel):
    """用户管理响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(..., description="是否活跃")
    is_superuser: bool = Field(..., description="是否超级用户")
    created_at: str = Field(..., description="创建时间")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    agent_count: int = Field(..., description="智能体数量")
    knowledge_base_count: int = Field(..., description="知识库数量")
    conversation_count: int = Field(..., description="对话数量")


class ComponentHealth(BaseModel):
    """组件健康状态"""
    status: str = Field(..., description="状态: healthy, warning, error")
    message: str = Field(..., description="状态消息")


class DiskHealth(ComponentHealth):
    """磁盘健康状态"""
    free_gb: float = Field(..., description="可用空间(GB)")
    total_gb: float = Field(..., description="总空间(GB)")
    usage_percent: float = Field(..., description="使用率(%)")


class MemoryHealth(ComponentHealth):
    """内存健康状态"""
    usage_percent: float = Field(..., description="使用率(%)")


class SystemHealthResponse(BaseModel):
    """系统健康状态响应"""
    overall_status: str = Field(..., description="整体状态")
    timestamp: str = Field(..., description="检查时间")
    components: Dict[str, Any] = Field(..., description="组件状态")


class CleanupRequest(BaseModel):
    """清理请求"""
    days: int = Field(30, ge=1, le=365, description="清理多少天前的数据")


class CleanupResponse(BaseModel):
    """清理响应"""
    message: str = Field(..., description="清理结果消息")
    cutoff_date: str = Field(..., description="截止日期")
    days: int = Field(..., description="清理天数")


class UserStatusUpdate(BaseModel):
    """用户状态更新"""
    is_active: bool = Field(..., description="是否激活")
