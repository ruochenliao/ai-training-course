"""
API v1 路由汇总
"""

from app.api.v1.endpoints import (
    auth,
    users,
    knowledge_bases,
    documents,
    conversations,
    chat,
    search,
    admin,
    system,
    advanced_search,
    intelligent_qa,
    vlm,
    analytics,
    user_behavior,
    cache_management,
    system_management,
)
from fastapi import APIRouter

api_router = APIRouter()

# 认证相关
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户管理
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# 知识库管理
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["知识库管理"])

# 文档管理
api_router.include_router(documents.router, prefix="/documents", tags=["文档管理"])

# 对话管理
api_router.include_router(conversations.router, prefix="/conversations", tags=["对话管理"])

# 聊天接口
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])

# 搜索接口
api_router.include_router(search.router, prefix="/search", tags=["搜索"])

# 系统管理
api_router.include_router(admin.router, prefix="/admin", tags=["系统管理"])

# 系统接口
api_router.include_router(system.router, prefix="/system", tags=["系统"])

# 高级搜索接口
api_router.include_router(advanced_search.router, prefix="/advanced-search", tags=["高级搜索"])

# 智能问答接口
api_router.include_router(intelligent_qa.router, prefix="/qa", tags=["智能问答"])

# VLM多模态接口
api_router.include_router(vlm.router, prefix="/vlm", tags=["多模态"])

# 数据分析接口
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])

# 用户行为分析接口
api_router.include_router(user_behavior.router, prefix="/user-behavior", tags=["用户行为"])

# 缓存管理接口
api_router.include_router(cache_management.router, prefix="/cache", tags=["缓存管理"])

# 系统管理接口
api_router.include_router(system_management.router, prefix="/system-management", tags=["系统管理"])


@api_router.get("/")
async def api_info():
    """API信息"""
    return {
        "name": "企业级Agent+RAG知识库系统 API",
        "version": "1.0.0",
        "description": "基于多智能体协作的企业级知识库系统API",
        "endpoints": {
            "auth": "认证相关接口",
            "users": "用户管理接口",
            "knowledge-bases": "知识库管理接口",
            "documents": "文档管理接口",
            "conversations": "对话管理接口",
            "chat": "聊天接口",
            "search": "搜索接口",
            "admin": "系统管理接口",
            "system": "系统接口",
            "advanced-search": "高级搜索接口",
            "qa": "智能问答接口",
            "vlm": "多模态接口",
            "analytics": "数据分析接口",
            "user-behavior": "用户行为分析接口",
            "cache": "缓存管理接口",
            "system": "系统管理接口",
        }
    }
