import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.base import settings
from app.config.factory import config_factory
from app.database.connection import create_tables
from app.api import auth, documents, ai, config
# 导入模型以确保它们被注册
import app.models

# 创建FastAPI应用
app = FastAPI(
    title="AI写作平台",
    description="基于FastAPI + AutoGen的智能写作平台",
    version="1.0.0"
)

# 配置CORS
cors_config = config_factory.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(documents.router, prefix="/api/documents", tags=["文档"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI助手"])
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])

# 导入模板路由
from app.api import template
app.include_router(template.router, prefix="/api/templates", tags=["模板管理"])

# 导入智能体配置路由
from app.api import agent_config
app.include_router(agent_config.router, prefix="/api", tags=["智能体配置"])

# 导入模型客户端管理路由
from app.api import model_clients
app.include_router(model_clients.router, prefix="/api", tags=["模型客户端管理"])

# 导入统一AI生成路由
from app.api import ai_generation
app.include_router(ai_generation.router, prefix="/api/ai-generation", tags=["AI内容生成"])

# 导入AI写作路由
from app.api import ai_writing
app.include_router(ai_writing.router, prefix="/api/ai-writing", tags=["AI写作"])

# 导入写作主题管理路由
from app.api import writing_theme_management
app.include_router(writing_theme_management.router, prefix="/api/writing-themes", tags=["写作主题管理"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 创建数据库表
    create_tables()


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI写作平台 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
