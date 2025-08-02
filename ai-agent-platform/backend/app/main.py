"""
智能体应用综合平台 - 主应用入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import check_db_connection
from app.api.v1 import api_router


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 智能体应用综合平台启动中...")

    # 检查数据库连接
    try:
        if check_db_connection():
            logger.info("✅ 数据库连接正常")
        else:
            logger.warning("⚠️ 数据库连接失败，请检查配置")
    except Exception as e:
        logger.error(f"❌ 数据库连接检查失败: {e}")

    logger.info("✅ 应用启动完成")

    yield

    # 关闭时执行
    logger.info("🔄 应用正在关闭...")
    logger.info("✅ 应用关闭完成")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="智能体应用综合平台 - 集成了前沿AI技术的一站式智能体解决方案",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件 (暂时注释掉，避免配置问题)
# if settings.BACKEND_CORS_ORIGINS:
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=settings.BACKEND_CORS_ORIGINS
#     )


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间到响应头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "Internal server error",
            "timestamp": time.time(),
            "path": str(request.url)
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    db_status = "connected" if check_db_connection() else "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "services": {
            "database": db_status,
            "redis": "unknown",  # 可以后续添加Redis检查
            "milvus": "unknown"  # 可以后续添加Milvus检查
        }
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "智能体应用综合平台 API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
