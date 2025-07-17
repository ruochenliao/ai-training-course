from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.base import settings
from app.config.database import DatabaseConfig

# 创建数据库引擎
db_config = DatabaseConfig.get_engine_config()
engine = create_engine(**db_config)

# 创建会话工厂
session_config = DatabaseConfig.get_session_config()
SessionLocal = sessionmaker(bind=engine, **session_config)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """获取数据库会话（用于异步任务）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
