from fastapi import APIRouter

from .apis import apis_router
from .auditlog import auditlog_router
from .auth import auth_router
from .base import base_router
from .chat import chat_router
from .depts import depts_router
from .knowledge import knowledge_router
from .menus import menus_router
from .resource import resource_router
from .roles import roles_router
from .system import system_router
from .users import users_router
from ...core.dependency import DependPermission

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(auth_router, prefix="/auth")
v1_router.include_router(chat_router, prefix="/chat")
v1_router.include_router(knowledge_router, prefix="/knowledge")
v1_router.include_router(resource_router, prefix="/resource")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(system_router, prefix="/system")
