import shutil  # 用于删除目录

from aerich import Command  # 数据库迁移工具
from fastapi import FastAPI  # FastAPI 框架
from fastapi.middleware import Middleware  # 中间件定义
from fastapi.middleware.cors import CORSMiddleware  # CORS 中间件
from tortoise.expressions import Q  # Tortoise ORM 查询条件构造工具
from fastapi.staticfiles import StaticFiles  # 静态文件服务

# 导入模块
from a_app.api import api_router  # API 路由
from a_app.controllers.api import api_controller  # API 控制器
from a_app.controllers.user import UserCreate, user_controller  # 用户控制器
from a_app.core.exceptions import (  # 异常处理相关
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
from a_app.log import logger  # 日志记录器
from a_app.models.admin import Api, Menu, Role  # 数据模型
from a_app.schemas.menus import MenuType  # 菜单类型枚举
from a_app.settings.config import settings  # 配置文件
from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware  # 自定义中间件


def make_middlewares():
    """
    创建中间件列表。
    返回:
        list[Middleware]: 中间件列表
    """
    middleware = [
        Middleware(
            CORSMiddleware,  # 添加 CORS 中间件
            allow_origins=settings.CORS_ORIGINS,  # 允许的来源
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,  # 是否允许凭据
            allow_methods=settings.CORS_ALLOW_METHODS,  # 允许的方法
            allow_headers=settings.CORS_ALLOW_HEADERS,  # 允许的头部
        ),
        # 添加安全头部中间件，允许在iframe中加载内容
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 允许所有来源访问静态资源
            allow_methods=["GET"],
            allow_headers=["*"],
            expose_headers=["Content-Disposition"],
            max_age=600
        ),
        Middleware(BackGroundTaskMiddleware),  # 后台任务中间件
        Middleware(
            HttpAuditLogMiddleware,  # HTTP 审计日志中间件
            methods=["GET", "POST", "PUT", "DELETE"],  # 需要记录的日志方法
            exclude_paths=[
                "/docs",
                "/openapi.json",
            ],  # 排除路径
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    """
    注册异常处理器。
    参数:
        app (FastAPI): FastAPI 应用实例
    """
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)  # 对象不存在异常
    app.add_exception_handler(HTTPException, HttpExcHandle)  # HTTP 异常
    app.add_exception_handler(IntegrityError, IntegrityHandle)  # 数据完整性异常
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)  # 请求验证错误
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)  # 响应验证错误


def register_routers(app: FastAPI, prefix: str = "/api"):
    """
    注册路由。
    参数:
        app (FastAPI): FastAPI 应用实例
        prefix (str): 路由前缀，默认为 /api
    """
    # 注册静态文件服务
    try:
        # 确保静态文件目录存在
        import os
        static_dir = os.path.join(os.getcwd(), "static")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        # 挂载静态文件目录
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"静态文件服务已挂载: {static_dir}")
    except Exception as e:
        print(f"挂载静态文件服务失败: {str(e)}")

    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    """
    初始化超级用户。
    如果数据库中没有用户，则创建一个默认的超级用户。
    """
    user = await user_controller.model.exists()  # 检查是否存在用户
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",  # 默认用户名
                email="admin@admin.com",  # 默认邮箱
                password="123456",  # 默认密码
                is_active=True,  # 用户激活状态
                is_superuser=True,  # 超级用户
            )
        )


async def init_menus():
    """
    初始化菜单。
    如果数据库中没有菜单，则创建默认的系统管理菜单及其子菜单。
    """
    menus = await Menu.exists()  # 检查是否存在菜单
    if not menus:
        parent_menu = await Menu.create(  # 创建父菜单（系统管理）
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
        children_menu = [  # 创建子菜单
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
            # 其他子菜单...
        ]
        await Menu.bulk_create(children_menu)  # 批量创建子菜单
        await Menu.create(  # 创建一级菜单
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )


async def init_apis():
    """
    初始化 API。
    如果数据库中没有 API，则刷新 API 列表。
    """
    apis = await api_controller.model.exists()  # 检查是否存在 API
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    """
    初始化数据库。
    包括创建数据库表结构、执行迁移和升级。
    """
    command = Command(tortoise_config=settings.TORTOISE_ORM)  # 创建 Aerich 命令对象
    try:
        await command.init_db(safe=True)  # 初始化数据库
    except FileExistsError:
        pass

    await command.init()  # 初始化 Aerich
    try:
        await command.migrate()  # 执行迁移
    except AttributeError:
        logger.warning("无法从数据库中检索模型历史记录，将从头开始创建模型历史记录")
        shutil.rmtree("migrations")  # 删除旧的迁移文件
        await command.init_db(safe=True)  # 重新初始化数据库

    await command.upgrade(run_in_transaction=True)  # 升级数据库


async def init_roles():
    """
    初始化角色。
    如果数据库中没有角色，则创建管理员和普通用户角色，并分配权限。
    """
    roles = await Role.exists()  # 检查是否存在角色
    if not roles:
        admin_role = await Role.create(  # 创建管理员角色
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(  # 创建普通用户角色
            name="普通用户",
            desc="普通用户角色",
        )

        all_apis = await Api.all()  # 获取所有 API
        await admin_role.apis.add(*all_apis)  # 为管理员角色分配所有 API

        all_menus = await Menu.all()  # 获取所有菜单
        await admin_role.menus.add(*all_menus)  # 为管理员角色分配所有菜单
        await user_role.menus.add(*all_menus)  # 为普通用户角色分配所有菜单

        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))  # 获取基础 API
        await user_role.apis.add(*basic_apis)  # 为普通用户角色分配基础 API


async def init_data():
    """
    初始化数据。
    包括数据库初始化、超级用户创建、菜单配置、API 配置和角色权限分配。
    """
    await init_db()  # 初始化数据库
    await init_superuser()  # 初始化超级用户
    await init_menus()  # 初始化菜单
    await init_apis()  # 初始化 API
    await init_roles()  # 初始化角色