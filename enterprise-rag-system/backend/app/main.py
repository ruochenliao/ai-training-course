"""
企业级Agent+RAG知识库系统 - FastAPI主应用
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import JSONResponse
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.api import api_router
from app.core import settings
from app.core import init_db, close_db, create_initial_data
from app.core import (
    BusinessException,
    business_exception_handler,
    general_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    tortoise_does_not_exist_handler,
    tortoise_integrity_error_handler,
)
from app.core import (
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

    # 添加数据库查询监控中间件
    from app.core.query_middleware import QueryMonitoringMiddleware
    app.add_middleware(
        QueryMonitoringMiddleware,
        enable_monitoring=settings.DEBUG,  # 开发环境启用
        log_slow_queries=True
    )

    # 添加增强的请求验证中间件
    from app.core.enhanced_validation_middleware import RequestValidationMiddleware
    app.add_middleware(
        RequestValidationMiddleware,
        enable_ip_filtering=True,
        enable_input_validation=True,
        enable_security_headers=True,
        enable_content_validation=True,
        max_request_size=10 * 1024 * 1024,  # 10MB
        rate_limit_per_ip=100  # 每分钟100个请求
    )
    
    # 注册异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # 添加Tortoise ORM异常处理器
    from tortoise.exceptions import DoesNotExist, IntegrityError
    app.add_exception_handler(DoesNotExist, tortoise_does_not_exist_handler)
    app.add_exception_handler(IntegrityError, tortoise_integrity_error_handler)

    # 通用异常处理器放在最后
    app.add_exception_handler(Exception, general_exception_handler)
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 自定义文档路由 - 修复空白页面问题，使用国内可访问的CDN
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.0/bundles/redoc.standalone.js",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

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

    # 应用启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info("🚀 应用启动中...")

        try:
            # 启动监控服务
            from app.services.monitoring_scheduler import start_monitoring
            await start_monitoring()
            logger.info("✅ 监控服务启动成功")
        except Exception as e:
            logger.error(f"❌ 监控服务启动失败: {e}")

        try:
            # 启动Redis缓存服务
            from app.core.redis_cache import get_redis_cache
            redis_cache = await get_redis_cache()
            logger.info("✅ Redis缓存服务启动成功")
        except Exception as e:
            logger.error(f"❌ Redis缓存服务启动失败: {e}")

        try:
            # 执行缓存预热
            from app.services.cache_service import get_business_cache
            cache_service = get_business_cache()
            await cache_service.warm_up_cache()
            logger.info("✅ 缓存预热完成")
        except Exception as e:
            logger.error(f"❌ 缓存预热失败: {e}")

        logger.info("🎉 应用启动完成")

    # 应用关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        logger.info("🛑 应用关闭中...")

        try:
            # 停止监控服务
            from app.services.monitoring_scheduler import stop_monitoring
            await stop_monitoring()
            logger.info("✅ 监控服务停止成功")
        except Exception as e:
            logger.error(f"❌ 监控服务停止失败: {e}")

        try:
            # 停止Redis缓存服务
            from app.core.redis_cache import redis_cache_manager
            await redis_cache_manager.disconnect()
            logger.info("✅ Redis缓存服务停止成功")
        except Exception as e:
            logger.error(f"❌ Redis缓存服务停止失败: {e}")

        # 清理其他资源
        await cleanup_resources()

        logger.info("👋 应用关闭完成")

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
        logger.info("✅ AI服务初始化成功")
    except Exception as e:
        logger.error(f"❌ AI服务初始化失败: {e}")
        raise


async def init_vector_database():
    """初始化向量数据库"""
    try:
        logger.info("✅ 向量数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 向量数据库初始化失败: {e}")
        raise


async def init_graph_database():
    """初始化图数据库"""
    try:
        logger.info("✅ 图数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 图数据库初始化失败: {e}")
        raise


async def cleanup_resources():
    """清理资源"""
    try:
        await close_db()
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
