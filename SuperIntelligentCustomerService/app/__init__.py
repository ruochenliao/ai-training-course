import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise

from .core.exceptions import SettingNotFound
from .core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)

try:
    from .settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库和基础数据
    await init_data()

    # 在数据库初始化完成后，延迟初始化LLM客户端
    try:
        from .core.llms import initialize_llm_clients
        await initialize_llm_clients()
        print("✅ LLM客户端延迟初始化完成")
    except Exception as e:
        print(f"⚠️  LLM客户端延迟初始化失败: {e}")

    # 启动异步文件处理器
    from .controllers.async_file_processor import async_file_processor
    await async_file_processor.start()

    yield

    # 关闭异步文件处理器
    await async_file_processor.stop()

    # 关闭数据库连接
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")

    # 添加静态文件支持（用于测试前端页面）
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
