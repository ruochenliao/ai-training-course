"""
数据库会话管理
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
import pymysql
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """
    如果数据库不存在则创建数据库
    """
    try:
        # 解析数据库URL获取连接信息
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
        raise


# 确保数据库存在
create_database_if_not_exists()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG  # 在调试模式下显示SQL语句
)

# 创建会话工厂
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
        from app.db.base import Base
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def check_db_connection() -> bool:
    """
    检查数据库连接
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False
