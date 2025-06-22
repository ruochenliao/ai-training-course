#!/usr/bin/env python3
"""
企业级Agent+RAG知识库系统 - 后端生产环境启动脚本
"""

import multiprocessing
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

class BackendProdServer:
    """后端生产服务器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.pid_file = self.project_root / "server.pid"
        self.workers: List[subprocess.Popen] = []
        
    def check_environment(self) -> bool:
        """检查生产环境配置"""
        logger.info("🔍 检查生产环境配置...")
        
        if not self.env_file.exists():
            logger.error("❌ .env 文件不存在，生产环境必须提供配置文件")
            return False
        
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
            
            # 检查关键配置
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL", 
                "SECRET_KEY",
                "LLM_API_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
                return False
            
            # 确保生产环境配置
            os.environ["ENVIRONMENT"] = "production"
            os.environ["DEBUG"] = "false"
            
            logger.info("✅ 生产环境配置检查通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 环境配置加载失败: {e}")
            return False
    
    def check_services(self) -> bool:
        """检查外部服务连接"""
        logger.info("🔍 检查外部服务连接...")
        
        services_status = {
            "MySQL数据库": self.check_database(),
            "Redis缓存": self.check_redis(),
            "Milvus向量数据库": self.check_milvus(),
            "Neo4j图数据库": self.check_neo4j(),
            "MinIO对象存储": self.check_minio(),
            "LLM模型API": self.check_llm_api(),
            "嵌入模型API": self.check_embedding_api(),
            "重排模型API": self.check_reranker_api(),
        }
        
        failed_services = [name for name, status in services_status.items() if not status]
        
        for service, status in services_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {service}: {'连接正常' if status else '连接失败'}")
        
        if failed_services:
            logger.error(f"❌ 以下服务连接失败: {', '.join(failed_services)}")
            logger.error("🛑 生产环境要求所有服务正常运行")
            return False
        
        return True
    
    def check_database(self) -> bool:
        """检查MySQL数据库连接"""
        try:
            import pymysql
            connection = pymysql.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'rag_system'),
                connect_timeout=5
            )
            # 测试连接
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection.close()
            logger.debug("MySQL数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"MySQL数据库连接失败: {e}")
            return False
    
    def check_redis(self) -> bool:
        """检查Redis连接"""
        try:
            import redis
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                db=int(os.getenv('REDIS_DB', 0)),
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            client.ping()
            logger.debug("Redis连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False
    
    def check_milvus(self) -> bool:
        """检查Milvus向量数据库连接"""
        try:
            from pymilvus import connections, utility
            
            host = os.getenv('MILVUS_HOST', 'localhost')
            port = os.getenv('MILVUS_PORT', '19530')
            
            # 连接到Milvus
            connections.connect(
                alias="default",
                host=host,
                port=port,
                timeout=5
            )
            
            # 测试连接
            utility.get_server_version()
            logger.debug("Milvus向量数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Milvus向量数据库连接失败: {e}")
            return False
    
    def check_neo4j(self) -> bool:
        """检查Neo4j图数据库连接"""
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            username = os.getenv('NEO4J_USERNAME', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', 'password')
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # 测试连接
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            driver.close()
            logger.debug("Neo4j图数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Neo4j图数据库连接失败: {e}")
            return False
    
    def check_minio(self) -> bool:
        """检查MinIO对象存储连接"""
        try:
            from minio import Minio
            
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
            secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            
            client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # 测试连接
            client.list_buckets()
            logger.debug("MinIO对象存储连接测试成功")
            return True
        except Exception as e:
            logger.error(f"MinIO对象存储连接失败: {e}")
            return False
    
    def check_llm_api(self) -> bool:
        """检查LLM模型API连接"""
        try:
            import requests
            
            api_key = os.getenv('LLM_API_KEY')
            api_base = os.getenv('LLM_API_BASE')
            model_name = os.getenv('LLM_MODEL_NAME')
            
            if not api_key or not api_base:
                logger.warning("LLM API配置不完整，跳过检测")
                return True  # 生产环境可能需要更严格的检查
            
            # 简单的健康检查
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # 尝试获取模型列表或发送简单请求
            response = requests.get(
                f"{api_base}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("LLM模型API连接测试成功")
                return True
            else:
                logger.error(f"LLM模型API返回状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"LLM模型API连接失败: {e}")
            return False
    
    def check_embedding_api(self) -> bool:
        """检查嵌入模型API连接"""
        try:
            import requests
            
            api_key = os.getenv('EMBEDDING_API_KEY')
            api_base = os.getenv('EMBEDDING_API_BASE')
            model_name = os.getenv('EMBEDDING_MODEL_NAME')
            
            if not api_key or not api_base:
                logger.warning("嵌入模型API配置不完整，跳过检测")
                return True
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{api_base}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("嵌入模型API连接测试成功")
                return True
            else:
                logger.error(f"嵌入模型API返回状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"嵌入模型API连接失败: {e}")
            return False
    
    def check_reranker_api(self) -> bool:
        """检查重排模型API连接"""
        try:
            import requests
            
            api_key = os.getenv('RERANKER_API_KEY')
            api_base = os.getenv('RERANKER_API_BASE')
            model_name = os.getenv('RERANKER_MODEL_NAME')
            
            if not api_key or not api_base:
                logger.warning("重排模型API配置不完整，跳过检测")
                return True
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{api_base}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("重排模型API连接测试成功")
                return True
            else:
                logger.error(f"重排模型API返回状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"重排模型API连接失败: {e}")
            return False
    
    def setup_logging(self):
        """设置生产环境日志"""
        # 创建logs目录
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 生产环境只输出到文件
        logger.add(
            logs_dir / "backend_{time:YYYY-MM-DD}.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # 错误日志单独记录
        logger.add(
            logs_dir / "error_{time:YYYY-MM-DD}.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
    
    def create_pid_file(self, pid: int):
        """创建PID文件"""
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
    
    def remove_pid_file(self):
        """删除PID文件"""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def is_running(self) -> bool:
        """检查服务是否正在运行"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            self.remove_pid_file()
            return False
    
    def stop_server(self):
        """停止服务器"""
        if not self.is_running():
            logger.info("📍 服务器未运行")
            return
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            logger.info(f"🛑 正在停止服务器 (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程结束
            for _ in range(30):  # 最多等待30秒
                if not self.is_running():
                    break
                time.sleep(1)
            
            if self.is_running():
                logger.warning("⚠️  强制终止服务器...")
                os.kill(pid, signal.SIGKILL)
            
            self.remove_pid_file()
            logger.info("✅ 服务器已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止服务器失败: {e}")
    
    def start_server(self):
        """启动生产服务器"""
        if self.is_running():
            logger.error("❌ 服务器已在运行中")
            return False
        
        logger.info("🚀 启动生产服务器...")
        
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        workers = int(os.getenv("WORKERS", multiprocessing.cpu_count()))
        
        logger.info(f"📍 服务地址: http://{host}:{port}")
        logger.info(f"👥 工作进程数: {workers}")
        
        try:
            # 使用Gunicorn启动生产服务器
            cmd = [
                "gunicorn",
                "app.main:app",
                "-w", str(workers),
                "-k", "uvicorn.workers.UvicornWorker",
                "-b", f"{host}:{port}",
                "--pid", str(self.pid_file),
                "--daemon",
                "--access-logfile", str(self.project_root / "logs" / "access.log"),
                "--error-logfile", str(self.project_root / "logs" / "error.log"),
                "--log-level", "info",
                "--timeout", "120",
                "--keep-alive", "5",
                "--max-requests", "1000",
                "--max-requests-jitter", "100",
                "--preload"
            ]
            
            subprocess.run(cmd, check=True, cwd=self.project_root)
            
            # 等待服务启动
            time.sleep(3)
            
            if self.is_running():
                logger.info("✅ 生产服务器启动成功")
                return True
            else:
                logger.error("❌ 生产服务器启动失败")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 启动命令执行失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {e}")
            return False
    
    def status(self):
        """显示服务器状态"""
        if self.is_running():
            with open(self.pid_file, 'r') as f:
                pid = f.read().strip()
            logger.info(f"✅ 服务器正在运行 (PID: {pid})")
        else:
            logger.info("📍 服务器未运行")
    
    def restart(self):
        """重启服务器"""
        logger.info("🔄 重启服务器...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def run(self, action: str = "start"):
        """运行生产服务器"""
        logger.info("🎯 企业级Agent+RAG知识库系统 - 生产环境")
        logger.info("=" * 60)
        
        # 设置日志
        self.setup_logging()
        
        if action == "start":
            # 检查环境
            if not self.check_environment():
                sys.exit(1)
            
            # 检查服务
            if not self.check_services():
                sys.exit(1)
            
            # 启动服务器
            if not self.start_server():
                sys.exit(1)
                
        elif action == "stop":
            self.stop_server()
        elif action == "restart":
            if not self.restart():
                sys.exit(1)
        elif action == "status":
            self.status()
        else:
            logger.error(f"❌ 未知操作: {action}")
            logger.info("💡 支持的操作: start, stop, restart, status")
            sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="企业级Agent+RAG知识库系统 - 生产环境服务器")
    parser.add_argument(
        "action", 
        choices=["start", "stop", "restart", "status"],
        help="服务器操作"
    )
    
    args = parser.parse_args()
    
    server = BackendProdServer()
    server.run(args.action)


if __name__ == "__main__":
    main()
