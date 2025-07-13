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
# BGE模型会在首次使用时自动下载，无需单独初始化
from ..api import api_router
from ..controllers.api import api_controller
from ..controllers.user import UserCreate, user_controller
from ..models.admin import Api, Menu, Role, Model, Dept
from ..schemas.menus import MenuType
from ..settings.config import settings
from ..utils.encryption import encrypt_api_key


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
        # 创建智能客服一级菜单
        ai_service_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="智能客服",
            path="/ai-service",
            order=1,
            parent_id=0,
            icon="material-symbols:smart-toy-outline",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/ai-service/model",
        )

        # 智能客服子菜单
        ai_service_children = [
            Menu(
                menu_type=MenuType.MENU,
                name="模型管理",
                path="model",
                order=1,
                parent_id=ai_service_menu.id,
                icon="material-symbols:model-training",
                is_hidden=False,
                component="/ai-service/model",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="知识库管理",
                path="knowledge",
                order=2,
                parent_id=ai_service_menu.id,
                icon="material-symbols:library-books-outline",
                is_hidden=False,
                component="/ai-service/knowledge",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(ai_service_children)

        # 创建系统管理菜单
        system_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=2,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )

        # 系统管理子菜单
        system_children = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=system_menu.id,
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
                parent_id=system_menu.id,
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
                parent_id=system_menu.id,
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
                parent_id=system_menu.id,
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
                parent_id=system_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=system_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(system_children)

        # 创建一级菜单示例
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
        # 创建DeepSeek文本模型
        await Model.create(
            category="对话模型",
            model_name="deepseek-chat",
            model_describe="DeepSeek Chat模型，专业的对话AI助手，支持中文优化",
            model_price=0.001,
            model_type="chat",
            model_show="DeepSeek Chat",
            system_prompt="""你是超级智能客服，专业、友好、乐于助人。请用中文回复用户的问题。

## 重要格式要求：
**必须使用标准 Markdown 格式**输出所有回复，特别注意：

1. **代码块格式**：
```语言名称
代码内容（必须有正确的换行符和缩进）
```

2. **确保代码块内容格式化良好**：
   - 每行代码独立成行
   - 保持正确的缩进
   - 包含适当的注释
   - 不要将所有代码挤在一行

3. **使用适当的 Markdown 语法**：
   - 标题：# ## ###
   - 列表：- 或 1.
   - 强调：**粗体** *斜体*
   - 行内代码：`代码`

确保所有代码示例都格式化良好。""",
            api_host="https://api.deepseek.com/v1",
            api_key=encrypt_api_key("sk-56f5743d59364543a00109a4c1c10a56"),
            is_active=True,
            remark="DeepSeek文本模型"
        )

        # 创建DeepSeek多模态模型
        await Model.create(
            category="多模态模型",
            model_name="deepseek-vl-chat",
            model_describe="DeepSeek VL Chat模型，支持图像理解和多模态对话",
            model_price=0.002,
            model_type="multimodal",
            model_show="DeepSeek VL Chat",
            system_prompt="""你是超级智能客服，专业、友好、乐于助人。你可以理解图像内容并用中文回复用户的问题。

## 重要格式要求：
**必须使用标准 Markdown 格式**输出所有回复，特别注意：

1. **代码块格式**：
```语言名称
代码内容（必须有正确的换行符和缩进）
```

2. **确保代码块内容格式化良好**：
   - 每行代码独立成行
   - 保持正确的缩进
   - 包含适当的注释
   - 不要将所有代码挤在一行

3. **使用适当的 Markdown 语法**：
   - 标题：# ## ###
   - 列表：- 或 1.
   - 强调：**粗体** *斜体*
   - 行内代码：`代码`

确保所有代码示例都格式化良好。""",
            api_host="https://api.deepseek.com/v1",
            api_key=encrypt_api_key("sk-56f5743d59364543a00109a4c1c10a56"),
            is_active=True,
            remark="DeepSeek多模态模型"
        )

        # 注意：DeepSeek Chat模型已在上面创建，避免重复


async def init_depts():
    """初始化部门数据"""
    depts = await Dept.exists()
    if not depts:
        # 创建总公司
        company = await Dept.create(
            name="超级智能客服公司",
            desc="公司总部",
            order=1,
            parent_id=0,
            is_deleted=False
        )

        # 创建一级部门
        tech_dept = await Dept.create(
            name="技术部",
            desc="负责技术研发和系统维护",
            order=1,
            parent_id=company.id,
            is_deleted=False
        )

        product_dept = await Dept.create(
            name="产品部",
            desc="负责产品设计和需求分析",
            order=2,
            parent_id=company.id,
            is_deleted=False
        )

        market_dept = await Dept.create(
            name="市场部",
            desc="负责市场推广和客户关系",
            order=3,
            parent_id=company.id,
            is_deleted=False
        )

        admin_dept = await Dept.create(
            name="行政部",
            desc="负责人事行政和财务管理",
            order=4,
            parent_id=company.id,
            is_deleted=False
        )

        # 创建技术部二级部门
        await Dept.create(
            name="前端开发组",
            desc="负责前端界面开发",
            order=1,
            parent_id=tech_dept.id,
            is_deleted=False
        )

        await Dept.create(
            name="后端开发组",
            desc="负责后端服务开发",
            order=2,
            parent_id=tech_dept.id,
            is_deleted=False
        )

        await Dept.create(
            name="AI算法组",
            desc="负责AI模型研发和优化",
            order=3,
            parent_id=tech_dept.id,
            is_deleted=False
        )

        await Dept.create(
            name="测试组",
            desc="负责软件测试和质量保证",
            order=4,
            parent_id=tech_dept.id,
            is_deleted=False
        )

        # 创建产品部二级部门
        await Dept.create(
            name="产品设计组",
            desc="负责产品原型设计",
            order=1,
            parent_id=product_dept.id,
            is_deleted=False
        )

        await Dept.create(
            name="用户体验组",
            desc="负责用户体验研究和优化",
            order=2,
            parent_id=product_dept.id,
            is_deleted=False
        )

        # 创建市场部二级部门
        await Dept.create(
            name="销售组",
            desc="负责客户开发和销售",
            order=1,
            parent_id=market_dept.id,
            is_deleted=False
        )

        await Dept.create(
            name="客服组",
            desc="负责客户服务和技术支持",
            order=2,
            parent_id=market_dept.id,
            is_deleted=False
        )


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_models()
    await init_depts()
    # BGE模型会在首次使用时自动下载，无需单独初始化
