#!/usr/bin/env python3
"""
企业级RAG知识库系统部署脚本
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                企业级Agent+RAG知识库系统                      ║
║                                                              ║
║  🤖 AutoGen多智能体协作                                       ║
║  🔍 向量数据库 + 知识图谱混合检索                              ║
║  🧠 大语言模型智能问答                                         ║
║  📚 企业级知识管理                                             ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本需要3.8或更高")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker未安装或不可用")
            return False
    except FileNotFoundError:
        print("❌ Docker未安装")
        return False
    
    # 检查Docker Compose
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose未安装或不可用")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose未安装")
        return False
    
    return True


def create_env_file():
    """创建环境变量文件"""
    print("📝 创建环境配置文件...")
    
    env_content = """# 企业级RAG知识库系统环境配置

# 基础配置
PROJECT_NAME=企业级Agent+RAG知识库系统
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 安全配置
SECRET_KEY=your-secret-key-here-please-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_MINUTES=43200

# 数据库配置
DATABASE_URL=mysql://root:password@mysql:3306/enterprise_rag
REDIS_URL=redis://redis:6379/0

# Milvus向量数据库配置
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=knowledge_base_vectors

# Neo4j图数据库配置
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# MinIO对象存储配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=enterprise-rag
MINIO_SECURE=false

# AI模型配置（请填入您的API密钥）
# LLM配置
LLM_MODEL_NAME=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your-deepseek-api-key-here

# 嵌入模型配置
EMBEDDING_MODEL_NAME=text-embedding-v1
EMBEDDING_API_BASE=https://dashscope.aliyuncs.com/api/v1
EMBEDDING_API_KEY=your-dashscope-api-key-here
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=100

# 重排模型配置
RERANKER_MODEL_NAME=gte-rerank
RERANKER_API_BASE=https://dashscope.aliyuncs.com/api/v1
RERANKER_API_KEY=your-dashscope-api-key-here

# 文档处理配置
MAX_FILE_SIZE=104857600  # 100MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 检索配置
DEFAULT_TOP_K=10
DEFAULT_SCORE_THRESHOLD=0.7

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
    
    env_file = Path("backend/.env")
    if not env_file.exists():
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"✅ 环境配置文件已创建: {env_file}")
    else:
        print(f"⚠️ 环境配置文件已存在: {env_file}")
    
    print("\n⚠️ 重要提醒:")
    print("请编辑 backend/.env 文件，填入您的API密钥:")
    print("- LLM_API_KEY: DeepSeek API密钥")
    print("- EMBEDDING_API_KEY: 阿里云DashScope API密钥")
    print("- RERANKER_API_KEY: 阿里云DashScope API密钥")


def start_infrastructure():
    """启动基础设施服务"""
    print("🚀 启动基础设施服务...")
    
    try:
        # 启动Docker Compose服务
        cmd = ["docker-compose", "up", "-d", "mysql", "redis", "milvus-etcd", "milvus-minio", "milvus-standalone", "neo4j", "minio"]
        result = subprocess.run(cmd, cwd=".", capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 基础设施服务启动成功")
            print("等待服务初始化...")
            time.sleep(30)  # 等待服务启动
            return True
        else:
            print(f"❌ 基础设施服务启动失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 启动基础设施服务时出错: {e}")
        return False


def install_backend_dependencies():
    """安装后端依赖"""
    print("📦 安装后端依赖...")
    
    try:
        # 切换到后端目录
        os.chdir("backend")
        
        # 安装Python依赖
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 后端依赖安装成功")
            return True
        else:
            print(f"❌ 后端依赖安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装后端依赖时出错: {e}")
        return False
    finally:
        os.chdir("..")


def install_frontend_dependencies():
    """安装前端依赖"""
    print("📦 安装前端依赖...")
    
    try:
        # 切换到前端目录
        os.chdir("frontend/user-app")
        
        # 安装Node.js依赖
        result = subprocess.run(["npm", "install"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 前端依赖安装成功")
            return True
        else:
            print(f"❌ 前端依赖安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装前端依赖时出错: {e}")
        return False
    finally:
        os.chdir("../..")


def run_database_migrations():
    """运行数据库迁移"""
    print("🗄️ 运行数据库迁移...")
    
    try:
        os.chdir("backend")
        
        # 运行数据库迁移
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据库迁移完成")
            return True
        else:
            print(f"❌ 数据库迁移失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行数据库迁移时出错: {e}")
        return False
    finally:
        os.chdir("..")


def start_backend():
    """启动后端服务"""
    print("🔧 启动后端服务...")
    
    try:
        os.chdir("backend")
        
        # 启动FastAPI服务
        print("后端服务正在启动，请在新终端中运行:")
        print("cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        
        return True
        
    except Exception as e:
        print(f"❌ 启动后端服务时出错: {e}")
        return False
    finally:
        os.chdir("..")


def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端服务...")
    
    try:
        os.chdir("frontend/user-app")
        
        # 启动Next.js服务
        print("前端服务正在启动，请在新终端中运行:")
        print("cd frontend/user-app && npm run dev")
        
        return True
        
    except Exception as e:
        print(f"❌ 启动前端服务时出错: {e}")
        return False
    finally:
        os.chdir("../..")


def print_success_info():
    """打印成功信息"""
    success_info = """
🎉 企业级RAG知识库系统部署完成！

📋 服务地址:
- 前端用户界面: http://localhost:3000
- 后端API文档: http://localhost:8000/docs
- 管理后台: http://localhost:8080 (如果启用)

🔧 管理界面:
- Milvus管理: http://localhost:9091
- Neo4j浏览器: http://localhost:7474
- MinIO控制台: http://localhost:9001

📚 使用说明:
1. 访问前端界面开始使用智能问答
2. 通过API上传文档到知识库
3. 配置知识库和用户权限
4. 查看API文档了解更多功能

⚠️ 注意事项:
- 请确保已配置正确的API密钥
- 首次使用需要创建知识库和上传文档
- 生产环境请修改默认密码和密钥

🆘 如需帮助:
- 查看README.md文档
- 运行测试脚本: python backend/test_system.py
- 检查日志文件排查问题
"""
    print(success_info)


def main():
    """主函数"""
    print_banner()
    
    # 检查系统要求
    if not check_requirements():
        print("❌ 系统要求检查失败，请安装必要的依赖")
        return False
    
    print()
    
    # 创建环境配置文件
    create_env_file()
    print()
    
    # 启动基础设施服务
    if not start_infrastructure():
        print("❌ 基础设施服务启动失败")
        return False
    
    print()
    
    # 安装依赖
    if not install_backend_dependencies():
        print("❌ 后端依赖安装失败")
        return False
    
    print()
    
    if not install_frontend_dependencies():
        print("❌ 前端依赖安装失败")
        return False
    
    print()
    
    # 运行数据库迁移
    if not run_database_migrations():
        print("❌ 数据库迁移失败")
        return False
    
    print()
    
    # 启动服务
    start_backend()
    print()
    start_frontend()
    print()
    
    # 打印成功信息
    print_success_info()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
