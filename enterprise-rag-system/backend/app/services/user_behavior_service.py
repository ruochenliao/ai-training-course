"""
用户行为分析服务
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional

from app.models.user import User, UserEvent as UserEventModel, UserSession as UserSessionModel
from loguru import logger

from app.core.exceptions import AnalyticsException


class EventType(Enum):
    """事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    SEARCH = "search"
    CHAT = "chat"
    UPLOAD = "upload"
    VIEW_DOCUMENT = "view_document"
    CREATE_KB = "create_knowledge_base"
    DELETE_KB = "delete_knowledge_base"
    RATE_ANSWER = "rate_answer"
    EXPORT_DATA = "export_data"


@dataclass
class UserEvent:
    """用户事件"""
    user_id: int
    event_type: EventType
    timestamp: datetime
    properties: Dict[str, Any] = None
    session_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # 秒
    page_views: int = 0
    events_count: int = 0
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class UserBehaviorProfile:
    """用户行为画像"""
    user_id: int
    total_sessions: int
    total_events: int
    avg_session_duration: float
    most_active_time: str
    preferred_features: List[str]
    engagement_score: float
    last_activity: datetime
    behavior_patterns: Dict[str, Any]


class UserBehaviorService:
    """用户行为分析服务类"""

    def __init__(self):
        """初始化用户行为服务"""
        self.session_timeout = 30 * 60  # 30分钟会话超时

        logger.info("用户行为分析服务初始化完成")
    
    async def track_event(self, event: UserEvent) -> bool:
        """记录用户事件"""
        try:
            # 获取用户对象
            user = await User.get(id=event.user_id)

            # 创建用户事件记录
            await UserEventModel.create(
                user=user,
                event_type=event.event_type.value,
                properties=event.properties,
                session_id=event.session_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent
            )

            # 更新会话信息
            await self._update_session(event)

            logger.debug(f"记录用户事件: {event.event_type.value} - 用户 {event.user_id}")
            return True

        except Exception as e:
            logger.error(f"记录用户事件失败: {e}")
            return False
    
    async def get_user_behavior_profile(self, user_id: int) -> UserBehaviorProfile:
        """获取用户行为画像"""
        try:
            # 获取用户基础统计
            stats = await self._get_user_stats(user_id)
            
            # 获取行为模式
            patterns = await self._analyze_behavior_patterns(user_id)
            
            # 计算参与度分数
            engagement_score = await self._calculate_engagement_score(user_id)
            
            # 获取最活跃时间
            most_active_time = await self._get_most_active_time(user_id)
            
            # 获取偏好功能
            preferred_features = await self._get_preferred_features(user_id)
            
            # 获取最后活动时间
            last_activity = await self._get_last_activity(user_id)
            
            return UserBehaviorProfile(
                user_id=user_id,
                total_sessions=stats["total_sessions"],
                total_events=stats["total_events"],
                avg_session_duration=stats["avg_session_duration"],
                most_active_time=most_active_time,
                preferred_features=preferred_features,
                engagement_score=engagement_score,
                last_activity=last_activity,
                behavior_patterns=patterns
            )
            
        except Exception as e:
            logger.error(f"获取用户行为画像失败: {e}")
            raise AnalyticsException(f"获取用户行为画像失败: {e}")
    
    async def get_user_journey(
        self,
        user_id: int,
        time_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """获取用户行为路径"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)

            start_date, end_date = time_range

            # 获取用户和事件
            user = await User.get(id=user_id)
            events = await UserEventModel.filter(
                user=user,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).order_by("created_at").all()

            # 构建用户行为路径
            journey = []
            current_session = None
            session_events = []

            for event in events:
                if current_session != event.session_id:
                    if session_events:
                        journey.append({
                            "session_id": current_session,
                            "events": session_events,
                            "duration": self._calculate_session_duration(session_events)
                        })
                    current_session = event.session_id
                    session_events = []

                session_events.append({
                    "event_type": event.event_type,
                    "timestamp": event.created_at.isoformat(),
                    "properties": event.properties
                })

            # 添加最后一个会话
            if session_events:
                journey.append({
                    "session_id": current_session,
                    "events": session_events,
                    "duration": self._calculate_session_duration(session_events)
                })

            return journey

        except Exception as e:
            logger.error(f"获取用户行为路径失败: {e}")
            raise AnalyticsException(f"获取用户行为路径失败: {e}")
    
    async def get_cohort_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        period: str = "week"
    ) -> Dict[str, Any]:
        """获取队列分析（简化版本）"""
        try:
            # 简化的队列分析实现
            users = await User.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).all()

            # 按时间段分组用户
            cohorts = {}
            for user in users:
                if period == "week":
                    # 按周分组
                    week_start = user.created_at - timedelta(days=user.created_at.weekday())
                    key = week_start.strftime("%Y-W%U")
                elif period == "month":
                    # 按月分组
                    key = user.created_at.strftime("%Y-%m")
                else:
                    # 按天分组
                    key = user.created_at.strftime("%Y-%m-%d")

                if key not in cohorts:
                    cohorts[key] = []
                cohorts[key].append(user.id)

            # 构建返回数据
            retention_data = []
            for cohort_key, user_ids in cohorts.items():
                retention_data.append({
                    "cohort": cohort_key,
                    "users": len(user_ids),
                    "retention": [100]  # 简化版本只返回初始留存率
                })

            return {
                "cohorts": retention_data,
                "period": period,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"队列分析失败: {e}")
            raise AnalyticsException(f"队列分析失败: {e}")
    
    async def get_funnel_analysis(
        self,
        funnel_steps: List[EventType],
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """获取漏斗分析（简化版本）"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)

            start_date, end_date = time_range

            funnel_data = []
            total_users = None

            for i, step in enumerate(funnel_steps):
                # 简化版本：获取在时间范围内触发该事件的用户数
                events = await UserEventModel.filter(
                    event_type=step.value,
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).all()

                unique_users = len(set(event.user_id for event in events))

                if i == 0:
                    total_users = unique_users

                conversion_rate = (unique_users / total_users * 100) if total_users > 0 else 0
                drop_off_rate = 100 - conversion_rate if i > 0 else 0

                funnel_data.append({
                    "step": i + 1,
                    "event_type": step.value,
                    "users": unique_users,
                    "conversion_rate": conversion_rate,
                    "drop_off_rate": drop_off_rate
                })

            return {
                "funnel": funnel_data,
                "total_users": total_users or 0,
                "overall_conversion": (funnel_data[-1]["users"] / total_users * 100) if total_users and total_users > 0 else 0,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"漏斗分析失败: {e}")
            raise AnalyticsException(f"漏斗分析失败: {e}")
    
    async def get_feature_usage_stats(
        self,
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """获取功能使用统计"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)

            start_date, end_date = time_range

            # 获取时间范围内的所有事件
            events = await UserEventModel.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).all()

            # 统计功能使用情况
            feature_stats_dict = {}
            total_events = len(events)

            for event in events:
                event_type = event.event_type
                if event_type not in feature_stats_dict:
                    feature_stats_dict[event_type] = {
                        "count": 0,
                        "users": set()
                    }
                feature_stats_dict[event_type]["count"] += 1
                feature_stats_dict[event_type]["users"].add(event.user_id)

            # 构建返回数据
            feature_stats = []
            for event_type, stats in feature_stats_dict.items():
                feature_stats.append({
                    "feature": event_type,
                    "usage_count": stats["count"],
                    "unique_users": len(stats["users"]),
                    "usage_percentage": (stats["count"] / total_events * 100) if total_events > 0 else 0
                })

            # 按使用次数排序
            feature_stats.sort(key=lambda x: x["usage_count"], reverse=True)

            return {
                "features": feature_stats,
                "total_events": total_events,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"获取功能使用统计失败: {e}")
            raise AnalyticsException(f"获取功能使用统计失败: {e}")
    
    async def detect_anomalies(
        self,
        user_id: Optional[int] = None,
        time_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """检测异常行为（简化版本）"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                time_range = (start_date, end_date)

            start_date, end_date = time_range
            anomalies = []

            # 简化的异常检测：检测高频操作用户
            events = await UserEventModel.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).all()

            # 统计每个用户的事件数量
            user_event_counts = {}
            for event in events:
                user_id_key = event.user_id
                user_event_counts[user_id_key] = user_event_counts.get(user_id_key, 0) + 1

            # 检测高频用户（超过平均值2倍的用户）
            if user_event_counts:
                avg_events = sum(user_event_counts.values()) / len(user_event_counts)
                threshold = avg_events * 2

                for uid, count in user_event_counts.items():
                    if count > threshold and count > 50:  # 至少50个事件才算异常
                        anomalies.append({
                            "type": "high_frequency",
                            "user_id": uid,
                            "description": f"用户在短时间内执行了 {count} 次操作",
                            "severity": "medium",
                            "timestamp": datetime.now().isoformat()
                        })

            return anomalies

        except Exception as e:
            logger.error(f"异常行为检测失败: {e}")
            raise AnalyticsException(f"异常行为检测失败: {e}")
    
    # 私有辅助方法
    async def _update_session(self, event: UserEvent):
        """更新会话信息"""
        try:
            # 获取用户对象
            user = await User.get(id=event.user_id)

            # 检查是否存在活跃会话
            session = await UserSessionModel.filter(
                user=user,
                session_id=event.session_id
            ).first()

            if session:
                # 更新现有会话
                session.last_activity_at = event.timestamp
                await session.save(update_fields=["last_activity_at"])
            else:
                # 创建新会话
                from datetime import timedelta
                await UserSessionModel.create(
                    user=user,
                    session_id=event.session_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    device_info={},
                    is_active=True,
                    last_activity_at=event.timestamp,
                    expires_at=event.timestamp + timedelta(minutes=60)
                )

        except Exception as e:
            logger.error(f"更新会话信息失败: {e}")
    
    async def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户基础统计"""
        try:
            user = await User.get(id=user_id)

            # 获取会话统计
            total_sessions = await UserSessionModel.filter(user=user).count()

            # 获取事件统计
            total_events = await UserEventModel.filter(user=user).count()

            # 计算平均会话时长（简化版本）
            sessions = await UserSessionModel.filter(user=user).all()
            total_duration = 0
            valid_sessions = 0

            for session in sessions:
                if session.last_activity_at and session.created_at:
                    duration = (session.last_activity_at - session.created_at).total_seconds()
                    total_duration += duration
                    valid_sessions += 1

            avg_session_duration = total_duration / valid_sessions if valid_sessions > 0 else 0

            return {
                "total_sessions": total_sessions,
                "total_events": total_events,
                "avg_session_duration": avg_session_duration
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {
                "total_sessions": 0,
                "total_events": 0,
                "avg_session_duration": 0
            }
    
    async def _analyze_behavior_patterns(self, user_id: int) -> Dict[str, Any]:
        """分析用户行为模式"""
        try:
            user = await User.get(id=user_id)

            # 获取用户所有事件
            events = await UserEventModel.filter(user=user).all()

            # 统计事件类型分布
            event_distribution = {}
            for event in events:
                event_type = event.event_type
                event_distribution[event_type] = event_distribution.get(event_type, 0) + 1

            # 找出最常见的操作
            most_common_action = None
            if event_distribution:
                most_common_action = max(event_distribution.items(), key=lambda x: x[1])[0]

            # 计算活跃度等级
            total_events = len(events)
            if total_events > 100:
                activity_level = "high"
            elif total_events > 20:
                activity_level = "medium"
            else:
                activity_level = "low"

            patterns = {
                "event_distribution": event_distribution,
                "most_common_action": most_common_action,
                "activity_level": activity_level
            }

            return patterns
        except Exception as e:
            logger.error(f"分析行为模式失败: {e}")
            return {
                "event_distribution": {},
                "most_common_action": None,
                "activity_level": "low"
            }
    
    async def _calculate_engagement_score(self, user_id: int) -> float:
        """计算用户参与度分数"""
        try:
            # 简化的参与度计算
            stats = await self._get_user_stats(user_id)

            # 基于会话数、事件数和平均会话时长计算分数
            session_score = min(stats["total_sessions"] / 10, 1.0) * 30
            event_score = min(stats["total_events"] / 100, 1.0) * 40
            duration_score = min(stats["avg_session_duration"] / 600, 1.0) * 30  # 10分钟为满分

            return session_score + event_score + duration_score
        except Exception as e:
            logger.error(f"计算参与度分数失败: {e}")
            return 0.0

    async def _get_most_active_time(self, user_id: int) -> str:
        """获取最活跃时间"""
        try:
            user = await User.get(id=user_id)
            events = await UserEventModel.filter(user=user).all()

            if not events:
                return "未知"

            # 统计各小时的活动次数
            hour_counts = {}
            for event in events:
                hour = event.created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

            # 找出最活跃的小时
            most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            return f"{most_active_hour:02d}:00-{most_active_hour+1:02d}:00"
        except Exception as e:
            logger.error(f"获取最活跃时间失败: {e}")
            return "未知"

    async def _get_preferred_features(self, user_id: int) -> List[str]:
        """获取偏好功能"""
        try:
            patterns = await self._analyze_behavior_patterns(user_id)
            event_distribution = patterns.get("event_distribution", {})

            # 按使用频率排序，返回前3个功能
            sorted_features = sorted(event_distribution.items(), key=lambda x: x[1], reverse=True)
            return [feature for feature, _ in sorted_features[:3]]
        except Exception as e:
            logger.error(f"获取偏好功能失败: {e}")
            return []

    async def _get_last_activity(self, user_id: int) -> datetime:
        """获取最后活动时间"""
        try:
            user = await User.get(id=user_id)
            last_event = await UserEventModel.filter(user=user).order_by("-created_at").first()

            if last_event:
                return last_event.created_at
            else:
                return user.created_at
        except Exception as e:
            logger.error(f"获取最后活动时间失败: {e}")
            return datetime.now()

    def _calculate_session_duration(self, session_events: List[Dict[str, Any]]) -> int:
        """计算会话持续时间（秒）"""
        if len(session_events) < 2:
            return 0

        try:
            start_time = datetime.fromisoformat(session_events[0]["timestamp"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(session_events[-1]["timestamp"].replace('Z', '+00:00'))
            return int((end_time - start_time).total_seconds())
        except Exception:
            return 0




# 全局用户行为服务实例
user_behavior_service = UserBehaviorService()
