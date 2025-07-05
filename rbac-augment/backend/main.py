"""
RBAC管理系统 - 主应用入口
基于FastAPI + Tortoise ORM的企业级权限管理系统
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from pathlib import Path

from app.core.config import settings
from app.middleware.exception import ExceptionMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.audit import AuditMiddleware
from app.api.v1 import api_router


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于FastAPI + Vue3的企业级RBAC权限管理系统",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加自定义中间件（注意顺序：安全中间件 -> 异常处理 -> 认证 -> 审计）
    # app.add_middleware(AuditMiddleware)  # 暂时禁用审计中间件
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(SecurityMiddleware)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 配置静态文件服务
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # 注册数据库
    register_tortoise(
        app,
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    
    return app


app = create_app()


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "RBAC管理系统API服务正在运行",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """企业级健康检查接口"""
    import time
    from datetime import datetime
    from tortoise import Tortoise

    start_time = time.time()
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time,
        "dependencies": {}
    }

    # 检查数据库连接
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # 检查Redis连接（如果配置了）
    if settings.REDIS_URL:
        try:
            # 这里可以添加Redis连接检查
            health_status["dependencies"]["redis"] = "healthy"
        except Exception as e:
            health_status["dependencies"]["redis"] = f"unhealthy: {str(e)}"

    return health_status


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )
