"""
审计日志CRUD操作
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from tortoise.expressions import Q
from tortoise.functions import Count

from ..models.audit_log import AuditLog, AuditAction, AuditLevel, AuditStatus
from ..schemas.audit_log import AuditLogCreate, AuditLogSearchParams
from .base import CRUDBase


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, None]):
    """审计日志CRUD操作类"""

    async def search(
        self,
        params: AuditLogSearchParams,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[AuditLog], int]:
        """搜索审计日志"""
        query = AuditLog.all()

        # 关键词搜索
        if params.keyword:
            query = query.filter(
                Q(description__icontains=params.keyword) |
                Q(resource_name__icontains=params.keyword) |
                Q(username__icontains=params.keyword)
            )

        # 操作类型筛选
        if params.action:
            query = query.filter(action=params.action)

        # 资源类型筛选
        if params.resource_type:
            query = query.filter(resource_type__icontains=params.resource_type)

        # 审计级别筛选
        if params.level:
            query = query.filter(level=params.level)

        # 操作状态筛选
        if params.status:
            query = query.filter(status=params.status)

        # 用户筛选
        if params.user_id:
            query = query.filter(user_id=params.user_id)

        if params.username:
            query = query.filter(username__icontains=params.username)

        # IP地址筛选
        if params.user_ip:
            query = query.filter(user_ip=params.user_ip)

        # 时间范围筛选
        if params.start_time:
            query = query.filter(created_at__gte=params.start_time)

        if params.end_time:
            query = query.filter(created_at__lte=params.end_time)

        # 排序
        query = query.order_by("-created_at")

        # 分页
        total = await query.count()
        offset = (page - 1) * size
        items = await query.offset(offset).limit(size).all()

        return items, total

    async def get_statistics(self) -> Dict[str, Any]:
        """获取审计日志统计信息"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 基础统计
        total_logs = await AuditLog.all().count()
        today_logs = await AuditLog.filter(created_at__gte=today_start).count()
        success_logs = await AuditLog.filter(status=AuditStatus.SUCCESS).count()
        failed_logs = await AuditLog.filter(status=AuditStatus.FAILED).count()

        # 按操作类型统计
        action_stats = {}
        for action in AuditAction:
            count = await AuditLog.filter(action=action).count()
            if count > 0:
                action_stats[action.value] = count

        # 按级别统计
        level_stats = {}
        for level in AuditLevel:
            count = await AuditLog.filter(level=level).count()
            if count > 0:
                level_stats[level.value] = count

        # 按资源类型统计
        resource_stats = await AuditLog.all().group_by("resource_type").annotate(
            count=Count("id")
        ).values("resource_type", "count")
        
        logs_by_resource = {item["resource_type"]: item["count"] for item in resource_stats}

        # 活跃用户TOP10
        user_stats = await AuditLog.filter(user_id__isnull=False).group_by("user_id", "username").annotate(
            count=Count("id")
        ).order_by("-count").limit(10).values("user_id", "username", "count")

        top_users = [
            {
                "user_id": item["user_id"],
                "username": item["username"],
                "action_count": item["count"]
            }
            for item in user_stats
        ]

        # 最近的关键操作
        recent_critical = await AuditLog.filter(
            level=AuditLevel.CRITICAL
        ).order_by("-created_at").limit(10).all()

        recent_critical_data = []
        for log in recent_critical:
            log_data = await log.to_dict()
            recent_critical_data.append(log_data)

        return {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "success_logs": success_logs,
            "failed_logs": failed_logs,
            "logs_by_action": action_stats,
            "logs_by_level": level_stats,
            "logs_by_resource": logs_by_resource,
            "top_users": top_users,
            "recent_critical": recent_critical_data
        }

    async def get_user_activity(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户活动统计"""
        start_date = datetime.now() - timedelta(days=days)
        
        logs = await AuditLog.filter(
            user_id=user_id,
            created_at__gte=start_date
        ).all()

        if not logs:
            return {
                "total_actions": 0,
                "actions_by_type": {},
                "actions_by_day": {},
                "last_action": None,
                "risk_score": 0.0
            }

        # 按操作类型统计
        actions_by_type = {}
        for log in logs:
            action = log.action.value
            actions_by_type[action] = actions_by_type.get(action, 0) + 1

        # 按天统计
        actions_by_day = {}
        for log in logs:
            day = log.created_at.date().isoformat()
            actions_by_day[day] = actions_by_day.get(day, 0) + 1

        # 计算风险评分
        risk_score = self._calculate_risk_score(logs)

        return {
            "total_actions": len(logs),
            "actions_by_type": actions_by_type,
            "actions_by_day": actions_by_day,
            "last_action": max(log.created_at for log in logs),
            "risk_score": risk_score
        }

    def _calculate_risk_score(self, logs: List[AuditLog]) -> float:
        """计算用户风险评分"""
        if not logs:
            return 0.0

        score = 0.0
        
        # 基于操作类型的风险评分
        risk_weights = {
            AuditAction.DELETE: 3.0,
            AuditAction.ASSIGN: 2.0,
            AuditAction.REVOKE: 2.0,
            AuditAction.UPDATE: 1.5,
            AuditAction.CREATE: 1.0,
            AuditAction.LOGIN: 0.5,
            AuditAction.VIEW: 0.1
        }

        # 基于级别的风险评分
        level_weights = {
            AuditLevel.CRITICAL: 4.0,
            AuditLevel.HIGH: 2.0,
            AuditLevel.MEDIUM: 1.0,
            AuditLevel.LOW: 0.5
        }

        for log in logs:
            action_weight = risk_weights.get(log.action, 1.0)
            level_weight = level_weights.get(log.level, 1.0)
            
            # 失败操作增加风险
            if log.status == AuditStatus.FAILED:
                action_weight *= 1.5
            
            score += action_weight * level_weight

        # 归一化到0-100分
        max_possible_score = len(logs) * 4.0 * 4.0  # 最高风险
        normalized_score = min(100.0, (score / max_possible_score) * 100) if max_possible_score > 0 else 0.0

        return round(normalized_score, 2)

    async def cleanup_old_logs(self, days_to_keep: int, dry_run: bool = True) -> Dict[str, Any]:
        """清理旧的审计日志"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 查询要删除的日志
        logs_to_delete = await AuditLog.filter(created_at__lt=cutoff_date).all()
        
        result = {
            "total_logs": await AuditLog.all().count(),
            "logs_to_delete": len(logs_to_delete),
            "deleted_count": 0,
            "freed_space": 0,
            "dry_run": dry_run
        }

        if not dry_run and logs_to_delete:
            # 实际删除
            deleted_count = await AuditLog.filter(created_at__lt=cutoff_date).delete()
            result["deleted_count"] = deleted_count
            
            # 估算释放的空间（简单估算）
            avg_log_size = 1024  # 假设每条日志平均1KB
            result["freed_space"] = deleted_count * avg_log_size

        return result

    async def export_logs(
        self,
        search_params: Optional[AuditLogSearchParams] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """导出审计日志"""
        if search_params:
            logs, _ = await self.search(search_params, page=1, size=limit)
        else:
            logs = await AuditLog.all().order_by("-created_at").limit(limit).all()

        export_data = []
        for log in logs:
            log_data = await log.to_dict()
            export_data.append(log_data)

        return export_data

    async def get_system_activity_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取系统活动摘要"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)

        summaries = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            # 当天的日志
            day_logs = await AuditLog.filter(
                created_at__gte=current_date,
                created_at__lt=next_date
            ).all()

            # 统计信息
            total_actions = len(day_logs)
            unique_users = len(set(log.user_id for log in day_logs if log.user_id))
            failed_actions = len([log for log in day_logs if log.status == AuditStatus.FAILED])
            critical_actions = len([log for log in day_logs if log.level == AuditLevel.CRITICAL])

            # 计算高峰时段
            hour_counts = {}
            for log in day_logs:
                hour = log.created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            peak_hour = max(hour_counts.keys(), key=lambda h: hour_counts[h]) if hour_counts else 0

            summaries.append({
                "date": current_date,
                "total_actions": total_actions,
                "unique_users": unique_users,
                "failed_actions": failed_actions,
                "critical_actions": critical_actions,
                "peak_hour": peak_hour
            })

        return summaries


# 创建CRUD实例
crud_audit_log = CRUDAuditLog(AuditLog)
