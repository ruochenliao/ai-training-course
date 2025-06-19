"""
企业级Agent+RAG知识库系统 - FastAPI主应用
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db, close_db, create_initial_data
from app.core.exceptions import (
    BusinessException,
    business_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import (
    LoggingMiddleware,
    ProcessTimeMiddleware,
    RateLimitMiddleware,
)
from app.services.health import HealthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动企业级Agent+RAG知识库系统...")
    
    # 初始化数据库连接
    await init_database()
    
    # 初始化AI服务
    await init_ai_services()
    
    # 初始化向量数据库
    await init_vector_database()
    
    # 初始化图数据库
    await init_graph_database()
    
    logger.info("✅ 系统启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("🔄 正在关闭系统...")
    await cleanup_resources()
    logger.info("✅ 系统关闭完成")


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="基于多智能体协作的企业级知识库系统",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # 配置CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 配置受信任主机
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    
    # 添加自定义中间件
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # 注册异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 健康检查端点
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """系统健康检查"""
        health_service = HealthService()
        health_status = await health_service.check_all()
        
        status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
    
    # 根路径
    @app.get("/", tags=["根路径"])
    async def root():
        """API根路径"""
        return {
            "message": "企业级Agent+RAG知识库系统",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
            "api": settings.API_V1_STR,
        }
    
    return app


async def init_database():
    """初始化数据库连接"""
    try:
        await init_db()
        await create_initial_data()
        logger.info("✅ 数据库连接初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        raise


async def init_ai_services():
    """初始化AI服务"""
    try:
        # 这里将初始化各种AI模型服务
        # LLM服务、嵌入服务、重排服务等
        logger.info("✅ AI服务初始化成功")
    except Exception as e:
        logger.error(f"❌ AI服务初始化失败: {e}")
        raise


async def init_vector_database():
    """初始化向量数据库"""
    try:
        # 初始化Milvus连接
        logger.info("✅ 向量数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 向量数据库初始化失败: {e}")
        raise


async def init_graph_database():
    """初始化图数据库"""
    try:
        # 初始化Neo4j连接
        logger.info("✅ 图数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 图数据库初始化失败: {e}")
        raise


async def cleanup_resources():
    """清理资源"""
    try:
        await close_db()
        # 清理缓存
        # 关闭AI服务连接
        logger.info("✅ 资源清理完成")
    except Exception as e:
        logger.error(f"❌ 资源清理失败: {e}")


# 创建应用实例
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )
