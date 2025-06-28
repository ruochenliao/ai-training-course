#!/usr/bin/env python3
"""
企业级Agent+RAG知识库系统 - 后端开发环境启动脚本
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
backend_root = project_root / "backend"
# 将backend目录添加到Python路径，这样可以直接导入app模块
sys.path.insert(0, str(backend_root))

class BackendDevServer:
    """后端开发服务器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_root = self.project_root / "backend"
        self.env_file = self.project_root / ".env"
        self.server_process: Optional[subprocess.Popen] = None
        
    def check_dependencies(self) -> bool:
        """检查依赖"""
        logger.info("🔍 检查Python依赖...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.error("❌ requirements.txt 文件不存在")
            return False
            
        try:
            # 检查是否安装了所需的包
            import fastapi
            import uvicorn
            import sqlalchemy
            import redis
            logger.info("✅ 核心依赖检查通过")
            return True
        except ImportError as e:
            logger.error(f"❌ 缺少依赖包: {e}")
            logger.info("💡 请运行: pip install -r requirements.txt")
            return False
    
    def check_environment(self) -> bool:
        """检查环境配置"""
        logger.info("🔍 检查环境配置...")
        
        if not self.env_file.exists():
            logger.warning("⚠️  .env 文件不存在，正在创建...")
            self.create_env_file()
        
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
            logger.info("✅ 环境配置加载成功")
            return True
        except Exception as e:
            logger.error(f"❌ 环境配置加载失败: {e}")
            return False
    
    def create_env_file(self):
        """创建环境文件"""
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            import shutil
            shutil.copy(env_example, self.env_file)
            logger.info("✅ 已从 .env.example 创建 .env 文件")
        else:
            # 创建基本的环境文件
            env_content = """# 基础配置
DEBUG=true
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=mysql://root:password@localhost:3306/enterprise_rag

# Redis配置
REDIS_URL=redis://localhost:6379/0

# AI模型配置 (请填入实际的API密钥)
LLM_API_KEY=your_deepseek_api_key_here
EMBEDDING_API_KEY=your_embedding_api_key_here
"""
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            logger.info("✅ 已创建基本的 .env 文件")
    
    def check_services(self) -> bool:
        """检查外部服务"""
        logger.info("🔍 检查外部服务...")
        
        services_status = {
            "MySQL数据库": self.check_mysql(),
            "Redis缓存": self.check_redis(),
            "Milvus向量数据库": self.check_milvus(),
            "Neo4j图数据库": self.check_neo4j(),
            "MinIO对象存储": self.check_minio(),
            "LLM模型API": self.check_llm_api(),
            "嵌入模型API": self.check_embedding_api(),
            "重排模型API": self.check_reranker_api(),
        }
        
        all_ok = all(services_status.values())
        
        for service, status in services_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {service}: {'可用' if status else '不可用'}")
        
        if not all_ok:
            logger.warning("⚠️  部分服务不可用，可能影响系统功能")
            logger.info("💡 请确保相关服务已启动，或使用 Docker 启动完整环境")
        
        return True  # 即使服务不可用也允许启动，用于开发调试
    
    def check_mysql(self) -> bool:
        """检查MySQL连接"""
        try:
            import pymysql
            from urllib.parse import urlparse
            database_url = os.getenv("DATABASE_URL", "mysql://root:password@localhost:3306/enterprise_rag")
            
            # 解析数据库URL
            parsed = urlparse(database_url)
            connection = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                connect_timeout=5
            )
            connection.ping()
            connection.close()
            return True
        except Exception as e:
            logger.debug(f"MySQL连接失败: {e}")
            return False
    
    def check_redis(self) -> bool:
        """检查Redis连接"""
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            r.ping()
            return True
        except Exception as e:
            logger.debug(f"Redis连接失败: {e}")
            return False
    
    def check_milvus(self) -> bool:
        """检查Milvus连接"""
        try:
            from pymilvus import connections, utility
            
            host = os.getenv("MILVUS_HOST", "localhost")
            port = os.getenv("MILVUS_PORT", "19530")
            user = os.getenv("MILVUS_USER", "")
            password = os.getenv("MILVUS_PASSWORD", "")
            
            # 连接Milvus
            connections.connect(
                alias="default",
                host=host,
                port=port,
                user=user,
                password=password,
                timeout=5
            )
            
            # 检查连接状态
            if utility.get_server_version():
                connections.disconnect("default")
                return True
            return False
        except Exception as e:
            logger.debug(f"Milvus连接失败: {e}")
            return False
    
    def check_neo4j(self) -> bool:
        """检查Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            driver.close()
            return True
        except Exception as e:
            logger.debug(f"Neo4j连接失败: {e}")
            return False
    
    def check_minio(self) -> bool:
        """检查MinIO连接"""
        try:
            from minio import Minio
            
            endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY", "")
            secret_key = os.getenv("MINIO_SECRET_KEY", "")
            secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
            
            if not access_key or not secret_key:
                return False
            
            client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # 检查连接
            list(client.list_buckets())
            return True
        except Exception as e:
            logger.debug(f"MinIO连接失败: {e}")
            return False
    
    def check_llm_api(self) -> bool:
        """检查LLM API连接"""
        try:
            import requests
            
            api_base = os.getenv("LLM_API_BASE", "")
            api_key = os.getenv("LLM_API_KEY", "")
            
            if not api_base or not api_key:
                return False
            
            # 简单的健康检查
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{api_base.rstrip('/')}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"LLM API连接失败: {e}")
            return False
    
    def check_embedding_api(self) -> bool:
        """检查嵌入模型API连接"""
        try:
            import requests
            
            api_base = os.getenv("EMBEDDING_API_BASE", "")
            api_key = os.getenv("EMBEDDING_API_KEY", "")
            
            if not api_base or not api_key:
                return False
            
            # 简单的健康检查
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{api_base.rstrip('/')}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"嵌入模型API连接失败: {e}")
            return False
    
    def check_reranker_api(self) -> bool:
        """检查重排模型API连接"""
        try:
            import requests
            
            api_base = os.getenv("RERANKER_API_BASE", "")
            api_key = os.getenv("RERANKER_API_KEY", "")
            
            if not api_base or not api_key:
                return False
            
            # 简单的健康检查
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{api_base.rstrip('/')}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"重排模型API连接失败: {e}")
            return False
    
    def setup_logging(self):
        """设置日志"""
        log_level = os.getenv("LOG_LEVEL", "DEBUG")
        
        # 创建logs目录
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 控制台输出
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # 文件输出
        logger.add(
            logs_dir / "backend_{time:YYYY-MM-DD}.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="7 days",
            compression="zip"
        )
    
    def start_server(self):
        """启动服务器"""
        logger.info("🚀 启动后端开发服务器...")

        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        reload = os.getenv("RELOAD", "true").lower() == "true"
        log_level = os.getenv("LOG_LEVEL", "debug").lower()

        logger.info(f"📍 服务地址: http://{host}:{port}")
        logger.info(f"📚 API文档: http://{host}:{port}/docs")
        logger.info(f"🔍 健康检查: http://{host}:{port}/health")

        # 切换到backend目录作为工作目录
        original_cwd = os.getcwd()
        os.chdir(str(self.backend_root))

        # 确保backend目录在Python路径中
        if str(self.backend_root) not in sys.path:
            sys.path.insert(0, str(self.backend_root))

        try:
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                reload=reload,
                log_level=log_level,
                access_log=True,
                reload_dirs=[str(self.backend_root / "app")],
                reload_excludes=["*.pyc", "*.pyo", "__pycache__", "logs/*", "temp/*"]
            )
        except KeyboardInterrupt:
            logger.info("🛑 服务器已停止")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            sys.exit(1)
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
    
    def run(self):
        """运行开发服务器"""
        logger.info("🎯 企业级Agent+RAG知识库系统 - 后端开发环境")
        logger.info("=" * 60)
        
        # 设置日志
        self.setup_logging()
        
        # 检查依赖
        if not self.check_dependencies():
            sys.exit(1)
        
        # 检查环境
        if not self.check_environment():
            sys.exit(1)
        
        # 检查服务
        self.check_services()
        
        # 启动服务器
        self.start_server()


def main():
    """主函数"""
    server = BackendDevServer()
    server.run()


if __name__ == "__main__":
    main()
