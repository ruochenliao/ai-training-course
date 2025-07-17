from app.data.init_data import init_shop_data
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from tortoise import Tortoise

from app.settings.config import settings

# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_data():
    """初始化数据库和数据"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await init_shop_data()


def register_exceptions(app: FastAPI):
    """注册异常处理器"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail, "status_code": exc.status_code}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error", "status_code": 500}
        )


def register_routers(app: FastAPI, prefix: str = ""):
    """注册路由"""
    from app.api.v1 import api_router

    # 注册 API 路由
    app.include_router(api_router, prefix=f"{prefix}/v1")
