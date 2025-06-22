"""
API限流和安全服务
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

import redis.asyncio as redis
from app.core.config import settings
from loguru import logger

from app.core.exceptions import RateLimitException, SecurityException


class LimitType(Enum):
    """限流类型"""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    CONCURRENT = "concurrent"


class SecurityThreatLevel(Enum):
    """安全威胁级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitRule:
    """限流规则"""
    name: str
    limit: int
    window: int  # 时间窗口（秒）
    limit_type: LimitType
    scope: str = "global"  # global, user, ip, api_key
    enabled: bool = True


@dataclass
class SecurityEvent:
    """安全事件"""
    event_type: str
    threat_level: SecurityThreatLevel
    source_ip: str
    user_id: Optional[int] = None
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}


@dataclass
class RateLimitStatus:
    """限流状态"""
    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None


class RateLimitService:
    """API限流和安全服务类"""
    
    def __init__(self):
        """初始化限流服务"""
        self.redis_client = None
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_activities: Dict[str, List[datetime]] = {}
        
        # 默认限流规则
        self.default_rules = [
            RateLimitRule(
                name="api_per_minute",
                limit=settings.RATE_LIMIT_PER_MINUTE,
                window=60,
                limit_type=LimitType.PER_MINUTE,
                scope="user"
            ),
            RateLimitRule(
                name="api_per_hour",
                limit=settings.RATE_LIMIT_PER_HOUR,
                window=3600,
                limit_type=LimitType.PER_HOUR,
                scope="user"
            ),
            RateLimitRule(
                name="api_per_day",
                limit=settings.RATE_LIMIT_PER_DAY,
                window=86400,
                limit_type=LimitType.PER_DAY,
                scope="user"
            ),
            RateLimitRule(
                name="ip_per_minute",
                limit=100,
                window=60,
                limit_type=LimitType.PER_MINUTE,
                scope="ip"
            ),
            RateLimitRule(
                name="concurrent_requests",
                limit=10,
                window=1,
                limit_type=LimitType.CONCURRENT,
                scope="user"
            )
        ]
        
        # 安全规则
        self.security_rules = {
            "max_failed_logins": 5,
            "failed_login_window": 300,  # 5分钟
            "max_requests_per_second": 20,
            "suspicious_patterns": [
                r"(?i)(union|select|insert|delete|drop|create|alter)",  # SQL注入
                r"(?i)(<script|javascript:|vbscript:|onload=|onerror=)",  # XSS
                r"(?i)(\.\.\/|\.\.\\|\/etc\/|\/proc\/|\/sys\/)",  # 路径遍历
            ]
        }
        
        logger.info("API限流和安全服务初始化完成")
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=3,  # 使用专门的数据库
                decode_responses=True
            )
            
            await self.redis_client.ping()
            logger.info("限流服务Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"限流服务Redis连接初始化失败: {e}")
            raise SecurityException(f"限流服务初始化失败: {e}")
    
    async def check_rate_limit(
        self,
        identifier: str,
        rule_name: str = "api_per_minute",
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> RateLimitStatus:
        """检查限流状态"""
        try:
            # 获取限流规则
            rule = self._get_rule(rule_name)
            if not rule or not rule.enabled:
                return RateLimitStatus(
                    allowed=True,
                    limit=0,
                    remaining=0,
                    reset_time=0
                )
            
            # 构建Redis键
            key = self._build_rate_limit_key(identifier, rule, user_id, ip_address)
            
            # 检查当前计数
            current_count = await self._get_current_count(key, rule)
            
            # 计算重置时间
            reset_time = int(time.time()) + rule.window
            
            # 检查是否超过限制
            if current_count >= rule.limit:
                retry_after = await self._get_retry_after(key, rule)
                return RateLimitStatus(
                    allowed=False,
                    limit=rule.limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            # 增加计数
            await self._increment_count(key, rule)
            
            return RateLimitStatus(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit - current_count - 1,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error(f"检查限流状态失败: {e}")
            # 出错时允许请求，但记录日志
            return RateLimitStatus(
                allowed=True,
                limit=0,
                remaining=0,
                reset_time=0
            )
    
    async def check_security_threats(
        self,
        request_data: Dict[str, Any],
        ip_address: str,
        user_id: Optional[int] = None
    ) -> List[SecurityEvent]:
        """检查安全威胁"""
        threats = []
        
        try:
            # 检查IP黑名单
            if await self._is_ip_blocked(ip_address):
                threats.append(SecurityEvent(
                    event_type="blocked_ip_access",
                    threat_level=SecurityThreatLevel.HIGH,
                    source_ip=ip_address,
                    user_id=user_id,
                    details={"reason": "IP在黑名单中"}
                ))
            
            # 检查请求频率
            if await self._check_request_frequency(ip_address):
                threats.append(SecurityEvent(
                    event_type="high_frequency_requests",
                    threat_level=SecurityThreatLevel.MEDIUM,
                    source_ip=ip_address,
                    user_id=user_id,
                    details={"reason": "请求频率过高"}
                ))
            
            # 检查恶意模式
            malicious_patterns = await self._check_malicious_patterns(request_data)
            for pattern in malicious_patterns:
                threats.append(SecurityEvent(
                    event_type="malicious_pattern_detected",
                    threat_level=SecurityThreatLevel.HIGH,
                    source_ip=ip_address,
                    user_id=user_id,
                    details={"pattern": pattern, "data": request_data}
                ))
            
            # 检查异常行为
            anomalies = await self._check_behavioral_anomalies(ip_address, user_id, request_data)
            threats.extend(anomalies)
            
            # 记录安全事件
            for threat in threats:
                await self._log_security_event(threat)
            
            return threats
            
        except Exception as e:
            logger.error(f"安全威胁检查失败: {e}")
            return []
    
    async def block_ip(
        self,
        ip_address: str,
        duration: int = 3600,
        reason: str = "安全威胁"
    ):
        """封禁IP地址"""
        try:
            key = f"blocked_ip:{ip_address}"
            await self.redis_client.setex(key, duration, reason)
            
            # 记录封禁事件
            await self._log_security_event(SecurityEvent(
                event_type="ip_blocked",
                threat_level=SecurityThreatLevel.HIGH,
                source_ip=ip_address,
                details={"reason": reason, "duration": duration}
            ))
            
            logger.warning(f"IP {ip_address} 已被封禁 {duration} 秒，原因: {reason}")
            
        except Exception as e:
            logger.error(f"封禁IP失败: {e}")
    
    async def unblock_ip(self, ip_address: str):
        """解封IP地址"""
        try:
            key = f"blocked_ip:{ip_address}"
            await self.redis_client.delete(key)
            
            logger.info(f"IP {ip_address} 已解封")
            
        except Exception as e:
            logger.error(f"解封IP失败: {e}")
    
    async def get_rate_limit_stats(
        self,
        identifier: str = None,
        time_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """获取限流统计"""
        try:
            stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "top_users": [],
                "top_ips": [],
                "rule_stats": {}
            }
            
            # 这里应该从Redis或数据库获取统计数据
            # 目前返回模拟数据
            
            return stats
            
        except Exception as e:
            logger.error(f"获取限流统计失败: {e}")
            return {}
    
    async def get_security_events(
        self,
        threat_level: SecurityThreatLevel = None,
        time_range: Tuple[datetime, datetime] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """获取安全事件"""
        try:
            # 这里应该从数据库获取安全事件
            # 目前返回模拟数据
            events = []
            
            return events
            
        except Exception as e:
            logger.error(f"获取安全事件失败: {e}")
            return []
    
    # 私有方法
    def _get_rule(self, rule_name: str) -> Optional[RateLimitRule]:
        """获取限流规则"""
        for rule in self.default_rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def _build_rate_limit_key(
        self,
        identifier: str,
        rule: RateLimitRule,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """构建限流键"""
        if rule.scope == "user" and user_id:
            return f"rate_limit:{rule.name}:user:{user_id}"
        elif rule.scope == "ip" and ip_address:
            return f"rate_limit:{rule.name}:ip:{ip_address}"
        else:
            return f"rate_limit:{rule.name}:global:{identifier}"
    
    async def _get_current_count(self, key: str, rule: RateLimitRule) -> int:
        """获取当前计数"""
        try:
            if rule.limit_type == LimitType.CONCURRENT:
                # 并发限制使用不同的逻辑
                return await self._get_concurrent_count(key)
            else:
                # 时间窗口限制
                count = await self.redis_client.get(key)
                return int(count) if count else 0
        except Exception:
            return 0
    
    async def _increment_count(self, key: str, rule: RateLimitRule):
        """增加计数"""
        try:
            if rule.limit_type == LimitType.CONCURRENT:
                # 并发限制不需要增加计数
                return
            
            # 使用管道确保原子性
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule.window)
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"增加限流计数失败: {e}")
    
    async def _get_retry_after(self, key: str, rule: RateLimitRule) -> int:
        """获取重试等待时间"""
        try:
            ttl = await self.redis_client.ttl(key)
            return max(ttl, 0)
        except Exception:
            return rule.window
    
    async def _get_concurrent_count(self, key: str) -> int:
        """获取并发计数"""
        try:
            # 并发限制的实现
            # 这里需要更复杂的逻辑来跟踪活跃请求
            return 0
        except Exception:
            return 0
    
    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """检查IP是否被封禁"""
        try:
            key = f"blocked_ip:{ip_address}"
            result = await self.redis_client.get(key)
            return result is not None
        except Exception:
            return False
    
    async def _check_request_frequency(self, ip_address: str) -> bool:
        """检查请求频率"""
        try:
            key = f"request_freq:{ip_address}"
            current_time = int(time.time())
            
            # 使用滑动窗口检查请求频率
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - 60)  # 移除1分钟前的记录
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, 60)
            
            results = await pipe.execute()
            request_count = results[2]
            
            return request_count > self.security_rules["max_requests_per_second"] * 60
            
        except Exception as e:
            logger.error(f"检查请求频率失败: {e}")
            return False
    
    async def _check_malicious_patterns(self, request_data: Dict[str, Any]) -> List[str]:
        """检查恶意模式"""
        import re
        
        patterns = []
        request_str = json.dumps(request_data, ensure_ascii=False)
        
        for pattern in self.security_rules["suspicious_patterns"]:
            if re.search(pattern, request_str):
                patterns.append(pattern)
        
        return patterns
    
    async def _check_behavioral_anomalies(
        self,
        ip_address: str,
        user_id: Optional[int],
        request_data: Dict[str, Any]
    ) -> List[SecurityEvent]:
        """检查行为异常"""
        anomalies = []
        
        try:
            # 检查登录失败次数
            if user_id:
                failed_logins = await self._get_failed_login_count(user_id)
                if failed_logins > self.security_rules["max_failed_logins"]:
                    anomalies.append(SecurityEvent(
                        event_type="excessive_failed_logins",
                        threat_level=SecurityThreatLevel.MEDIUM,
                        source_ip=ip_address,
                        user_id=user_id,
                        details={"failed_count": failed_logins}
                    ))
            
            # 检查异常访问模式
            # 这里可以添加更多的异常检测逻辑
            
        except Exception as e:
            logger.error(f"检查行为异常失败: {e}")
        
        return anomalies
    
    async def _get_failed_login_count(self, user_id: int) -> int:
        """获取登录失败次数"""
        try:
            key = f"failed_login:{user_id}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception:
            return 0
    
    async def _log_security_event(self, event: SecurityEvent):
        """记录安全事件"""
        try:
            # 记录到Redis
            key = f"security_event:{int(event.timestamp.timestamp())}"
            event_data = {
                "event_type": event.event_type,
                "threat_level": event.threat_level.value,
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "details": json.dumps(event.details),
                "timestamp": event.timestamp.isoformat()
            }
            
            await self.redis_client.hset(key, mapping=event_data)
            await self.redis_client.expire(key, 86400 * 30)  # 保留30天
            
            # 如果是高威胁级别，立即告警
            if event.threat_level in [SecurityThreatLevel.HIGH, SecurityThreatLevel.CRITICAL]:
                await self._send_security_alert(event)
            
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")
    
    async def _send_security_alert(self, event: SecurityEvent):
        """发送安全告警"""
        try:
            # 这里应该集成告警系统
            logger.warning(f"安全告警: {event.event_type} - {event.threat_level.value} - {event.source_ip}")
            
        except Exception as e:
            logger.error(f"发送安全告警失败: {e}")


# 全局限流服务实例
rate_limit_service = RateLimitService()
