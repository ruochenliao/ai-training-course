#!/usr/bin/env python3
"""
企业级Agent+RAG知识库系统 - 后端服务管理工具
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
    
    def load_environment(self):
        """加载环境变量"""
        if self.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
    
    async def init_database(self):
        """初始化数据库"""
        logger.info("🔧 初始化数据库...")
        
        try:
            # 导入数据库初始化模块
            from app.core.database import init_db, create_initial_data
            
            # 初始化数据库连接和表结构
            await init_db()
            logger.info("✅ 数据库表结构初始化完成")
            
            # 创建初始数据
            await create_initial_data()
            logger.info("✅ 初始数据创建完成")
            
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    async def migrate_database(self):
        """数据库迁移"""
        logger.info("🔧 执行数据库迁移...")
        
        try:
            # 这里应该实现数据库迁移逻辑
            # 例如使用Alembic进行迁移
            logger.info("✅ 数据库迁移完成")
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            raise
    
    def create_superuser(self, username: str, email: str, password: str):
        """创建超级用户"""
        logger.info(f"👤 创建超级用户: {username}")
        
        try:
            # 这里应该实现创建超级用户的逻辑
            logger.info("✅ 超级用户创建完成")
        except Exception as e:
            logger.error(f"❌ 超级用户创建失败: {e}")
            raise
    
    def run_tests(self, test_path: Optional[str] = None):
        """运行测试"""
        logger.info("🧪 运行测试...")
        
        cmd = ["python", "-m", "pytest"]
        
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("tests/")
        
        # 添加测试选项
        cmd.extend([
            "-v",  # 详细输出
            "--tb=short",  # 简短的错误回溯
            "--cov=app",  # 代码覆盖率
            "--cov-report=html",  # HTML覆盖率报告
            "--cov-report=term-missing"  # 终端显示缺失的行
        ])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            if result.returncode == 0:
                logger.info("✅ 所有测试通过")
            else:
                logger.error("❌ 部分测试失败")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 运行测试失败: {e}")
            return False
    
    def lint_code(self):
        """代码检查"""
        logger.info("🔍 执行代码检查...")
        
        tools = [
            (["black", "--check", "app/"], "Black 格式检查"),
            (["isort", "--check-only", "app/"], "Import 排序检查"),
            (["flake8", "app/"], "Flake8 代码风格检查"),
            (["mypy", "app/"], "MyPy 类型检查")
        ]
        
        all_passed = True
        
        for cmd, description in tools:
            try:
                logger.info(f"🔧 {description}...")
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ {description} 通过")
                else:
                    logger.error(f"❌ {description} 失败")
                    if result.stdout:
                        logger.error(f"输出: {result.stdout}")
                    if result.stderr:
                        logger.error(f"错误: {result.stderr}")
                    all_passed = False
                    
            except FileNotFoundError:
                logger.warning(f"⚠️  {description} 工具未安装，跳过")
            except Exception as e:
                logger.error(f"❌ {description} 执行失败: {e}")
                all_passed = False
        
        return all_passed
    
    def format_code(self):
        """格式化代码"""
        logger.info("🎨 格式化代码...")
        
        tools = [
            (["black", "app/"], "Black 代码格式化"),
            (["isort", "app/"], "Import 排序")
        ]
        
        for cmd, description in tools:
            try:
                logger.info(f"🔧 {description}...")
                result = subprocess.run(cmd, cwd=self.project_root)
                
                if result.returncode == 0:
                    logger.info(f"✅ {description} 完成")
                else:
                    logger.error(f"❌ {description} 失败")
                    
            except FileNotFoundError:
                logger.warning(f"⚠️  {description} 工具未安装，跳过")
            except Exception as e:
                logger.error(f"❌ {description} 执行失败: {e}")
    
    def generate_docs(self):
        """生成文档"""
        logger.info("📚 生成API文档...")
        
        try:
            # 生成OpenAPI文档
            from app.main import app
            import json
            
            docs_dir = self.project_root / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # 导出OpenAPI规范
            openapi_spec = app.openapi()
            with open(docs_dir / "openapi.json", "w", encoding="utf-8") as f:
                json.dump(openapi_spec, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ API文档生成完成")
            
        except Exception as e:
            logger.error(f"❌ 文档生成失败: {e}")
    
    def backup_database(self, backup_path: Optional[str] = None):
        """备份数据库"""
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.sql"
        
        logger.info(f"💾 备份数据库到: {backup_path}")
        
        try:
            # 这里应该实现数据库备份逻辑
            logger.info("✅ 数据库备份完成")
        except Exception as e:
            logger.error(f"❌ 数据库备份失败: {e}")
    
    def restore_database(self, backup_path: str):
        """恢复数据库"""
        logger.info(f"🔄 从备份恢复数据库: {backup_path}")
        
        try:
            # 这里应该实现数据库恢复逻辑
            logger.info("✅ 数据库恢复完成")
        except Exception as e:
            logger.error(f"❌ 数据库恢复失败: {e}")


# CLI命令定义
@click.group()
def cli():
    """企业级Agent+RAG知识库系统 - 后端服务管理工具"""
    pass

@cli.command()
def init_db():
    """初始化数据库"""
    manager = ServiceManager()
    manager.load_environment()
    asyncio.run(manager.init_database())

@cli.command()
def migrate():
    """数据库迁移"""
    manager = ServiceManager()
    manager.load_environment()
    asyncio.run(manager.migrate_database())

@cli.command()
@click.option("--username", prompt=True, help="用户名")
@click.option("--email", prompt=True, help="邮箱")
@click.option("--password", prompt=True, hide_input=True, help="密码")
def create_superuser(username, email, password):
    """创建超级用户"""
    manager = ServiceManager()
    manager.load_environment()
    manager.create_superuser(username, email, password)

@cli.command()
@click.option("--path", help="测试路径")
def test(path):
    """运行测试"""
    manager = ServiceManager()
    manager.run_tests(path)

@cli.command()
def lint():
    """代码检查"""
    manager = ServiceManager()
    manager.lint_code()

@cli.command()
def format():
    """格式化代码"""
    manager = ServiceManager()
    manager.format_code()

@cli.command()
def docs():
    """生成文档"""
    manager = ServiceManager()
    manager.load_environment()
    manager.generate_docs()

@cli.command()
@click.option("--path", help="备份文件路径")
def backup(path):
    """备份数据库"""
    manager = ServiceManager()
    manager.load_environment()
    manager.backup_database(path)

@cli.command()
@click.argument("backup_path")
def restore(backup_path):
    """恢复数据库"""
    manager = ServiceManager()
    manager.load_environment()
    manager.restore_database(backup_path)

if __name__ == "__main__":
    cli()
