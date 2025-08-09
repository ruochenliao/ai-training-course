"""
# Copyright (c) 2025 左岚. All rights reserved.

API v1 路由模块
"""

# # Third-party imports
from fastapi import APIRouter

# # Local application imports
from app.api.v1 import (
    admin,
    agents,
    auth,
    chat,
    conversations,
    files,
    health,
    knowledge,
    monitoring,
    plugins,
    sse_api,
    system,
    templates,
    users,
    workflow,
)

# 创建API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证授权"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# 添加其他模块路由
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(knowledge.router, prefix="/knowledge-bases", tags=["知识库"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["对话"])
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])
api_router.include_router(templates.router, prefix="/templates", tags=["智能体模板"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["工作流管理"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["插件管理"])
api_router.include_router(sse_api.router, prefix="/sse", tags=["SSE实时通信"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监控管理"])
