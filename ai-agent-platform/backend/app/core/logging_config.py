# Copyright (c) 2025 左岚. All rights reserved.
"""
结构化日志系统配置
"""

# # Standard library imports
from datetime import datetime
import json
import logging
import logging.config
from pathlib import Path
import sys
import traceback
from typing import Any, Dict, Optional

# # Third-party imports
import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
)
from structlog.stdlib import LoggerFactory

# # Local application imports
from app.core.config import settings

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class StructuredLogger:
    """结构化日志管理器"""
    
    def __init__(self):
        self.logger = None
        self._setup_structlog()
    
    def _setup_structlog(self):
        """配置structlog"""
        
        # 处理器链
        processors = [
            structlog.stdlib.filter_by_level,  # 按级别过滤
            structlog.stdlib.add_logger_name,  # 添加logger名称
            structlog.stdlib.add_log_level,    # 添加日志级别
            structlog.stdlib.PositionalArgumentsFormatter(),  # 格式化位置参数
            TimeStamper(fmt="iso"),            # 添加时间戳
            StackInfoRenderer(),               # 堆栈信息渲染
            structlog.processors.format_exc_info,  # 格式化异常信息
        ]
        
        # 根据环境选择渲染器
        if settings.ENVIRONMENT == "development":
            processors.append(ConsoleRenderer(colors=True))
        else:
            processors.append(JSONRenderer())
        
        # 配置structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=LoggerFactory(),
            context_class=dict,
            cache_logger_on_first_use=True,
        )
        
        # 配置标准库logging
        self._setup_stdlib_logging()
    
    def _setup_stdlib_logging(self):
        """配置标准库logging"""
        
        # 日志格式
        json_formatter = {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "logging.Formatter",
        }
        
        console_formatter = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
        
        # 处理器配置
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "console" if settings.ENVIRONMENT == "development" else "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": LOG_DIR / "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": LOG_DIR / "error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": LOG_DIR / "access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        }
        
        # 日志器配置
        loggers = {
            "": {  # 根日志器
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "app": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "app.api": {
                "level": "INFO",
                "handlers": ["console", "access_file"],
                "propagate": False,
            },
            "app.errors": {
                "level": "ERROR",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False,
            },
        }
        
        # 应用配置
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": json_formatter,
                "console": console_formatter,
            },
            "handlers": handlers,
            "loggers": loggers,
        }
        
        logging.config.dictConfig(config)
    
    def get_logger(self, name: str = None) -> structlog.BoundLogger:
        """获取结构化日志器"""
        return structlog.get_logger(name)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: structlog.BoundLogger, **context):
        self.logger = logger
        self.context = context
        self.bound_logger = None
    
    def __enter__(self):
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.bound_logger.error(
                "Exception in log context",
                exc_info=True,
                exception_type=exc_type.__name__,
                exception_message=str(exc_val)
            )


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger("app.api")
    
    def log_request(self, request, response, duration: float):
        """记录请求日志"""
        self.logger.info(
            "HTTP Request",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
            content_length=response.headers.get("content-length"),
        )
    
    def log_error(self, request, error: Exception):
        """记录错误日志"""
        self.logger.error(
            "HTTP Request Error",
            method=request.method,
            url=str(request.url),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
        )


class DatabaseLogger:
    """数据库日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger("app.database")
    
    def log_query(self, query: str, params: Any, duration: float, status: str = "success"):
        """记录数据库查询日志"""
        self.logger.info(
            "Database Query",
            query=query[:200] + "..." if len(query) > 200 else query,
            duration_ms=round(duration * 1000, 2),
            status=status,
            param_count=len(params) if params else 0,
        )
    
    def log_connection_event(self, event: str, details: Dict[str, Any] = None):
        """记录数据库连接事件"""
        self.logger.info(
            "Database Connection Event",
            event=event,
            details=details or {},
        )


class AIModelLogger:
    """AI模型日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger("app.ai_model")
    
    def log_request(self, model_name: str, prompt_length: int, response_length: int, 
                   duration: float, tokens_used: int = 0, status: str = "success"):
        """记录AI模型请求日志"""
        self.logger.info(
            "AI Model Request",
            model_name=model_name,
            prompt_length=prompt_length,
            response_length=response_length,
            duration_ms=round(duration * 1000, 2),
            tokens_used=tokens_used,
            status=status,
        )
    
    def log_error(self, model_name: str, error: Exception, context: Dict[str, Any] = None):
        """记录AI模型错误日志"""
        self.logger.error(
            "AI Model Error",
            model_name=model_name,
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
            traceback=traceback.format_exc(),
        )


class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger("app.security")
    
    def log_auth_event(self, event: str, user_id: Optional[str] = None, 
                      ip_address: Optional[str] = None, details: Dict[str, Any] = None):
        """记录认证事件"""
        self.logger.info(
            "Authentication Event",
            event=event,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {},
        )
    
    def log_security_incident(self, incident_type: str, severity: str, 
                            details: Dict[str, Any] = None):
        """记录安全事件"""
        self.logger.warning(
            "Security Incident",
            incident_type=incident_type,
            severity=severity,
            details=details or {},
        )


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger("app.performance")
    
    def log_slow_operation(self, operation: str, duration: float, threshold: float = 1.0,
                          details: Dict[str, Any] = None):
        """记录慢操作"""
        if duration > threshold:
            self.logger.warning(
                "Slow Operation Detected",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                threshold_ms=round(threshold * 1000, 2),
                details=details or {},
            )
    
    def log_resource_usage(self, cpu_percent: float, memory_percent: float, 
                          disk_percent: float):
        """记录资源使用情况"""
        self.logger.info(
            "Resource Usage",
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
        )


# 全局日志管理器实例
structured_logger = StructuredLogger()

# 专用日志记录器实例
request_logger = RequestLogger()
database_logger = DatabaseLogger()
ai_model_logger = AIModelLogger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """获取结构化日志器的便捷函数"""
    return structured_logger.get_logger(name)


def log_context(**context) -> LogContext:
    """创建日志上下文的便捷函数"""
    logger = get_logger()
    return LogContext(logger, **context)
