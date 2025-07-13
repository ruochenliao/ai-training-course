from contextlib import asynccontextmanager

from fastapi import FastAPI
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
    return app


app = create_app()
