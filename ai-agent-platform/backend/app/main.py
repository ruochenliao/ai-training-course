# Copyright (c) 2025 左岚. All rights reserved.
"""
智能体应用综合平台 - 主应用入口
"""

# # Standard library imports
import os
from pathlib import Path
import sys

# 添加backend目录到Python路径，使用相对路径
current_file = Path(__file__).resolve()  # 获取当前文件的绝对路径
backend_dir = current_file.parent.parent  # 向上两级到backend目录
sys.path.insert(0, str(backend_dir))  # 添加到Python路径

# # Standard library imports
from contextlib import asynccontextmanager
import logging
import time

# # Third-party imports
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# # Local application imports
from app.api.v1 import api_router
from app.core.config import settings
from app.core.simple_cache import cache_manager
from app.core.database_pool import db_pool_manager
from app.core.logging_config import structured_logger
from app.core.metrics import metrics_manager
from app.core.tracing import tracing_manager
from app.db.init_db import init as init_database_data
from app.db.session import check_db_connection, init_db
from app.rag.embeddings import embedding_manager

# 初始化结构化日志
structured_logger = structured_logger
logger = logging.getLogger(__name__)

# 减少各种组件的日志详细程度
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)  # 只显示错误
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)  # 减少模型加载日志
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('torch').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('watchfiles').setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 智能体应用综合平台启动中...")

    # 自动初始化数据库
    try:
        init_database_data()  # 这个函数现在会自动检查数据库状态并决定是否初始化数据
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")

    # 启动BGE模型后台下载任务
    try:
        embedding_manager.start_background_bge_loading()
        logger.info("🤖 BGE模型后台加载中...")
    except Exception as e:
        logger.error(f"❌ BGE模型后台任务启动失败: {e}")

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

    # 获取嵌入模型状态
    embedding_status = embedding_manager.get_model_status()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "embedding_models": embedding_status,
        "default_embedding_model": embedding_manager.default_model,
        "services": {
            "database": db_status,
            "deepseek_llm": "ready",
            "embedding": "ready" if embedding_status else "unknown",
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
    # # Third-party imports
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
