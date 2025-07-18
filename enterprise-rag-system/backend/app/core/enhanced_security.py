"""
增强安全模块 - 第四阶段核心组件
包含高级安全功能：限流、审计、加密、威胁检测等
"""

import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
import redis
from sqlalchemy.orm import Session
from collections import defaultdict, deque
import re

from app.core import settings
from app.core.database import get_db
from app.models.user import User


# Redis连接（用于会话管理和限流）
try:
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True
    )
    redis_client.ping()  # 测试连接
except Exception as e:
    logger.warning(f"Redis连接失败: {e}")
    redis_client = None


class AdvancedRateLimiter:
    """高级限流器 - 支持多种限流策略"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_cache = defaultdict(lambda: deque())
        
    def sliding_window_limit(self, key: str, limit: int, window: int) -> bool:
        """滑动窗口限流"""
        if not self.redis:
            return self._local_sliding_window_limit(key, limit, window)
        
        try:
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # 移除过期的请求记录
            pipeline.zremrangebyscore(key, 0, now - window)
            # 添加当前请求
            pipeline.zadd(key, {str(now): now})
            # 获取当前窗口内的请求数
            pipeline.zcard(key)
            # 设置过期时间
            pipeline.expire(key, window)
            
            results = pipeline.execute()
            current_count = results[2]
            
            return current_count <= limit
            
        except Exception as e:
            logger.error(f"Redis限流检查失败: {e}")
            return self._local_sliding_window_limit(key, limit, window)
    
    def _local_sliding_window_limit(self, key: str, limit: int, window: int) -> bool:
        """本地滑动窗口限流（Redis不可用时的备选方案）"""
        now = time.time()
        requests = self.local_cache[key]
        
        # 移除过期请求
        while requests and requests[0] < now - window:
            requests.popleft()
        
        # 检查是否超过限制
        if len(requests) >= limit:
            return False
        
        # 添加当前请求
        requests.append(now)
        return True
    
    def token_bucket_limit(self, key: str, capacity: int, refill_rate: float) -> bool:
        """令牌桶限流"""
        if not self.redis:
            return True  # 简化处理
        
        try:
            now = time.time()
            bucket_key = f"bucket:{key}"
            
            # 获取当前令牌数和最后更新时间
            bucket_data = self.redis.hmget(bucket_key, 'tokens', 'last_update')
            
            if bucket_data[0] is None:
                # 初始化令牌桶
                tokens = capacity
                last_update = now
            else:
                tokens = float(bucket_data[0])
                last_update = float(bucket_data[1])
                
                # 计算需要添加的令牌数
                time_passed = now - last_update
                tokens_to_add = time_passed * refill_rate
                tokens = min(capacity, tokens + tokens_to_add)
            
            # 检查是否有足够的令牌
            if tokens >= 1:
                tokens -= 1
                # 更新令牌桶状态
                self.redis.hmset(bucket_key, {
                    'tokens': tokens,
                    'last_update': now
                })
                self.redis.expire(bucket_key, 3600)  # 1小时过期
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"令牌桶限流检查失败: {e}")
            return True


class ThreatDetector:
    """威胁检测器"""
    
    def __init__(self):
        # 恶意IP黑名单
        self.ip_blacklist: Set[str] = set()
        # 可疑行为模式
        self.suspicious_patterns = [
            r'(?i)(union|select|insert|delete|drop|create|alter|exec)',  # SQL注入
            r'(?i)(<script|javascript:|vbscript:|onload=|onerror=)',      # XSS
            r'(?i)(\.\.\/|\.\.\\|\/etc\/|\/proc\/|\/sys\/)',             # 路径遍历
            r'(?i)(cmd\.exe|powershell|bash|sh|nc\.exe)',                # 命令注入
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.suspicious_patterns]
        
        # 异常行为计数
        self.anomaly_counter = defaultdict(int)
    
    def detect_malicious_input(self, input_data: str) -> Dict[str, Any]:
        """检测恶意输入"""
        threats = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(input_data):
                threat_types = ['SQL注入', 'XSS攻击', '路径遍历', '命令注入']
                threats.append({
                    'type': threat_types[i],
                    'pattern': self.suspicious_patterns[i],
                    'severity': 'high'
                })
        
        return {
            'is_malicious': len(threats) > 0,
            'threats': threats,
            'risk_score': len(threats) * 25  # 每个威胁25分
        }
    
    def detect_anomalous_behavior(self, user_id: int, action: str, ip: str) -> bool:
        """检测异常行为"""
        # 检查IP是否在黑名单中
        if ip in self.ip_blacklist:
            return True
        
        # 检查用户行为频率
        user_key = f"user_behavior:{user_id}:{action}"
        self.anomaly_counter[user_key] += 1
        
        # 如果某个用户在短时间内执行相同操作过多次，标记为异常
        if self.anomaly_counter[user_key] > 100:  # 阈值可配置
            logger.warning(f"检测到用户{user_id}异常行为: {action}")
            return True
        
        return False
    
    def add_to_blacklist(self, ip: str):
        """添加IP到黑名单"""
        self.ip_blacklist.add(ip)
        logger.info(f"IP {ip} 已添加到黑名单")
    
    def remove_from_blacklist(self, ip: str):
        """从黑名单移除IP"""
        self.ip_blacklist.discard(ip)
        logger.info(f"IP {ip} 已从黑名单移除")


class SecurityAuditor:
    """安全审计器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.audit_buffer = []
        self.buffer_size = 100
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[int],
        ip_address: str,
        details: Dict[str, Any],
        severity: str = "info"
    ):
        """记录安全事件"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details,
            'severity': severity
        }
        
        # 添加到缓冲区
        self.audit_buffer.append(event)
        
        # 如果缓冲区满了，批量写入
        if len(self.audit_buffer) >= self.buffer_size:
            self._flush_audit_buffer()
        
        # 记录到日志
        logger.info(f"安全事件: {event_type} - 用户{user_id} - IP{ip_address} - {severity}")
    
    def _flush_audit_buffer(self):
        """刷新审计缓冲区"""
        if not self.audit_buffer:
            return
        
        try:
            if self.redis:
                # 写入Redis
                for event in self.audit_buffer:
                    self.redis.lpush('security_audit_log', json.dumps(event))
                    self.redis.ltrim('security_audit_log', 0, 9999)  # 保留最近10000条
            
            # 写入文件（备份）
            with open('security_audit.log', 'a', encoding='utf-8') as f:
                for event in self.audit_buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            self.audit_buffer.clear()
            
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")
    
    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取安全事件"""
        try:
            if self.redis:
                events = self.redis.lrange('security_audit_log', 0, limit - 1)
                return [json.loads(event) for event in events]
            else:
                # 从文件读取
                events = []
                try:
                    with open('security_audit.log', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:
                            events.append(json.loads(line.strip()))
                except FileNotFoundError:
                    pass
                return events
        except Exception as e:
            logger.error(f"获取安全事件失败: {e}")
            return []


class DataSanitizer:
    """数据清理器"""
    
    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """清理输入数据"""
        if isinstance(data, str):
            return DataSanitizer._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: DataSanitizer.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataSanitizer.sanitize_input(item) for item in data]
        else:
            return data
    
    @staticmethod
    def _sanitize_string(text: str) -> str:
        """清理字符串"""
        # HTML转义
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#x27;')
        text = text.replace('&', '&amp;')
        
        # 移除控制字符
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # 限制长度
        if len(text) > 10000:  # 可配置
            text = text[:10000]
        
        return text
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        score = 0
        feedback = []
        
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("密码长度至少8位")
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("需要包含小写字母")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("需要包含大写字母")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("需要包含数字")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("需要包含特殊字符")
        
        strength_levels = ["很弱", "弱", "一般", "强", "很强"]
        strength = strength_levels[min(score, 4)]
        
        return {
            'score': score,
            'strength': strength,
            'is_strong': score >= 4,
            'feedback': feedback
        }


class SessionManager:
    """会话管理器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.session_timeout = 3600  # 1小时
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """创建会话"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        if self.redis:
            self.redis.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session_data)
            )
        
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        if not self.redis:
            return None
        
        try:
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return None
            
            session = json.loads(session_data)
            
            # 检查IP地址是否匹配（可选，根据安全需求）
            if getattr(settings, 'STRICT_SESSION_IP_CHECK', False):
                if session['ip_address'] != ip_address:
                    logger.warning(f"会话IP不匹配: {session['ip_address']} vs {ip_address}")
                    return None
            
            # 更新最后活动时间
            session['last_activity'] = datetime.utcnow().isoformat()
            self.redis.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session)
            )
            
            return session
            
        except Exception as e:
            logger.error(f"会话验证失败: {e}")
            return None
    
    def destroy_session(self, session_id: str):
        """销毁会话"""
        if self.redis:
            self.redis.delete(f"session:{session_id}")


# 全局实例
rate_limiter = AdvancedRateLimiter(redis_client)
threat_detector = ThreatDetector()
security_auditor = SecurityAuditor(redis_client)
data_sanitizer = DataSanitizer()
session_manager = SessionManager(redis_client)


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def security_middleware(request: Request):
    """安全中间件"""
    ip_address = get_client_ip(request)
    
    # 威胁检测
    if threat_detector.detect_anomalous_behavior(0, "request", ip_address):
        security_auditor.log_security_event(
            "suspicious_request",
            None,
            ip_address,
            {"path": str(request.url.path), "method": request.method},
            "warning"
        )
    
    # 输入验证
    if request.method in ["POST", "PUT", "PATCH"]:
        # 这里可以添加请求体的威胁检测
        pass
    
    return True
