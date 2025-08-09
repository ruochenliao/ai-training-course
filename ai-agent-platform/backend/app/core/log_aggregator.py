# Copyright (c) 2025 左岚. All rights reserved.
"""
日志聚合和分析系统
"""

# # Standard library imports
import asyncio
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import gzip
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

# # Local application imports
from app.core.simple_cache import cache_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """日志条目数据类"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    extra_data: Dict[str, Any]
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LogEntry':
        """从JSON字符串创建日志条目"""
        try:
            data = json.loads(json_str)
            return cls(
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                level=LogLevel(data.get('level', 'INFO')),
                logger_name=data.get('logger', 'unknown'),
                message=data.get('message', ''),
                module=data.get('module', ''),
                function=data.get('function', ''),
                line_number=data.get('lineno', 0),
                extra_data=data.get('extra', {})
            )
        except Exception as e:
            logger.error(f"解析日志条目失败: {e}")
            return None


class LogAggregator:
    """日志聚合器"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_files = {
            'app': self.log_dir / "app.log",
            'error': self.log_dir / "error.log",
            'access': self.log_dir / "access.log"
        }
        self._stats_cache_ttl = 300  # 5分钟缓存
    
    def read_log_file(self, log_type: str, lines: int = 1000) -> List[LogEntry]:
        """读取日志文件"""
        log_file = self.log_files.get(log_type)
        if not log_file or not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # 读取最后N行
                file_lines = f.readlines()
                recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        entry = LogEntry.from_json(line)
                        if entry:
                            entries.append(entry)
        
        except Exception as e:
            logger.error(f"读取日志文件失败 {log_type}: {e}")
        
        return entries
    
    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志统计信息"""
        cache_key = f"log_stats_{hours}h"
        cached_stats = cache_manager.get(cache_key, prefix="log_aggregator")
        
        if cached_stats:
            return cached_stats
        
        stats = self._calculate_log_stats(hours)
        cache_manager.set(cache_key, stats, ttl=self._stats_cache_ttl, prefix="log_aggregator")
        
        return stats
    
    def _calculate_log_stats(self, hours: int) -> Dict[str, Any]:
        """计算日志统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {
            'total_logs': 0,
            'level_distribution': defaultdict(int),
            'logger_distribution': defaultdict(int),
            'error_patterns': Counter(),
            'top_errors': [],
            'hourly_distribution': defaultdict(int),
            'performance_metrics': {
                'slow_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0
            }
        }
        
        # 分析所有日志文件
        for log_type in self.log_files.keys():
            entries = self.read_log_file(log_type, lines=10000)
            
            for entry in entries:
                if entry.timestamp < cutoff_time:
                    continue
                
                stats['total_logs'] += 1
                stats['level_distribution'][entry.level.value] += 1
                stats['logger_distribution'][entry.logger_name] += 1
                
                # 按小时分组
                hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
                stats['hourly_distribution'][hour_key] += 1
                
                # 错误分析
                if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                    error_pattern = self._extract_error_pattern(entry.message)
                    if error_pattern:
                        stats['error_patterns'][error_pattern] += 1
                
                # 性能指标分析
                if 'duration_ms' in entry.extra_data:
                    duration = entry.extra_data['duration_ms']
                    if duration > 1000:  # 超过1秒的请求
                        stats['performance_metrics']['slow_requests'] += 1
        
        # 计算错误率
        total_requests = stats['logger_distribution'].get('app.api', 0)
        total_errors = stats['level_distribution'].get('ERROR', 0) + stats['level_distribution'].get('CRITICAL', 0)
        
        if total_requests > 0:
            stats['performance_metrics']['error_rate'] = (total_errors / total_requests) * 100
        
        # 获取Top错误
        stats['top_errors'] = [
            {'pattern': pattern, 'count': count}
            for pattern, count in stats['error_patterns'].most_common(10)
        ]
        
        return dict(stats)
    
    def _extract_error_pattern(self, message: str) -> Optional[str]:
        """提取错误模式"""
        # 移除具体的数值、ID等变化的部分
        pattern = re.sub(r'\d+', 'N', message)
        pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', pattern)
        pattern = re.sub(r'\b\w+@\w+\.\w+\b', 'EMAIL', pattern)
        pattern = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', 'IP', pattern)
        
        return pattern[:100]  # 限制长度
    
    def search_logs(self, query: str, log_type: str = 'app', 
                   level: Optional[LogLevel] = None, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[LogEntry]:
        """搜索日志"""
        entries = self.read_log_file(log_type, lines=10000)
        results = []
        
        for entry in entries:
            # 时间过滤
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            # 级别过滤
            if level and entry.level != level:
                continue
            
            # 文本搜索
            if query.lower() in entry.message.lower() or query.lower() in str(entry.extra_data).lower():
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误分析报告"""
        cache_key = f"error_analysis_{hours}h"
        cached_analysis = cache_manager.get(cache_key, prefix="log_aggregator")
        
        if cached_analysis:
            return cached_analysis
        
        analysis = self._analyze_errors(hours)
        cache_manager.set(cache_key, analysis, ttl=self._stats_cache_ttl, prefix="log_aggregator")
        
        return analysis
    
    def _analyze_errors(self, hours: int) -> Dict[str, Any]:
        """分析错误日志"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        error_entries = self.read_log_file('error', lines=5000)
        
        analysis = {
            'total_errors': 0,
            'error_types': Counter(),
            'error_modules': Counter(),
            'error_timeline': defaultdict(int),
            'critical_errors': [],
            'recurring_errors': [],
            'error_trends': {}
        }
        
        for entry in error_entries:
            if entry.timestamp < cutoff_time:
                continue
            
            analysis['total_errors'] += 1
            
            # 错误类型统计
            error_type = entry.extra_data.get('error_type', 'Unknown')
            analysis['error_types'][error_type] += 1
            
            # 模块统计
            analysis['error_modules'][entry.module] += 1
            
            # 时间线统计
            hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
            analysis['error_timeline'][hour_key] += 1
            
            # 关键错误
            if entry.level == LogLevel.CRITICAL:
                analysis['critical_errors'].append({
                    'timestamp': entry.timestamp.isoformat(),
                    'message': entry.message,
                    'module': entry.module,
                    'extra': entry.extra_data
                })
        
        # 识别重复错误
        error_patterns = Counter()
        for entry in error_entries:
            if entry.timestamp >= cutoff_time:
                pattern = self._extract_error_pattern(entry.message)
                if pattern:
                    error_patterns[pattern] += 1
        
        # 重复错误（出现3次以上）
        analysis['recurring_errors'] = [
            {'pattern': pattern, 'count': count}
            for pattern, count in error_patterns.items()
            if count >= 3
        ]
        
        return dict(analysis)
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能报告"""
        cache_key = f"performance_report_{hours}h"
        cached_report = cache_manager.get(cache_key, prefix="log_aggregator")
        
        if cached_report:
            return cached_report
        
        report = self._analyze_performance(hours)
        cache_manager.set(cache_key, report, ttl=self._stats_cache_ttl, prefix="log_aggregator")
        
        return report
    
    def _analyze_performance(self, hours: int) -> Dict[str, Any]:
        """分析性能日志"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        access_entries = self.read_log_file('access', lines=10000)
        
        report = {
            'total_requests': 0,
            'avg_response_time': 0,
            'slow_requests': 0,
            'response_time_distribution': {
                '<100ms': 0,
                '100-500ms': 0,
                '500ms-1s': 0,
                '1-5s': 0,
                '>5s': 0
            },
            'status_code_distribution': Counter(),
            'endpoint_performance': defaultdict(list),
            'slowest_endpoints': []
        }
        
        total_duration = 0
        
        for entry in access_entries:
            if entry.timestamp < cutoff_time:
                continue
            
            duration_ms = entry.extra_data.get('duration_ms', 0)
            status_code = entry.extra_data.get('status_code', 200)
            endpoint = entry.extra_data.get('url', 'unknown')
            
            report['total_requests'] += 1
            total_duration += duration_ms
            
            # 响应时间分布
            if duration_ms < 100:
                report['response_time_distribution']['<100ms'] += 1
            elif duration_ms < 500:
                report['response_time_distribution']['100-500ms'] += 1
            elif duration_ms < 1000:
                report['response_time_distribution']['500ms-1s'] += 1
            elif duration_ms < 5000:
                report['response_time_distribution']['1-5s'] += 1
            else:
                report['response_time_distribution']['>5s'] += 1
            
            # 慢请求统计
            if duration_ms > 1000:
                report['slow_requests'] += 1
            
            # 状态码分布
            report['status_code_distribution'][str(status_code)] += 1
            
            # 端点性能
            report['endpoint_performance'][endpoint].append(duration_ms)
        
        # 计算平均响应时间
        if report['total_requests'] > 0:
            report['avg_response_time'] = total_duration / report['total_requests']
        
        # 最慢的端点
        endpoint_avg_times = {}
        for endpoint, times in report['endpoint_performance'].items():
            if times:
                endpoint_avg_times[endpoint] = sum(times) / len(times)
        
        report['slowest_endpoints'] = [
            {'endpoint': endpoint, 'avg_time_ms': avg_time, 'request_count': len(report['endpoint_performance'][endpoint])}
            for endpoint, avg_time in sorted(endpoint_avg_times.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return dict(report)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"删除旧日志文件: {log_file}")
            
            # 压缩旧日志
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < (datetime.now() - timedelta(days=7)).timestamp():
                    self._compress_log_file(log_file)
                    
        except Exception as e:
            logger.error(f"清理日志文件失败: {e}")
    
    def _compress_log_file(self, log_file: Path):
        """压缩日志文件"""
        try:
            compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            log_file.unlink()
            logger.info(f"压缩日志文件: {log_file} -> {compressed_file}")
            
        except Exception as e:
            logger.error(f"压缩日志文件失败 {log_file}: {e}")


# 全局日志聚合器实例
log_aggregator = LogAggregator()
