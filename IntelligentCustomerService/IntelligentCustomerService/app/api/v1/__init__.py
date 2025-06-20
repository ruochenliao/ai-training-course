from fastapi import APIRouter

from app.core.dependency import DependPermission
from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .chat import chats_router
from .depts import depts_router
from .knowledge import knowledge_router
from .menus import menus_router
from .models import models_router
from .roles import roles_router
from .users import users_router
# 新增智能体相关路由
from .agents import agents_router
from .tools import tools_router
from .mcp import mcp_router
from .knowledge_graph import knowledge_graph_router
from .monitoring import monitoring_router
# 新增高级功能路由
from .voice import voice_router
from .image_generation import image_generation_router
from .collaboration import collaboration_router
from .analytics import analytics_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(chats_router, prefix="/chat")
v1_router.include_router(knowledge_router, prefix="/knowledge")
v1_router.include_router(models_router, prefix="/models")
# 新增智能体相关路由
v1_router.include_router(agents_router, prefix="/agents")
v1_router.include_router(tools_router, prefix="/tools")
v1_router.include_router(mcp_router, prefix="/mcp")
v1_router.include_router(knowledge_graph_router, prefix="/knowledge-graph")
v1_router.include_router(monitoring_router, prefix="/monitoring")
# 新增高级功能路由
v1_router.include_router(voice_router, prefix="/voice")
v1_router.include_router(image_generation_router, prefix="/image-generation")
v1_router.include_router(collaboration_router, prefix="/collaboration")
v1_router.include_router(analytics_router, prefix="/analytics")
