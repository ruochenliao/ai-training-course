"""
告警通知服务
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import json

from loguru import logger


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """告警类型"""
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"
    AI_SERVICE = "ai_service"
    DATABASE = "database"
    CACHE = "cache"


@dataclass
class Alert:
    """告警数据类"""
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    details: Dict[str, Any]
    timestamp: float
    source: str
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolved_by: Optional[str] = None
    notification_sent: bool = False


class AlertRule:
    """告警规则"""
    
    def __init__(
        self,
        name: str,
        alert_type: AlertType,
        level: AlertLevel,
        condition: Callable[[Dict[str, Any]], bool],
        message_template: str,
        cooldown: int = 300,  # 5分钟冷却期
        enabled: bool = True
    ):
        self.name = name
        self.alert_type = alert_type
        self.level = level
        self.condition = condition
        self.message_template = message_template
        self.cooldown = cooldown
        self.enabled = enabled
        self.last_triggered = 0


class AlertService:
    """告警服务"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[AlertRule] = []
        self.notification_handlers: List[Callable] = []
        
        # 初始化默认告警规则
        self._init_default_rules()
        
        # 统计信息
        self.stats = {
            "total_alerts": 0,
            "alerts_by_level": {},
            "alerts_by_type": {},
            "resolved_alerts": 0,
            "notifications_sent": 0,
        }
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        
        # 系统健康告警
        self.add_rule(AlertRule(
            name="database_unhealthy",
            alert_type=AlertType.DATABASE,
            level=AlertLevel.CRITICAL,
            condition=lambda data: data.get("database", {}).get("status") != "healthy",
            message_template="数据库连接异常: {details}",
            cooldown=60
        ))
        
        self.add_rule(AlertRule(
            name="redis_unhealthy",
            alert_type=AlertType.CACHE,
            level=AlertLevel.ERROR,
            condition=lambda data: data.get("redis", {}).get("status") != "healthy",
            message_template="Redis缓存服务异常: {details}",
            cooldown=60
        ))
        
        self.add_rule(AlertRule(
            name="ai_service_unhealthy",
            alert_type=AlertType.AI_SERVICE,
            level=AlertLevel.ERROR,
            condition=lambda data: data.get("ai_services", {}).get("status") != "healthy",
            message_template="AI服务异常: {details}",
            cooldown=120
        ))
        
        # 性能告警
        self.add_rule(AlertRule(
            name="high_error_rate",
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING,
            condition=lambda data: data.get("performance", {}).get("error_rate", 0) > 0.05,
            message_template="错误率过高: {error_rate:.2%}",
            cooldown=300
        ))
        
        self.add_rule(AlertRule(
            name="slow_response_time",
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING,
            condition=lambda data: data.get("performance", {}).get("p95_response_time", 0) > 2.0,
            message_template="响应时间过慢: P95={p95_response_time:.2f}s",
            cooldown=300
        ))
        
        # 缓存告警
        self.add_rule(AlertRule(
            name="low_cache_hit_rate",
            alert_type=AlertType.CACHE,
            level=AlertLevel.WARNING,
            condition=lambda data: data.get("cache", {}).get("hit_rate", 1.0) < 0.5,
            message_template="缓存命中率过低: {hit_rate:.2%}",
            cooldown=600
        ))
        
        # 业务告警
        self.add_rule(AlertRule(
            name="document_processing_failure",
            alert_type=AlertType.BUSINESS,
            level=AlertLevel.WARNING,
            condition=lambda data: data.get("document_metrics", {}).get("processing_success_rate", 1.0) < 0.8,
            message_template="文档处理成功率过低: {processing_success_rate:.2%}",
            cooldown=900
        ))
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules.append(rule)
        logger.info(f"添加告警规则: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        self.alert_rules = [rule for rule in self.alert_rules if rule.name != rule_name]
        logger.info(f"移除告警规则: {rule_name}")
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """添加通知处理器"""
        self.notification_handlers.append(handler)
    
    async def check_alerts(self, data: Dict[str, Any]) -> List[Alert]:
        """检查告警条件"""
        triggered_alerts = []
        current_time = time.time()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # 检查冷却期
            if current_time - rule.last_triggered < rule.cooldown:
                continue
            
            try:
                # 检查告警条件
                if rule.condition(data):
                    # 生成告警
                    alert = self._create_alert(rule, data)
                    triggered_alerts.append(alert)
                    
                    # 更新规则触发时间
                    rule.last_triggered = current_time
                    
                    # 保存告警
                    self.alerts[alert.id] = alert
                    
                    # 发送通知
                    await self._send_notification(alert)
                    
                    # 更新统计
                    self._update_stats(alert)
                    
            except Exception as e:
                logger.error(f"检查告警规则 {rule.name} 时出错: {e}")
        
        return triggered_alerts
    
    def _create_alert(self, rule: AlertRule, data: Dict[str, Any]) -> Alert:
        """创建告警"""
        alert_id = f"{rule.name}_{int(time.time())}"
        
        # 格式化消息
        try:
            message = rule.message_template.format(**data.get(rule.alert_type.value, {}))
        except (KeyError, ValueError):
            message = rule.message_template
        
        return Alert(
            id=alert_id,
            type=rule.alert_type,
            level=rule.level,
            title=f"[{rule.level.upper()}] {rule.name}",
            message=message,
            details=data.get(rule.alert_type.value, {}),
            timestamp=time.time(),
            source="alert_service"
        )
    
    async def _send_notification(self, alert: Alert):
        """发送告警通知"""
        if alert.notification_sent:
            return
        
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"发送告警通知失败: {e}")
        
        alert.notification_sent = True
        self.stats["notifications_sent"] += 1
    
    def _update_stats(self, alert: Alert):
        """更新统计信息"""
        self.stats["total_alerts"] += 1
        
        # 按级别统计
        level_key = alert.level.value
        self.stats["alerts_by_level"][level_key] = self.stats["alerts_by_level"].get(level_key, 0) + 1
        
        # 按类型统计
        type_key = alert.type.value
        self.stats["alerts_by_type"][type_key] = self.stats["alerts_by_type"].get(type_key, 0) + 1
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """解决告警"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        if alert.resolved:
            return False
        
        alert.resolved = True
        alert.resolved_at = time.time()
        alert.resolved_by = resolved_by
        
        self.stats["resolved_alerts"] += 1
        
        logger.info(f"告警已解决: {alert_id} by {resolved_by}")
        return True
    
    def get_active_alerts(self, alert_type: Optional[AlertType] = None, level: Optional[AlertLevel] = None) -> List[Alert]:
        """获取活跃告警"""
        alerts = [alert for alert in self.alerts.values() if not alert.resolved]
        
        if alert_type:
            alerts = [alert for alert in alerts if alert.type == alert_type]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        # 按时间倒序排序
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts
    
    def get_alert_history(self, hours: int = 24, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        cutoff_time = time.time() - (hours * 3600)
        
        alerts = [
            alert for alert in self.alerts.values()
            if alert.timestamp >= cutoff_time
        ]
        
        # 按时间倒序排序并限制数量
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        active_alerts = len(self.get_active_alerts())
        
        return {
            **self.stats,
            "active_alerts": active_alerts,
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([rule for rule in self.alert_rules if rule.enabled]),
            "notification_handlers": len(self.notification_handlers),
        }
    
    def clear_old_alerts(self, hours: int = 168):  # 默认保留7天
        """清理旧告警"""
        cutoff_time = time.time() - (hours * 3600)
        
        old_alert_ids = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_time and alert.resolved
        ]
        
        for alert_id in old_alert_ids:
            del self.alerts[alert_id]
        
        logger.info(f"清理了 {len(old_alert_ids)} 条过期告警")
        return len(old_alert_ids)


# 默认通知处理器
async def log_notification_handler(alert: Alert):
    """日志通知处理器"""
    log_level = {
        AlertLevel.INFO: logger.info,
        AlertLevel.WARNING: logger.warning,
        AlertLevel.ERROR: logger.error,
        AlertLevel.CRITICAL: logger.critical,
    }.get(alert.level, logger.info)
    
    log_level(
        f"告警通知: {alert.title} - {alert.message}",
        extra={
            "alert_id": alert.id,
            "alert_type": alert.type.value,
            "alert_level": alert.level.value,
            "alert_details": alert.details,
            "timestamp": alert.timestamp,
        }
    )


async def webhook_notification_handler(alert: Alert, webhook_url: str = None):
    """Webhook通知处理器"""
    if not webhook_url:
        return
    
    try:
        import aiohttp
        
        payload = {
            "alert_id": alert.id,
            "type": alert.type.value,
            "level": alert.level.value,
            "title": alert.title,
            "message": alert.message,
            "details": alert.details,
            "timestamp": alert.timestamp,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Webhook通知发送成功: {alert.id}")
                else:
                    logger.error(f"Webhook通知发送失败: {response.status}")
                    
    except Exception as e:
        logger.error(f"Webhook通知处理器错误: {e}")


# 全局告警服务实例
alert_service = AlertService()

# 添加默认通知处理器
alert_service.add_notification_handler(log_notification_handler)


def get_alert_service() -> AlertService:
    """获取告警服务实例"""
    return alert_service
