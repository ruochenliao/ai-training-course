import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.expressions import Q

from .exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware
from ..api import api_router
from ..controllers.api import api_controller
from ..controllers.user import UserCreate, user_controller
from ..log import logger
from ..models.admin import Api, Menu, Role, Model
from ..schemas.menus import MenuType
from ..settings.config import settings


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        # 创建UserCreate对象
        user_create = UserCreate(
            username="admin",
            email="admin@admin.com",
            password="123456",
            is_active=True,
            is_superuser=True,
        )
        await user_controller.create_user(user_create)


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="模型管理",
                path="model",
                order=6,
                parent_id=parent_menu.id,
                icon="material-symbols:model-training",
                is_hidden=False,
                component="/system/model",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=7,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)

        # 创建知识库管理菜单
        knowledge_parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="知识库管理",
            path="/knowledge",
            order=2,
            parent_id=0,
            icon="material-symbols:library-books-outline",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/knowledge/base",
        )

        knowledge_menus = [
            Menu(
                menu_type=MenuType.MENU,
                name="知识库",
                path="base",
                order=1,
                parent_id=knowledge_parent.id,
                icon="material-symbols:database-outline",
                is_hidden=False,
                component="/knowledge",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(knowledge_menus)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=3,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    # 初始化Tortoise ORM连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_models():
    """初始化模型数据"""
    models = await Model.exists()
    if not models:
        # 创建deepseek模型
        await Model.create(
            category="对话模型",
            model_name="deepseek-chat",
            model_describe="Deepseek Chat 模型，专业的对话AI助手",
            model_price=0.001,
            model_type="chat",
            model_show="Deepseek Chat",
            system_prompt="你是超级智能客服，专业、友好、乐于助人。请用中文回复用户的问题。",
            api_host="https://api.deepseek.com/v1",
            api_key="sk-56f5743d59364543a00109a4c1c10a56",
            is_active=True,
            remark="默认对话模型"
        )

        # 创建其他示例模型
        await Model.create(
            category="对话模型",
            model_name="gpt-3.5-turbo",
            model_describe="OpenAI GPT-3.5 Turbo 模型，适用于对话和文本生成",
            model_price=0.002,
            model_type="chat",
            model_show="GPT-3.5",
            system_prompt="你是一个有用的AI助手。",
            api_host="https://api.openai.com",
            api_key="",
            is_active=False,
            remark="OpenAI对话模型"
        )


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_models()
