"""
知识库专用日志记录器
提供结构化的日志记录功能，支持不同级别的日志和事件跟踪
"""
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum

from app.settings.config import settings


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """日志分类"""
    KNOWLEDGE_BASE = "knowledge_base"
    FILE_PROCESSING = "file_processing"
    VECTOR_SEARCH = "vector_search"
    PERMISSION = "permission"
    BATCH_OPERATION = "batch_operation"
    API_REQUEST = "api_request"
    SYSTEM = "system"


class KnowledgeLogger:
    """知识库专用日志记录器"""
    
    def __init__(self, name: str = "knowledge"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"knowledge.{self.name}")
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = Path(settings.BASE_DIR) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            log_dir / f"knowledge_{self.name}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 错误文件处理器
        error_handler = logging.FileHandler(
            log_dir / f"knowledge_{self.name}_error.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _format_log_data(
        self,
        message: str,
        category: LogCategory,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """格式化日志数据"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "message": message,
            "user_id": user_id,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "action": action,
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        return log_data
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """记录日志"""
        log_data = self._format_log_data(
            message, category, user_id, resource_id, 
            resource_type, action, extra_data
        )
        
        if exception:
            log_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }
        
        log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    # 业务相关的日志方法
    
    def log_knowledge_base_created(self, user_id: int, kb_id: int, kb_name: str):
        """记录知识库创建"""
        self.info(
            f"知识库创建成功: {kb_name}",
            category=LogCategory.KNOWLEDGE_BASE,
            user_id=user_id,
            resource_id=kb_id,
            resource_type="knowledge_base",
            action="create",
            extra_data={"knowledge_base_name": kb_name}
        )
    
    def log_knowledge_base_deleted(self, user_id: int, kb_id: int, kb_name: str):
        """记录知识库删除"""
        self.info(
            f"知识库删除成功: {kb_name}",
            category=LogCategory.KNOWLEDGE_BASE,
            user_id=user_id,
            resource_id=kb_id,
            resource_type="knowledge_base",
            action="delete",
            extra_data={"knowledge_base_name": kb_name}
        )
    
    def log_file_uploaded(self, user_id: int, file_id: int, filename: str, kb_id: int):
        """记录文件上传"""
        self.info(
            f"文件上传成功: {filename}",
            category=LogCategory.FILE_PROCESSING,
            user_id=user_id,
            resource_id=file_id,
            resource_type="knowledge_file",
            action="upload",
            extra_data={
                "filename": filename,
                "knowledge_base_id": kb_id
            }
        )
    
    def log_file_processing_started(self, file_id: int, filename: str):
        """记录文件处理开始"""
        self.info(
            f"文件处理开始: {filename}",
            category=LogCategory.FILE_PROCESSING,
            resource_id=file_id,
            resource_type="knowledge_file",
            action="process_start",
            extra_data={"filename": filename}
        )
    
    def log_file_processing_completed(self, file_id: int, filename: str, chunk_count: int):
        """记录文件处理完成"""
        self.info(
            f"文件处理完成: {filename}, 分块数: {chunk_count}",
            category=LogCategory.FILE_PROCESSING,
            resource_id=file_id,
            resource_type="knowledge_file",
            action="process_complete",
            extra_data={
                "filename": filename,
                "chunk_count": chunk_count
            }
        )
    
    def log_file_processing_failed(self, file_id: int, filename: str, error: str):
        """记录文件处理失败"""
        self.error(
            f"文件处理失败: {filename} - {error}",
            category=LogCategory.FILE_PROCESSING,
            resource_id=file_id,
            resource_type="knowledge_file",
            action="process_failed",
            extra_data={
                "filename": filename,
                "error": error
            }
        )
    
    def log_search_query(self, user_id: int, query: str, kb_ids: list, result_count: int):
        """记录搜索查询"""
        self.info(
            f"搜索查询: {query}, 结果数: {result_count}",
            category=LogCategory.VECTOR_SEARCH,
            user_id=user_id,
            action="search",
            extra_data={
                "query": query,
                "knowledge_base_ids": kb_ids,
                "result_count": result_count
            }
        )
    
    def log_permission_denied(self, user_id: int, resource_type: str, resource_id: int, action: str):
        """记录权限拒绝"""
        self.warning(
            f"权限拒绝: 用户 {user_id} 无权限对 {resource_type}:{resource_id} 执行 {action}",
            category=LogCategory.PERMISSION,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action=action
        )
    
    def log_batch_operation(self, user_id: int, operation: str, total: int, success: int, failed: int):
        """记录批量操作"""
        self.info(
            f"批量{operation}完成: 总数 {total}, 成功 {success}, 失败 {failed}",
            category=LogCategory.BATCH_OPERATION,
            user_id=user_id,
            action=f"batch_{operation}",
            extra_data={
                "operation": operation,
                "total_count": total,
                "success_count": success,
                "failed_count": failed
            }
        )
    
    def log_api_request(self, user_id: int, method: str, path: str, status_code: int, duration: float):
        """记录API请求"""
        self.info(
            f"API请求: {method} {path} - {status_code} ({duration:.3f}s)",
            category=LogCategory.API_REQUEST,
            user_id=user_id,
            action="api_request",
            extra_data={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration": duration
            }
        )
    
    def log_system_event(self, event: str, details: Dict[str, Any]):
        """记录系统事件"""
        self.info(
            f"系统事件: {event}",
            category=LogCategory.SYSTEM,
            action="system_event",
            extra_data={
                "event": event,
                "details": details
            }
        )


# 创建不同模块的日志记录器实例
knowledge_base_logger = KnowledgeLogger("base")
file_processing_logger = KnowledgeLogger("file_processing")
vector_search_logger = KnowledgeLogger("vector_search")
permission_logger = KnowledgeLogger("permission")
batch_operation_logger = KnowledgeLogger("batch_operation")
api_logger = KnowledgeLogger("api")
system_logger = KnowledgeLogger("system")


def get_logger(module: str = "base") -> KnowledgeLogger:
    """
    获取指定模块的日志记录器
    
    Args:
        module: 模块名称
        
    Returns:
        日志记录器实例
    """
    loggers = {
        "base": knowledge_base_logger,
        "file_processing": file_processing_logger,
        "vector_search": vector_search_logger,
        "permission": permission_logger,
        "batch_operation": batch_operation_logger,
        "api": api_logger,
        "system": system_logger
    }
    
    return loggers.get(module, knowledge_base_logger)
