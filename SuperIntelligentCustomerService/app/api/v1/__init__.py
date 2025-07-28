from fastapi import APIRouter

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .customer import customer_router
from .depts import depts_router
from .knowledge import knowledge_router
from .llm_models import llm_models_router
from .mcp import mcp_api_router
from .memory import memory_router
from .menus import menus_router
from .roles import roles_router
from .sessions import sessions_router
from .users import users_router
from ...core.dependency import DependPermission

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(customer_router, prefix="/customer", dependencies=[DependPermission])
v1_router.include_router(sessions_router, prefix="/customer/sessions", dependencies=[DependPermission])
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(llm_models_router, prefix="/llm", dependencies=[DependPermission])
v1_router.include_router(knowledge_router, prefix="/knowledge", dependencies=[DependPermission])
v1_router.include_router(memory_router, prefix="/memory", dependencies=[DependPermission])
v1_router.include_router(mcp_api_router, prefix="/mcp", dependencies=[DependPermission])
