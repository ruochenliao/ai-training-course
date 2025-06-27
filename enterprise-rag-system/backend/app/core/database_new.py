"""
数据库配置和连接管理 - SQLAlchemy 2.0+ 重构版
严格按照技术栈要求：MySQL 8.0+ + SQLAlchemy 2.0+ + Alembic
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from app.core.config import settings
from loguru import logger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0+ 声明式基类"""
    pass


class DatabaseManager:
    """数据库管理器 - 单例模式"""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return
            
        try:
            # 创建异步引擎 - MySQL 8.0+ 配置
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                # 连接池配置
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                # MySQL 8.0+ 优化
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                },
                echo=settings.DEBUG,  # 开发环境显示SQL
            )
            
            # 创建会话工厂
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            self._initialized = True
            logger.info("MySQL 8.0+ 数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话 - 上下文管理器"""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入 - 获取数据库会话"""
    async with db_manager.get_session() as session:
        yield session


async def init_database():
    """初始化数据库连接 - 应用启动时调用"""
    await db_manager.initialize()


async def close_database():
    """关闭数据库连接 - 应用关闭时调用"""
    await db_manager.close()


async def check_database_health() -> bool:
    """检查数据库健康状态"""
    return await db_manager.health_check()


# 数据库事务装饰器
def transactional(func):
    """数据库事务装饰器"""
    async def wrapper(*args, **kwargs):
        async with db_manager.get_session() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    return wrapper


# Alembic 配置
def get_alembic_config():
    """获取Alembic配置"""
    from alembic.config import Config
    from alembic import command
    
    # Alembic配置文件路径
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+aiomysql", ""))
    
    return alembic_cfg


async def run_migrations():
    """运行数据库迁移"""
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        logger.info("数据库迁移完成")
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        raise


# 数据库连接事件监听器
@event.listens_for(DatabaseManager.engine, "connect")
def set_mysql_pragma(dbapi_connection, connection_record):
    """设置MySQL连接参数"""
    with dbapi_connection.cursor() as cursor:
        # 设置字符集
        cursor.execute("SET NAMES utf8mb4")
        # 设置时区
        cursor.execute("SET time_zone = '+00:00'")
        # 设置SQL模式
        cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")


# 数据库连接池监控
class DatabaseMetrics:
    """数据库连接池指标监控"""
    
    @staticmethod
    def get_pool_status():
        """获取连接池状态"""
        if not db_manager.engine:
            return None
            
        pool = db_manager.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    @staticmethod
    async def log_pool_status():
        """记录连接池状态"""
        status = DatabaseMetrics.get_pool_status()
        if status:
            logger.info(f"数据库连接池状态: {status}")


# 数据库备份和恢复
class DatabaseBackup:
    """数据库备份和恢复工具"""
    
    @staticmethod
    async def create_backup(backup_path: str):
        """创建数据库备份"""
        try:
            import subprocess
            
            # 从DATABASE_URL解析连接信息
            url_parts = settings.DATABASE_URL.replace("mysql+aiomysql://", "").split("@")
            user_pass = url_parts[0].split(":")
            host_db = url_parts[1].split("/")
            
            user = user_pass[0]
            password = user_pass[1]
            host = host_db[0].split(":")[0]
            port = host_db[0].split(":")[1] if ":" in host_db[0] else "3306"
            database = host_db[1]
            
            # 执行mysqldump
            cmd = [
                "mysqldump",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                database
            ]
            
            with open(backup_path, "w") as f:
                subprocess.run(cmd, stdout=f, check=True)
                
            logger.info(f"数据库备份完成: {backup_path}")
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise
    
    @staticmethod
    async def restore_backup(backup_path: str):
        """恢复数据库备份"""
        try:
            import subprocess
            
            # 从DATABASE_URL解析连接信息
            url_parts = settings.DATABASE_URL.replace("mysql+aiomysql://", "").split("@")
            user_pass = url_parts[0].split(":")
            host_db = url_parts[1].split("/")
            
            user = user_pass[0]
            password = user_pass[1]
            host = host_db[0].split(":")[0]
            port = host_db[0].split(":")[1] if ":" in host_db[0] else "3306"
            database = host_db[1]
            
            # 执行mysql恢复
            cmd = [
                "mysql",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                database
            ]
            
            with open(backup_path, "r") as f:
                subprocess.run(cmd, stdin=f, check=True)
                
            logger.info(f"数据库恢复完成: {backup_path}")
            
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise
