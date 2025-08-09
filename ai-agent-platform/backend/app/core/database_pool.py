# Copyright (c) 2025 左岚. All rights reserved.
"""
数据库连接池优化管理器
"""

# # Standard library imports
from contextlib import contextmanager
from datetime import datetime, timedelta
import logging
import threading
import time
from typing import Any, Dict, Generator, Optional

# # Third-party imports
import pymysql
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

# # Local application imports
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """数据库连接池管理器"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'checked_out': 0,
            'checked_in': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0,
            'query_count': 0,
            'slow_queries': 0,
            'total_query_time': 0.0,
            'avg_query_time': 0.0
        }
        self._slow_query_threshold = 1.0  # 慢查询阈值(秒)
        self._lock = threading.Lock()
        self._last_health_check = None
        self._health_status = 'unknown'
    
    def create_optimized_engine(self) -> Engine:
        """创建优化的数据库引擎"""
        try:
            # 根据数据库类型设置连接参数
            connect_args = {}

            if settings.DATABASE_URL.startswith('sqlite'):
                # SQLite连接参数
                connect_args = {
                    'check_same_thread': False,  # 允许多线程访问
                    'timeout': 30,  # 连接超时
                }
            elif settings.DATABASE_URL.startswith('mysql'):
                # MySQL连接参数
                connect_args = {
                    'charset': 'utf8mb4',
                    'autocommit': False,
                    'connect_timeout': 10,
                    'read_timeout': 30,
                    'write_timeout': 30,
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'max_allowed_packet': 16777216,  # 16MB
                }
            
            # 根据数据库类型创建引擎
            if settings.DATABASE_URL.startswith('sqlite'):
                # SQLite引擎配置
                engine = create_engine(
                    settings.DATABASE_URL,
                    poolclass=StaticPool,  # SQLite使用StaticPool
                    connect_args=connect_args,
                    echo=settings.DEBUG
                )
            else:
                # MySQL等其他数据库引擎配置
                engine = create_engine(
                    settings.DATABASE_URL,
                    poolclass=QueuePool,
                    pool_size=settings.DATABASE_POOL_SIZE,
                    max_overflow=settings.DATABASE_MAX_OVERFLOW,
                    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                    pool_recycle=settings.DATABASE_POOL_RECYCLE,
                    pool_pre_ping=True,  # 连接前ping检查
                    pool_reset_on_return='commit',  # 返回时重置连接
                    echo=False,  # 生产环境关闭SQL日志
                    echo_pool=settings.DEBUG,  # 调试模式显示连接池日志
                    connect_args=connect_args,
                    execution_options={
                        'isolation_level': 'READ_COMMITTED',
                        'autocommit': False
                    }
                )
            
            # 注册事件监听器
            self._register_event_listeners(engine)
            
            logger.info(f"数据库引擎创建成功 - 连接池大小: {settings.DATABASE_POOL_SIZE}, 最大溢出: {settings.DATABASE_MAX_OVERFLOW}")
            return engine
            
        except Exception as e:
            logger.error(f"数据库引擎创建失败: {e}")
            raise
    
    def _register_event_listeners(self, engine: Engine):
        """注册数据库事件监听器"""
        
        @event.listens_for(engine, "connect")
        def set_database_pragma(dbapi_connection, connection_record):
            """连接时设置数据库参数"""
            if settings.DATABASE_URL.startswith('sqlite'):
                # SQLite参数设置
                if hasattr(dbapi_connection, 'execute'):
                    dbapi_connection.execute('PRAGMA foreign_keys=ON')
                    dbapi_connection.execute('PRAGMA journal_mode=WAL')
                    dbapi_connection.execute('PRAGMA synchronous=NORMAL')
                    dbapi_connection.execute('PRAGMA temp_store=MEMORY')
                    dbapi_connection.execute('PRAGMA mmap_size=268435456')  # 256MB
            elif settings.DATABASE_URL.startswith('mysql'):
                # MySQL参数设置
                if hasattr(dbapi_connection, 'cursor'):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES'")
                    cursor.execute("SET SESSION innodb_lock_wait_timeout = 50")
                    cursor.execute("SET SESSION wait_timeout = 28800")
                    cursor.execute("SET SESSION interactive_timeout = 28800")
                    cursor.close()
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出时的统计"""
            with self._lock:
                self._pool_stats['checked_out'] += 1
                self._pool_stats['active_connections'] += 1
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入时的统计"""
            with self._lock:
                self._pool_stats['checked_in'] += 1
                self._pool_stats['active_connections'] = max(0, self._pool_stats['active_connections'] - 1)
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行前记录时间"""
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """查询执行后统计"""
            if hasattr(context, '_query_start_time'):
                query_time = time.time() - context._query_start_time
                with self._lock:
                    self._pool_stats['query_count'] += 1
                    self._pool_stats['total_query_time'] += query_time
                    self._pool_stats['avg_query_time'] = self._pool_stats['total_query_time'] / self._pool_stats['query_count']
                    
                    if query_time > self._slow_query_threshold:
                        self._pool_stats['slow_queries'] += 1
                        logger.warning(f"慢查询检测 ({query_time:.3f}s): {statement[:200]}...")
    
    def initialize(self):
        """初始化数据库连接池"""
        try:
            self.engine = self.create_optimized_engine()
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False  # 避免对象过期
            )
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        if not self.SessionLocal:
            raise RuntimeError("数据库连接池未初始化")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """获取数据库会话 - 用于依赖注入"""
        if not self.SessionLocal:
            raise RuntimeError("数据库连接池未初始化")
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        try:
            pool = self.engine.pool if self.engine else None
            if pool:
                with self._lock:
                    stats = self._pool_stats.copy()
                    stats.update({
                        'pool_size': pool.size(),
                        'checked_in_connections': pool.checkedin(),
                        'checked_out_connections': pool.checkedout(),
                        'overflow_connections': pool.overflow(),
                        'invalid_connections': pool.invalid(),
                        'pool_status': {
                            'size': pool.size(),
                            'checked_in': pool.checkedin(),
                            'checked_out': pool.checkedout(),
                            'overflow': pool.overflow(),
                            'invalid': pool.invalid()
                        }
                    })
                return stats
            else:
                return {'error': '连接池未初始化'}
        except Exception as e:
            logger.error(f"获取连接池统计失败: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """数据库健康检查"""
        try:
            start_time = time.time()
            
            with self.get_db_session() as session:
                # 执行简单查询测试连接
                result = session.execute(text("SELECT 1 as health_check"))
                result.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            self._last_health_check = datetime.now()
            self._health_status = 'healthy'
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'last_check': self._last_health_check.isoformat(),
                'pool_stats': self.get_pool_stats()
            }
            
        except Exception as e:
            self._health_status = 'unhealthy'
            logger.error(f"数据库健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def optimize_pool(self):
        """动态优化连接池"""
        try:
            stats = self.get_pool_stats()
            if 'pool_status' in stats:
                pool_status = stats['pool_status']
                
                # 检查连接池使用率
                usage_rate = pool_status['checked_out'] / max(pool_status['size'], 1)
                
                if usage_rate > 0.8:
                    logger.warning(f"连接池使用率过高: {usage_rate:.2%}")
                elif usage_rate < 0.2:
                    logger.info(f"连接池使用率较低: {usage_rate:.2%}")
                
                # 检查慢查询
                if stats.get('slow_queries', 0) > 10:
                    logger.warning(f"检测到 {stats['slow_queries']} 个慢查询")
                
                # 检查平均查询时间
                avg_time = stats.get('avg_query_time', 0)
                if avg_time > 0.5:
                    logger.warning(f"平均查询时间过长: {avg_time:.3f}s")
                    
        except Exception as e:
            logger.error(f"连接池优化检查失败: {e}")
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self._pool_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'idle_connections': 0,
                'checked_out': 0,
                'checked_in': 0,
                'pool_hits': 0,
                'pool_misses': 0,
                'connection_errors': 0,
                'query_count': 0,
                'slow_queries': 0,
                'total_query_time': 0.0,
                'avg_query_time': 0.0
            }
        logger.info("连接池统计信息已重置")
    
    def close(self):
        """关闭连接池"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("数据库连接池已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接池失败: {e}")


# 全局数据库连接池管理器
db_pool_manager = DatabasePoolManager()
