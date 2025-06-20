#!/usr/bin/env python3
"""
智能客服系统快速启动脚本
一键完成环境检查、模型下载、数据库初始化和系统启动
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuickStarter:
    """快速启动器"""
    
    def __init__(self, skip_checks: bool = False, force_download: bool = False):
        """
        初始化快速启动器
        
        Args:
            skip_checks: 跳过环境检查
            force_download: 强制重新下载模型
        """
        self.skip_checks = skip_checks
        self.force_download = force_download
        self.project_root = Path(__file__).parent
        self.scripts_dir = self.project_root / "scripts"
        
    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        智能客服系统 v2.0 快速启动                            ║
║                                                                              ║
║  🤖 基于AutoGen智能体框架                                                    ║
║  🧠 集成DeepSeek-Chat + Qwen-VL-Max多模态模型                               ║
║  🔍 Milvus向量数据库 + Neo4j图数据库                                        ║
║  📄 Marker高质量文档解析                                                     ║
║  🎨 Gemini风格炫酷聊天界面                                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self) -> bool:
        """检查Python版本"""
        logger.info("检查Python版本...")
        
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"❌ Python版本过低: {python_version}, 需要3.8+")
            return False
        
        logger.info(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return True
    
    def check_dependencies(self) -> bool:
        """检查关键依赖"""
        logger.info("检查关键依赖...")
        
        critical_packages = [
            "fastapi",
            "uvicorn", 
            "autogen_agentchat",
            "pymilvus",
            "transformers",
            "torch"
        ]
        
        missing_packages = []
        
        for package in critical_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package}")
            except ImportError:
                logger.error(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"缺少关键依赖: {', '.join(missing_packages)}")
            logger.info("请运行: pip install -r requirements-upgrade.txt")
            return False
        
        return True
    
    async def download_models(self) -> bool:
        """下载模型"""
        logger.info("检查和下载模型...")
        
        try:
            script_path = self.scripts_dir / "download_models.py"
            
            cmd = [sys.executable, str(script_path)]
            if self.force_download:
                cmd.append("--force")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ 模型下载完成")
                return True
            else:
                logger.error(f"❌ 模型下载失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 模型下载过程出错: {str(e)}")
            return False
    
    async def init_databases(self) -> bool:
        """初始化数据库"""
        logger.info("初始化数据库...")
        
        try:
            script_path = self.scripts_dir / "init_databases.py"
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ 数据库初始化完成")
                return True
            else:
                logger.warning(f"⚠️ 数据库初始化部分失败: {stderr.decode()}")
                # 数据库初始化失败不阻止启动
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ 数据库初始化过程出错: {str(e)}")
            return True
    
    async def verify_system(self) -> bool:
        """验证系统"""
        logger.info("验证系统状态...")
        
        try:
            script_path = self.scripts_dir / "verify_system.py"
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path), "--task", "python",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ 系统验证通过")
                return True
            else:
                logger.warning(f"⚠️ 系统验证发现问题: {stderr.decode()}")
                return True  # 不阻止启动
                
        except Exception as e:
            logger.warning(f"⚠️ 系统验证过程出错: {str(e)}")
            return True
    
    def create_env_file(self):
        """创建环境变量文件"""
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            logger.info("✅ .env文件已存在")
            return
        
        logger.info("创建.env配置文件...")
        
        env_template = """# 智能客服系统环境配置

# 应用配置
APP_NAME=智能客服系统升级版
APP_VERSION=2.0.0
DEBUG=True
SECRET_KEY=your_secret_key_here_please_change_in_production

# 数据库配置
DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=mysql://ics_user:ics_password@localhost:3306/intelligent_customer_service

# Milvus向量数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_DATABASE=default

# Neo4j图数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
NEO4J_DATABASE=neo4j

# Redis缓存配置
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 模型API配置（请填入您的API密钥）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ModelScope本地模型配置
MODELSCOPE_CACHE_DIR=./models
MODELSCOPE_TOKEN=your_modelscope_token_here

# 嵌入模型配置
EMBEDDING_MODEL=Qwen/Qwen3-0.6B
EMBEDDING_DEVICE=cpu
EMBEDDING_MAX_LENGTH=512

# 重排模型配置
RERANK_MODEL=Qwen/Qwen3-Reranker-0.6B
RERANK_DEVICE=cpu

# 文档解析配置
MARKER_MODELS_DIR=./models/marker
MARKER_TEMP_DIR=./temp/marker
MARKER_MAX_PAGES=1000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# 安全配置
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# 文件上传配置
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "txt", "md", "jpg", "jpeg", "png", "gif"]
UPLOAD_DIR=./uploads

# 性能配置
MAX_WORKERS=4
REQUEST_TIMEOUT=30
BATCH_SIZE=32
"""
        
        try:
            env_file.write_text(env_template, encoding='utf-8')
            logger.info("✅ .env配置文件创建成功")
            logger.warning("⚠️ 请编辑.env文件，填入您的API密钥")
        except Exception as e:
            logger.error(f"❌ 创建.env文件失败: {str(e)}")
    
    def start_backend_server(self):
        """启动后端服务器"""
        logger.info("启动后端服务器...")
        
        try:
            # 创建日志目录
            logs_dir = self.project_root / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # 启动命令
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "9999",
                "--reload"
            ]
            
            logger.info("🚀 启动后端服务器...")
            logger.info(f"命令: {' '.join(cmd)}")
            logger.info("服务器地址: http://localhost:9999")
            logger.info("API文档: http://localhost:9999/docs")
            logger.info("按 Ctrl+C 停止服务器")
            
            # 启动服务器
            subprocess.run(cmd, cwd=self.project_root)
            
        except KeyboardInterrupt:
            logger.info("用户停止服务器")
        except Exception as e:
            logger.error(f"❌ 启动后端服务器失败: {str(e)}")
    
    def show_next_steps(self):
        """显示后续步骤"""
        next_steps = """
🎉 智能客服系统启动完成！

📋 后续步骤:

1. 🔑 配置API密钥
   编辑 .env 文件，填入您的模型API密钥：
   - DEEPSEEK_API_KEY: DeepSeek大语言模型API密钥
   - QWEN_API_KEY: 通义千问多模态模型API密钥

2. 🌐 访问系统
   - 后端API: http://localhost:9999
   - API文档: http://localhost:9999/docs
   - 管理后台: http://localhost:3000 (需要启动前端)
   - 聊天界面: http://localhost:3001 (需要启动前端)

3. 🖥️ 启动前端界面
   # Vue3管理后台
   cd web && pnpm install && pnpm dev
   
   # React聊天界面
   cd web-react && pnpm install && pnpm dev

4. 🧪 测试系统
   python scripts/verify_system.py

5. 📚 查看文档
   - 架构设计: 智能客服系统完整架构设计方案.md
   - 工作计划: 详细分阶段工作计划.md
   - 启动指南: 项目启动指南.md

如有问题，请查看日志文件: logs/app.log
        """
        print(next_steps)
    
    async def run_quick_start(self):
        """运行快速启动流程"""
        self.print_banner()
        
        start_time = time.time()
        
        try:
            # 1. 检查Python版本
            if not self.check_python_version():
                return False
            
            # 2. 检查依赖
            if not self.skip_checks and not self.check_dependencies():
                logger.error("❌ 依赖检查失败，请先安装依赖")
                return False
            
            # 3. 创建配置文件
            self.create_env_file()
            
            # 4. 下载模型
            if not await self.download_models():
                logger.error("❌ 模型下载失败")
                return False
            
            # 5. 初始化数据库
            if not await self.init_databases():
                logger.warning("⚠️ 数据库初始化失败，但继续启动")
            
            # 6. 验证系统
            if not self.skip_checks:
                await self.verify_system()
            
            total_time = time.time() - start_time
            logger.info(f"✅ 系统准备完成，耗时 {total_time:.1f} 秒")
            
            # 7. 显示后续步骤
            self.show_next_steps()
            
            # 8. 启动后端服务器
            input("\n按回车键启动后端服务器...")
            self.start_backend_server()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("用户中断启动流程")
            return False
        except Exception as e:
            logger.error(f"❌ 启动流程失败: {str(e)}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能客服系统快速启动")
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="跳过环境检查和系统验证"
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="强制重新下载模型"
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="不启动后端服务器"
    )
    
    args = parser.parse_args()
    
    # 创建快速启动器
    starter = QuickStarter(
        skip_checks=args.skip_checks,
        force_download=args.force_download
    )
    
    try:
        if args.no_server:
            # 只进行准备工作，不启动服务器
            async def prepare_only():
                starter.print_banner()
                
                if not starter.check_python_version():
                    return False
                
                if not args.skip_checks and not starter.check_dependencies():
                    return False
                
                starter.create_env_file()
                
                if not await starter.download_models():
                    return False
                
                if not await starter.init_databases():
                    logger.warning("数据库初始化失败")
                
                if not args.skip_checks:
                    await starter.verify_system()
                
                starter.show_next_steps()
                return True
            
            success = asyncio.run(prepare_only())
        else:
            # 完整启动流程
            success = asyncio.run(starter.run_quick_start())
        
        if success:
            logger.info("🎉 启动流程完成")
            sys.exit(0)
        else:
            logger.error("❌ 启动流程失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
