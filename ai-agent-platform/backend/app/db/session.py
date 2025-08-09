# Copyright (c) 2025 左岚. All rights reserved.
"""
数据库会话管理 - 优化版本
"""
# # Standard library imports
import logging
from typing import Generator

# # Third-party imports
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

# # Local application imports
from app.core.config import settings
from app.core.database_pool import db_pool_manager

logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """
    如果数据库不存在则创建数据库
    """
    try:
        # 检查是否为SQLite数据库
        if settings.DATABASE_URL.startswith('sqlite'):
            logger.info("使用SQLite数据库，无需预创建")
            return

        # 解析数据库URL获取连接信息
        # # Standard library imports
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.DATABASE_URL)

        # 提取连接参数
        host = parsed.hostname
        port = parsed.port or 3306
        username = parsed.username
        password = parsed.password
        database_name = parsed.path.lstrip('/')

        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            charset='utf8mb4'
        )

        try:
            with connection.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute(f"SHOW DATABASES LIKE '{database_name}'")
                result = cursor.fetchone()

                if not result:
                    # 创建数据库
                    cursor.execute(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"数据库 '{database_name}' 创建成功")
                else:
                    logger.info(f"数据库 '{database_name}' 已存在")

            connection.commit()

        finally:
            connection.close()

    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        # 对于SQLite，这不是致命错误
        if not settings.DATABASE_URL.startswith('sqlite'):
            raise


# 确保数据库存在
create_database_if_not_exists()

# 根据数据库类型选择连接方式
if settings.DATABASE_URL.startswith('sqlite'):
    logger.info("使用SQLite数据库，采用传统连接方式")
    # SQLite使用传统连接方式
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
        echo=settings.DEBUG
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
else:
    # MySQL等其他数据库尝试使用优化的连接池
    try:
        db_pool_manager.initialize()
        engine = db_pool_manager.engine
        SessionLocal = db_pool_manager.SessionLocal
        logger.info("使用优化的数据库连接池")
    except Exception as e:
        logger.warning(f"连接池初始化失败，使用传统数据库连接: {e}")
        # 降级到传统连接方式
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import QueuePool

        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            echo=settings.DEBUG
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    创建所有表
    """
    try:
        # # Local application imports
        from app.db.base import Base
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def check_db_connection() -> bool:
    """
    检查数据库连接 - 使用优化的健康检查
    """
    try:
        health_result = db_pool_manager.health_check()
        return health_result.get('status') == 'healthy'
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
