"""
错误监控和统计模块
"""

import time
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict

from loguru import logger
from .error_codes import ErrorCode, ErrorMessages


@dataclass
class ErrorMetric:
    """错误指标数据类"""
    error_code: str
    count: int
    last_occurrence: float
    first_occurrence: float
    avg_response_time: float
    paths: List[str]
    user_agents: List[str]
    client_ips: List[str]


class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self, max_history: int = 1000, time_window: int = 3600):
        self.max_history = max_history
        self.time_window = time_window  # 时间窗口（秒）
        
        # 错误统计
        self.error_counts = defaultdict(int)
        self.error_history = deque(maxlen=max_history)
        self.error_details = defaultdict(lambda: {
            "count": 0,
            "last_occurrence": 0,
            "first_occurrence": 0,
            "response_times": deque(maxlen=100),
            "paths": set(),
            "user_agents": set(),
            "client_ips": set(),
        })
        
        # 性能指标
        self.response_times = deque(maxlen=1000)
        self.request_counts = defaultdict(int)
        
        # 告警配置
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% 错误率
            "response_time_p95": 2.0,  # 95分位响应时间2秒
            "consecutive_errors": 10,  # 连续错误次数
        }
        
        # 告警状态
        self.alert_states = defaultdict(bool)
        self.last_alert_time = defaultdict(float)
        
    def record_error(
        self,
        error_code: str,
        path: str,
        method: str,
        response_time: float = 0,
        user_agent: str = None,
        client_ip: str = None,
        request_id: str = None,
    ):
        """记录错误"""
        current_time = time.time()
        
        # 更新错误计数
        self.error_counts[error_code] += 1
        
        # 记录错误历史
        error_record = {
            "timestamp": current_time,
            "error_code": error_code,
            "path": path,
            "method": method,
            "response_time": response_time,
            "user_agent": user_agent,
            "client_ip": client_ip,
            "request_id": request_id,
        }
        self.error_history.append(error_record)
        
        # 更新错误详情
        details = self.error_details[error_code]
        details["count"] += 1
        details["last_occurrence"] = current_time
        if details["first_occurrence"] == 0:
            details["first_occurrence"] = current_time
        
        if response_time > 0:
            details["response_times"].append(response_time)
        
        details["paths"].add(path)
        if user_agent:
            details["user_agents"].add(user_agent)
        if client_ip:
            details["client_ips"].add(client_ip)
        
        # 检查告警条件
        self._check_alerts(error_code, current_time)
        
    def record_request(self, path: str, method: str, response_time: float, status_code: int):
        """记录请求"""
        current_time = time.time()
        
        # 记录响应时间
        self.response_times.append({
            "timestamp": current_time,
            "response_time": response_time,
            "status_code": status_code,
            "path": path,
            "method": method,
        })
        
        # 记录请求计数
        key = f"{method}:{path}"
        self.request_counts[key] += 1
        
    def get_error_statistics(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """获取错误统计"""
        if time_window is None:
            time_window = self.time_window
            
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # 过滤时间窗口内的错误
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] >= cutoff_time
        ]
        
        # 统计错误
        error_stats = defaultdict(lambda: {
            "count": 0,
            "paths": set(),
            "methods": set(),
            "response_times": [],
        })
        
        for error in recent_errors:
            code = error["error_code"]
            error_stats[code]["count"] += 1
            error_stats[code]["paths"].add(error["path"])
            error_stats[code]["methods"].add(error["method"])
            if error["response_time"] > 0:
                error_stats[code]["response_times"].append(error["response_time"])
        
        # 转换为可序列化格式
        result = {}
        for code, stats in error_stats.items():
            avg_response_time = (
                sum(stats["response_times"]) / len(stats["response_times"])
                if stats["response_times"] else 0
            )
            
            result[code] = {
                "count": stats["count"],
                "paths": list(stats["paths"]),
                "methods": list(stats["methods"]),
                "avg_response_time": avg_response_time,
                "error_message": ErrorMessages.get_message(ErrorCode(code)) if hasattr(ErrorCode, code) else "Unknown error",
            }
        
        return {
            "time_window": time_window,
            "total_errors": len(recent_errors),
            "error_breakdown": result,
            "timestamp": current_time,
        }
        
    def get_performance_metrics(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """获取性能指标"""
        if time_window is None:
            time_window = self.time_window
            
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # 过滤时间窗口内的请求
        recent_requests = [
            req for req in self.response_times
            if req["timestamp"] >= cutoff_time
        ]
        
        if not recent_requests:
            return {
                "time_window": time_window,
                "total_requests": 0,
                "avg_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
                "error_rate": 0,
                "timestamp": current_time,
            }
        
        # 计算响应时间统计
        response_times = [req["response_time"] for req in recent_requests]
        response_times.sort()
        
        total_requests = len(recent_requests)
        avg_response_time = sum(response_times) / total_requests
        p95_index = int(total_requests * 0.95)
        p99_index = int(total_requests * 0.99)
        p95_response_time = response_times[p95_index] if p95_index < total_requests else response_times[-1]
        p99_response_time = response_times[p99_index] if p99_index < total_requests else response_times[-1]
        
        # 计算错误率
        error_requests = [req for req in recent_requests if req["status_code"] >= 400]
        error_rate = len(error_requests) / total_requests if total_requests > 0 else 0
        
        return {
            "time_window": time_window,
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 3),
            "p95_response_time": round(p95_response_time, 3),
            "p99_response_time": round(p99_response_time, 3),
            "error_rate": round(error_rate, 4),
            "error_count": len(error_requests),
            "timestamp": current_time,
        }
        
    def get_top_errors(self, limit: int = 10, time_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取最频繁的错误"""
        error_stats = self.get_error_statistics(time_window)
        
        # 按错误次数排序
        sorted_errors = sorted(
            error_stats["error_breakdown"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return [
            {
                "error_code": code,
                "count": stats["count"],
                "avg_response_time": stats["avg_response_time"],
                "paths": stats["paths"][:5],  # 只返回前5个路径
                "error_message": stats["error_message"],
            }
            for code, stats in sorted_errors[:limit]
        ]
        
    def _check_alerts(self, error_code: str, current_time: float):
        """检查告警条件"""
        # 检查连续错误
        recent_errors = [
            error for error in list(self.error_history)[-20:]  # 最近20个错误
            if error["error_code"] == error_code
        ]
        
        if len(recent_errors) >= self.alert_thresholds["consecutive_errors"]:
            self._trigger_alert("consecutive_errors", {
                "error_code": error_code,
                "count": len(recent_errors),
                "threshold": self.alert_thresholds["consecutive_errors"],
            })
        
        # 检查错误率
        metrics = self.get_performance_metrics(300)  # 5分钟窗口
        if metrics["error_rate"] > self.alert_thresholds["error_rate"]:
            self._trigger_alert("high_error_rate", {
                "error_rate": metrics["error_rate"],
                "threshold": self.alert_thresholds["error_rate"],
                "total_requests": metrics["total_requests"],
            })
        
        # 检查响应时间
        if metrics["p95_response_time"] > self.alert_thresholds["response_time_p95"]:
            self._trigger_alert("slow_response", {
                "p95_response_time": metrics["p95_response_time"],
                "threshold": self.alert_thresholds["response_time_p95"],
            })
            
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """触发告警"""
        current_time = time.time()
        
        # 防止重复告警（5分钟内不重复）
        if current_time - self.last_alert_time[alert_type] < 300:
            return
            
        self.last_alert_time[alert_type] = current_time
        self.alert_states[alert_type] = True
        
        logger.warning(
            f"告警触发: {alert_type}",
            extra={
                "alert_type": alert_type,
                "alert_data": data,
                "timestamp": current_time,
            }
        )
        
    def clear_old_data(self):
        """清理过期数据"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window * 2  # 保留2倍时间窗口的数据
        
        # 清理错误历史
        while self.error_history and self.error_history[0]["timestamp"] < cutoff_time:
            self.error_history.popleft()
            
        # 清理响应时间历史
        while self.response_times and self.response_times[0]["timestamp"] < cutoff_time:
            self.response_times.popleft()


# 全局错误监控实例
error_monitor = ErrorMonitor()


def get_error_monitor() -> ErrorMonitor:
    """获取错误监控实例"""
    return error_monitor
