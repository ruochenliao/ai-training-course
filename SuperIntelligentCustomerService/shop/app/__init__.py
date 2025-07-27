from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from tortoise import Tortoise

from app.core.init_app import init_data, register_exceptions, register_routers
from app.core.mcp_config import setup_mcp_server
from app.settings.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_data()
    yield
    await Tortoise.close_connections()


def create_shop_app() -> FastAPI:
    """创建 Shop 应用"""
    app = FastAPI(
        title="智能电商系统",
        description="基于 FastAPI 构建的现代电商平台，专为智能客服场景设计",
        version="1.0.0",
        openapi_url="/shop/openapi.json",
        docs_url="/shop/docs",
        redoc_url="/shop/redoc",
        lifespan=lifespan,
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

    # 注册异常处理器
    register_exceptions(app)
    
    # 注册路由
    register_routers(app, prefix="/shop/api")

    # 设置MCP服务器（如果启用）
    if getattr(settings, 'MCP_ENABLED', True):
        mcp = setup_mcp_server(app)
        print(f"✅ MCP服务器已启用，访问地址: http://{settings.HOST}:{settings.PORT}{settings.MCP_MOUNT_PATH}")

    return app


app = create_shop_app()
