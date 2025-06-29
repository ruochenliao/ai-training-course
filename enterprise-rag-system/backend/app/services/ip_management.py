"""
IP管理服务
"""

import time
import asyncio
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import ipaddress

from loguru import logger
from tortoise.models import Model
from tortoise import fields

from app.core.redis_cache import get_redis_cache


class IPRule(Model):
    """IP规则模型"""
    
    id = fields.IntField(pk=True)
    ip_range = fields.CharField(max_length=50, description="IP地址或IP段")
    rule_type = fields.CharField(max_length=10, description="规则类型: allow/deny")
    description = fields.TextField(description="规则描述")
    enabled = fields.BooleanField(default=True, description="是否启用")
    priority = fields.IntField(default=0, description="优先级，数字越大优先级越高")
    
    # 创建信息
    created_by = fields.CharField(max_length=100, description="创建者")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 统计信息
    hit_count = fields.IntField(default=0, description="命中次数")
    last_hit_at = fields.DatetimeField(null=True, description="最后命中时间")
    
    class Meta:
        table = "ip_rules"
        ordering = ["-priority", "-created_at"]


class IPAccessLog(Model):
    """IP访问日志模型"""
    
    id = fields.IntField(pk=True)
    ip_address = fields.CharField(max_length=45, description="IP地址")
    request_path = fields.CharField(max_length=500, description="请求路径")
    request_method = fields.CharField(max_length=10, description="请求方法")
    user_agent = fields.TextField(null=True, description="用户代理")
    
    # 访问结果
    access_result = fields.CharField(max_length=20, description="访问结果: allowed/blocked/rate_limited")
    block_reason = fields.CharField(max_length=200, null=True, description="阻止原因")
    matched_rule_id = fields.IntField(null=True, description="匹配的规则ID")
    
    # 时间信息
    access_time = fields.DatetimeField(auto_now_add=True, description="访问时间")
    response_time = fields.FloatField(null=True, description="响应时间")
    
    # 地理位置信息（可选）
    country = fields.CharField(max_length=50, null=True, description="国家")
    region = fields.CharField(max_length=50, null=True, description="地区")
    city = fields.CharField(max_length=50, null=True, description="城市")
    
    class Meta:
        table = "ip_access_logs"
        ordering = ["-access_time"]


@dataclass
class IPStatistics:
    """IP统计信息"""
    ip_address: str
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    rate_limited_requests: int
    first_seen: datetime
    last_seen: datetime
    countries: List[str]
    user_agents: List[str]


class IPManagementService:
    """IP管理服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5分钟缓存
        self.stats_cache_ttl = 3600  # 1小时统计缓存
        
        # 内存缓存
        self.ip_rules_cache: Optional[List[IPRule]] = None
        self.cache_updated_at: Optional[float] = None
    
    async def get_ip_rules(self, force_refresh: bool = False) -> List[IPRule]:
        """获取IP规则列表"""
        current_time = time.time()
        
        # 检查缓存
        if (not force_refresh and 
            self.ip_rules_cache is not None and 
            self.cache_updated_at and 
            current_time - self.cache_updated_at < self.cache_ttl):
            return self.ip_rules_cache
        
        # 从数据库获取
        rules = await IPRule.filter(enabled=True).order_by("-priority", "-created_at")
        
        # 更新缓存
        self.ip_rules_cache = rules
        self.cache_updated_at = current_time
        
        logger.debug(f"加载IP规则: {len(rules)} 条")
        return rules
    
    async def add_ip_rule(
        self,
        ip_range: str,
        rule_type: str,
        description: str,
        created_by: str,
        priority: int = 0
    ) -> IPRule:
        """添加IP规则"""
        # 验证IP地址格式
        if not self._validate_ip_range(ip_range):
            raise ValueError(f"无效的IP地址或IP段: {ip_range}")
        
        # 验证规则类型
        if rule_type not in ["allow", "deny"]:
            raise ValueError(f"无效的规则类型: {rule_type}")
        
        # 创建规则
        rule = await IPRule.create(
            ip_range=ip_range,
            rule_type=rule_type,
            description=description,
            created_by=created_by,
            priority=priority
        )
        
        # 清除缓存
        await self._clear_cache()
        
        logger.info(f"添加IP规则: {rule_type} {ip_range} - {description}")
        return rule
    
    async def update_ip_rule(
        self,
        rule_id: int,
        ip_range: Optional[str] = None,
        rule_type: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Optional[IPRule]:
        """更新IP规则"""
        rule = await IPRule.get_or_none(id=rule_id)
        if not rule:
            return None
        
        # 更新字段
        if ip_range is not None:
            if not self._validate_ip_range(ip_range):
                raise ValueError(f"无效的IP地址或IP段: {ip_range}")
            rule.ip_range = ip_range
        
        if rule_type is not None:
            if rule_type not in ["allow", "deny"]:
                raise ValueError(f"无效的规则类型: {rule_type}")
            rule.rule_type = rule_type
        
        if description is not None:
            rule.description = description
        
        if enabled is not None:
            rule.enabled = enabled
        
        if priority is not None:
            rule.priority = priority
        
        await rule.save()
        
        # 清除缓存
        await self._clear_cache()
        
        logger.info(f"更新IP规则: {rule_id}")
        return rule
    
    async def delete_ip_rule(self, rule_id: int) -> bool:
        """删除IP规则"""
        rule = await IPRule.get_or_none(id=rule_id)
        if not rule:
            return False
        
        await rule.delete()
        
        # 清除缓存
        await self._clear_cache()
        
        logger.info(f"删除IP规则: {rule_id}")
        return True
    
    async def check_ip_access(self, ip_address: str) -> Dict[str, Any]:
        """检查IP访问权限"""
        rules = await self.get_ip_rules()
        
        for rule in rules:
            if self._ip_matches_rule(ip_address, rule):
                # 更新命中统计
                await self._update_rule_hit_stats(rule)
                
                return {
                    "allowed": rule.rule_type == "allow",
                    "rule_id": rule.id,
                    "rule_type": rule.rule_type,
                    "description": rule.description,
                    "priority": rule.priority
                }
        
        # 没有匹配的规则，默认允许
        return {
            "allowed": True,
            "rule_id": None,
            "rule_type": "default",
            "description": "默认允许",
            "priority": -1
        }
    
    async def log_ip_access(
        self,
        ip_address: str,
        request_path: str,
        request_method: str,
        access_result: str,
        user_agent: Optional[str] = None,
        block_reason: Optional[str] = None,
        matched_rule_id: Optional[int] = None,
        response_time: Optional[float] = None
    ):
        """记录IP访问日志"""
        try:
            await IPAccessLog.create(
                ip_address=ip_address,
                request_path=request_path,
                request_method=request_method,
                user_agent=user_agent,
                access_result=access_result,
                block_reason=block_reason,
                matched_rule_id=matched_rule_id,
                response_time=response_time
            )
        except Exception as e:
            logger.error(f"记录IP访问日志失败: {e}")
    
    async def get_ip_statistics(
        self,
        ip_address: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[IPStatistics]:
        """获取IP统计信息"""
        try:
            # 尝试从缓存获取
            cache_key = f"ip_stats:{ip_address or 'all'}:{hours}"
            redis_cache = await get_redis_cache()
            cached_stats = await redis_cache.get(cache_key, "ip_management")
            
            if cached_stats:
                return cached_stats
            
            # 从数据库查询
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = IPAccessLog.filter(access_time__gte=cutoff_time)
            if ip_address:
                query = query.filter(ip_address=ip_address)
            
            logs = await query.order_by("-access_time").limit(limit * 10)  # 获取更多数据用于统计
            
            # 按IP分组统计
            ip_stats_dict = {}
            for log in logs:
                ip = log.ip_address
                if ip not in ip_stats_dict:
                    ip_stats_dict[ip] = {
                        "ip_address": ip,
                        "total_requests": 0,
                        "blocked_requests": 0,
                        "allowed_requests": 0,
                        "rate_limited_requests": 0,
                        "first_seen": log.access_time,
                        "last_seen": log.access_time,
                        "countries": set(),
                        "user_agents": set()
                    }
                
                stats = ip_stats_dict[ip]
                stats["total_requests"] += 1
                
                if log.access_result == "blocked":
                    stats["blocked_requests"] += 1
                elif log.access_result == "allowed":
                    stats["allowed_requests"] += 1
                elif log.access_result == "rate_limited":
                    stats["rate_limited_requests"] += 1
                
                if log.access_time < stats["first_seen"]:
                    stats["first_seen"] = log.access_time
                if log.access_time > stats["last_seen"]:
                    stats["last_seen"] = log.access_time
                
                if log.country:
                    stats["countries"].add(log.country)
                if log.user_agent:
                    stats["user_agents"].add(log.user_agent[:100])  # 限制长度
            
            # 转换为IPStatistics对象
            result = []
            for stats in ip_stats_dict.values():
                result.append(IPStatistics(
                    ip_address=stats["ip_address"],
                    total_requests=stats["total_requests"],
                    blocked_requests=stats["blocked_requests"],
                    allowed_requests=stats["allowed_requests"],
                    rate_limited_requests=stats["rate_limited_requests"],
                    first_seen=stats["first_seen"],
                    last_seen=stats["last_seen"],
                    countries=list(stats["countries"]),
                    user_agents=list(stats["user_agents"])
                ))
            
            # 按总请求数排序
            result.sort(key=lambda x: x.total_requests, reverse=True)
            result = result[:limit]
            
            # 缓存结果
            await redis_cache.set(cache_key, result, self.stats_cache_ttl, "ip_management")
            
            return result
            
        except Exception as e:
            logger.error(f"获取IP统计失败: {e}")
            return []
    
    async def get_blocked_ips(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取被阻止的IP列表"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        logs = await IPAccessLog.filter(
            access_time__gte=cutoff_time,
            access_result="blocked"
        ).group_by("ip_address").order_by("-access_time")
        
        # 统计每个IP的阻止次数
        blocked_ips = {}
        for log in logs:
            ip = log.ip_address
            if ip not in blocked_ips:
                blocked_ips[ip] = {
                    "ip_address": ip,
                    "block_count": 0,
                    "last_blocked": log.access_time,
                    "block_reasons": set()
                }
            
            blocked_ips[ip]["block_count"] += 1
            if log.block_reason:
                blocked_ips[ip]["block_reasons"].add(log.block_reason)
            
            if log.access_time > blocked_ips[ip]["last_blocked"]:
                blocked_ips[ip]["last_blocked"] = log.access_time
        
        # 转换为列表并排序
        result = []
        for stats in blocked_ips.values():
            stats["block_reasons"] = list(stats["block_reasons"])
            result.append(stats)
        
        result.sort(key=lambda x: x["block_count"], reverse=True)
        return result
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """清理旧的访问日志"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        deleted_count = await IPAccessLog.filter(access_time__lt=cutoff_time).delete()
        
        logger.info(f"清理IP访问日志: 删除 {deleted_count} 条记录")
        return deleted_count
    
    def _validate_ip_range(self, ip_range: str) -> bool:
        """验证IP地址或IP段格式"""
        try:
            if "/" in ip_range:
                # IP段
                ipaddress.ip_network(ip_range, strict=False)
            else:
                # 单个IP
                ipaddress.ip_address(ip_range)
            return True
        except ValueError:
            return False
    
    def _ip_matches_rule(self, ip_address: str, rule: IPRule) -> bool:
        """检查IP是否匹配规则"""
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            if "/" in rule.ip_range:
                # IP段匹配
                network = ipaddress.ip_network(rule.ip_range, strict=False)
                return ip_obj in network
            else:
                # 精确匹配
                return ip_address == rule.ip_range
                
        except ValueError:
            return False
    
    async def _update_rule_hit_stats(self, rule: IPRule):
        """更新规则命中统计"""
        try:
            rule.hit_count += 1
            rule.last_hit_at = datetime.now()
            await rule.save(update_fields=["hit_count", "last_hit_at"])
        except Exception as e:
            logger.error(f"更新规则命中统计失败: {e}")
    
    async def _clear_cache(self):
        """清除缓存"""
        self.ip_rules_cache = None
        self.cache_updated_at = None
        
        # 清除Redis缓存
        try:
            redis_cache = await get_redis_cache()
            await redis_cache.clear_namespace("ip_management")
        except Exception as e:
            logger.error(f"清除IP管理缓存失败: {e}")


# 全局IP管理服务实例
ip_management_service = IPManagementService()


def get_ip_management_service() -> IPManagementService:
    """获取IP管理服务实例"""
    return ip_management_service
