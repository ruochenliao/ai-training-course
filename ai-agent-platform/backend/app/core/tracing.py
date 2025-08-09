# Copyright (c) 2025 左岚. All rights reserved.
"""
分布式追踪系统 - Jaeger集成
"""

# # Standard library imports
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import uuid

# # Local application imports
from app.core.config import settings

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Span类型枚举"""
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


@dataclass
class SpanContext:
    """Span上下文"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'baggage': self.baggage
        }


@dataclass
class Span:
    """追踪Span"""
    operation_name: str
    context: SpanContext
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    kind: SpanKind = SpanKind.INTERNAL
    status: str = "ok"
    
    def set_tag(self, key: str, value: Any):
        """设置标签"""
        self.tags[key] = value
    
    def set_baggage(self, key: str, value: str):
        """设置行李"""
        self.context.baggage[key] = value
    
    def log(self, message: str, level: str = "info", **kwargs):
        """添加日志"""
        log_entry = {
            'timestamp': time.time(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logs.append(log_entry)
    
    def finish(self, end_time: Optional[float] = None):
        """结束Span"""
        self.end_time = end_time or time.time()
    
    def duration(self) -> float:
        """获取持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'operation_name': self.operation_name,
            'trace_id': self.context.trace_id,
            'span_id': self.context.span_id,
            'parent_span_id': self.context.parent_span_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration(),
            'tags': self.tags,
            'logs': self.logs,
            'kind': self.kind.value,
            'status': self.status
        }


class TracingManager:
    """分布式追踪管理器"""
    
    def __init__(self):
        self._local = threading.local()
        self._spans: Dict[str, Span] = {}
        self._traces: Dict[str, List[Span]] = {}
        self._samplers: List[Callable[[str], bool]] = []
        self._reporters: List[Callable[[Span], None]] = []
        self._enabled = settings.ENABLE_METRICS
        
        # 默认采样器 - 100%采样
        self.add_sampler(lambda operation_name: True)
        
        # 默认报告器 - 日志输出
        self.add_reporter(self._log_reporter)
    
    def add_sampler(self, sampler: Callable[[str], bool]):
        """添加采样器"""
        self._samplers.append(sampler)
    
    def add_reporter(self, reporter: Callable[[Span], None]):
        """添加报告器"""
        self._reporters.append(reporter)
    
    def _should_sample(self, operation_name: str) -> bool:
        """判断是否应该采样"""
        if not self._enabled:
            return False
        
        for sampler in self._samplers:
            if not sampler(operation_name):
                return False
        return True
    
    def _generate_trace_id(self) -> str:
        """生成追踪ID"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_span_id(self) -> str:
        """生成SpanID"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def start_span(self, operation_name: str, 
                   parent_context: Optional[SpanContext] = None,
                   kind: SpanKind = SpanKind.INTERNAL,
                   tags: Optional[Dict[str, Any]] = None) -> Optional[Span]:
        """开始一个新的Span"""
        if not self._should_sample(operation_name):
            return None
        
        # 创建Span上下文
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
            baggage = parent_context.baggage.copy()
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
            baggage = {}
        
        span_id = self._generate_span_id()
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=baggage
        )
        
        # 创建Span
        span = Span(
            operation_name=operation_name,
            context=context,
            start_time=time.time(),
            kind=kind
        )
        
        # 设置标签
        if tags:
            span.tags.update(tags)
        
        # 设置默认标签
        span.set_tag('component', 'ai-platform')
        span.set_tag('version', settings.VERSION)
        
        # 存储Span
        self._spans[span_id] = span
        
        if trace_id not in self._traces:
            self._traces[trace_id] = []
        self._traces[trace_id].append(span)
        
        # 设置当前Span
        self._set_current_span(span)
        
        logger.debug(f"开始Span: {operation_name} (trace_id: {trace_id}, span_id: {span_id})")
        return span
    
    def finish_span(self, span: Span):
        """结束Span"""
        if not span:
            return
        
        span.finish()
        
        # 报告Span
        for reporter in self._reporters:
            try:
                reporter(span)
            except Exception as e:
                logger.error(f"报告Span失败: {e}")
        
        # 清理当前Span
        current_span = self._get_current_span()
        if current_span and current_span.context.span_id == span.context.span_id:
            self._set_current_span(None)
        
        logger.debug(f"结束Span: {span.operation_name} (duration: {span.duration():.3f}s)")
    
    def _get_current_span(self) -> Optional[Span]:
        """获取当前Span"""
        return getattr(self._local, 'current_span', None)
    
    def _set_current_span(self, span: Optional[Span]):
        """设置当前Span"""
        self._local.current_span = span
    
    def get_current_context(self) -> Optional[SpanContext]:
        """获取当前上下文"""
        current_span = self._get_current_span()
        return current_span.context if current_span else None
    
    @contextmanager
    def trace(self, operation_name: str, 
              kind: SpanKind = SpanKind.INTERNAL,
              tags: Optional[Dict[str, Any]] = None):
        """追踪上下文管理器"""
        parent_context = self.get_current_context()
        span = self.start_span(operation_name, parent_context, kind, tags)
        
        try:
            yield span
        except Exception as e:
            if span:
                span.set_tag('error', True)
                span.set_tag('error.kind', type(e).__name__)
                span.set_tag('error.message', str(e))
                span.status = "error"
                span.log(f"异常: {e}", level="error")
            raise
        finally:
            if span:
                self.finish_span(span)
    
    def inject_context(self, context: SpanContext, carrier: Dict[str, str]):
        """注入上下文到载体"""
        carrier['x-trace-id'] = context.trace_id
        carrier['x-span-id'] = context.span_id
        if context.parent_span_id:
            carrier['x-parent-span-id'] = context.parent_span_id
        
        # 注入行李
        for key, value in context.baggage.items():
            carrier[f'x-baggage-{key}'] = value
    
    def extract_context(self, carrier: Dict[str, str]) -> Optional[SpanContext]:
        """从载体提取上下文"""
        trace_id = carrier.get('x-trace-id')
        span_id = carrier.get('x-span-id')
        
        if not trace_id or not span_id:
            return None
        
        parent_span_id = carrier.get('x-parent-span-id')
        
        # 提取行李
        baggage = {}
        for key, value in carrier.items():
            if key.startswith('x-baggage-'):
                baggage_key = key[10:]  # 移除 'x-baggage-' 前缀
                baggage[baggage_key] = value
        
        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=baggage
        )
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """获取追踪信息"""
        return self._traces.get(trace_id, [])
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """获取Span"""
        return self._spans.get(span_id)
    
    def _log_reporter(self, span: Span):
        """日志报告器"""
        logger.info(
            f"Span完成: {span.operation_name}",
            extra={
                'trace_id': span.context.trace_id,
                'span_id': span.context.span_id,
                'parent_span_id': span.context.parent_span_id,
                'duration_ms': round(span.duration() * 1000, 2),
                'tags': span.tags,
                'status': span.status
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取追踪统计信息"""
        return {
            'total_traces': len(self._traces),
            'total_spans': len(self._spans),
            'enabled': self._enabled,
            'samplers_count': len(self._samplers),
            'reporters_count': len(self._reporters)
        }
    
    def cleanup_old_traces(self, max_traces: int = 1000):
        """清理旧的追踪数据"""
        if len(self._traces) > max_traces:
            # 保留最新的追踪
            sorted_traces = sorted(
                self._traces.items(),
                key=lambda x: max(span.start_time for span in x[1]),
                reverse=True
            )
            
            # 删除旧的追踪
            for trace_id, spans in sorted_traces[max_traces:]:
                del self._traces[trace_id]
                for span in spans:
                    if span.context.span_id in self._spans:
                        del self._spans[span.context.span_id]
            
            logger.info(f"清理了 {len(sorted_traces) - max_traces} 个旧追踪")


def trace_function(operation_name: Optional[str] = None, 
                  kind: SpanKind = SpanKind.INTERNAL,
                  tags: Optional[Dict[str, Any]] = None):
    """函数追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracing_manager.trace(op_name, kind, tags) as span:
                if span:
                    span.set_tag('function.name', func.__name__)
                    span.set_tag('function.module', func.__module__)
                
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_async_function(operation_name: Optional[str] = None,
                        kind: SpanKind = SpanKind.INTERNAL,
                        tags: Optional[Dict[str, Any]] = None):
    """异步函数追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracing_manager.trace(op_name, kind, tags) as span:
                if span:
                    span.set_tag('function.name', func.__name__)
                    span.set_tag('function.module', func.__module__)
                    span.set_tag('async', True)
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 全局追踪管理器实例
tracing_manager = TracingManager()
