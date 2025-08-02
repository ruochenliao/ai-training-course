"""
API v1 路由模块
"""

from fastapi import APIRouter

from app.api.v1 import health, auth, users, conversations, agents, knowledge, files

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
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
# api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
