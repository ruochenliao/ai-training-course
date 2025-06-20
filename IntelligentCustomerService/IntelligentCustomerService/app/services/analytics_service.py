"""
高级分析服务
提供用户行为分析、数据洞察、性能监控、趋势预测等功能
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ..core.cache_manager import cache_manager
from ..models.admin import User
from ..core.crud import CRUDBase

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    CHAT_START = "chat_start"
    CHAT_END = "chat_end"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    VOICE_USED = "voice_used"
    IMAGE_GENERATED = "image_generated"
    DOCUMENT_UPLOADED = "document_uploaded"
    KNOWLEDGE_SEARCHED = "knowledge_searched"
    ERROR_OCCURRED = "error_occurred"
    FEATURE_USED = "feature_used"


@dataclass
class AnalyticsEvent:
    """分析事件"""
    event_id: str
    event_type: EventType
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    properties: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "properties": self.properties,
            "metadata": self.metadata or {}
        }


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    username: str
    registration_date: datetime
    last_active: datetime
    total_sessions: int
    total_messages: int
    avg_session_duration: float
    favorite_features: List[str]
    user_segment: str
    engagement_score: float
    satisfaction_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    active_users: int
    total_sessions: int
    avg_response_time: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnalyticsService:
    """高级分析服务"""
    
    def __init__(self):
        self.events_buffer: List[AnalyticsEvent] = []
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.user_profiles_cache: Dict[str, UserProfile] = {}
        
        # 启动后台任务
        asyncio.create_task(self._process_events_task())
        asyncio.create_task(self._collect_metrics_task())
        
        logger.info("高级分析服务初始化完成")
    
    async def track_event(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        跟踪事件
        
        Args:
            event_type: 事件类型
            user_id: 用户ID
            session_id: 会话ID
            properties: 事件属性
            metadata: 元数据
        """
        try:
            event = AnalyticsEvent(
                event_id=f"{datetime.now().timestamp()}_{user_id}_{event_type.value}",
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now(),
                properties=properties or {},
                metadata=metadata
            )
            
            self.events_buffer.append(event)
            
            # 实时更新用户会话
            if user_id and session_id:
                await self._update_user_session(user_id, session_id, event)
            
        except Exception as e:
            logger.error(f"跟踪事件失败: {str(e)}")
    
    async def _update_user_session(
        self,
        user_id: str,
        session_id: str,
        event: AnalyticsEvent
    ):
        """更新用户会话信息"""
        try:
            session_key = f"{user_id}_{session_id}"
            
            if session_key not in self.user_sessions:
                self.user_sessions[session_key] = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "start_time": event.timestamp,
                    "last_activity": event.timestamp,
                    "events": [],
                    "message_count": 0,
                    "features_used": set(),
                    "errors": 0
                }
            
            session = self.user_sessions[session_key]
            session["last_activity"] = event.timestamp
            session["events"].append(event.to_dict())
            
            # 更新统计信息
            if event.event_type == EventType.MESSAGE_SENT:
                session["message_count"] += 1
            elif event.event_type == EventType.ERROR_OCCURRED:
                session["errors"] += 1
            elif event.event_type == EventType.FEATURE_USED:
                feature_name = event.properties.get("feature_name")
                if feature_name:
                    session["features_used"].add(feature_name)
            
        except Exception as e:
            logger.error(f"更新用户会话失败: {str(e)}")
    
    async def get_user_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户分析数据
        
        Args:
            user_id: 用户ID
            days: 分析天数
            
        Returns:
            用户分析数据
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取用户事件
            user_events = [
                event for event in self.events_buffer
                if event.user_id == user_id and start_date <= event.timestamp <= end_date
            ]
            
            if not user_events:
                return {
                    "user_id": user_id,
                    "period": f"{days}天",
                    "total_events": 0,
                    "message": "暂无数据"
                }
            
            # 基础统计
            total_events = len(user_events)
            event_types = Counter([event.event_type.value for event in user_events])
            
            # 会话分析
            user_sessions = [
                session for session in self.user_sessions.values()
                if session["user_id"] == user_id
            ]
            
            session_durations = []
            total_messages = 0
            features_used = set()
            
            for session in user_sessions:
                start_time = datetime.fromisoformat(session["start_time"].isoformat())
                last_activity = datetime.fromisoformat(session["last_activity"].isoformat())
                duration = (last_activity - start_time).total_seconds() / 60  # 分钟
                session_durations.append(duration)
                total_messages += session["message_count"]
                features_used.update(session["features_used"])
            
            # 活跃度分析
            daily_activity = defaultdict(int)
            for event in user_events:
                date_key = event.timestamp.date().isoformat()
                daily_activity[date_key] += 1
            
            # 使用模式分析
            hourly_activity = defaultdict(int)
            for event in user_events:
                hour_key = event.timestamp.hour
                hourly_activity[hour_key] += 1
            
            return {
                "user_id": user_id,
                "period": f"{days}天",
                "summary": {
                    "total_events": total_events,
                    "total_sessions": len(user_sessions),
                    "total_messages": total_messages,
                    "avg_session_duration": statistics.mean(session_durations) if session_durations else 0,
                    "features_used": list(features_used)
                },
                "event_distribution": dict(event_types),
                "daily_activity": dict(daily_activity),
                "hourly_activity": dict(hourly_activity),
                "engagement_metrics": {
                    "active_days": len(daily_activity),
                    "avg_daily_events": statistics.mean(daily_activity.values()) if daily_activity else 0,
                    "peak_hour": max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户分析失败: {str(e)}")
            return {"error": str(e)}
    
    async def get_system_analytics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取系统分析数据
        
        Args:
            days: 分析天数
            
        Returns:
            系统分析数据
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取时间范围内的事件
            period_events = [
                event for event in self.events_buffer
                if start_date <= event.timestamp <= end_date
            ]
            
            # 基础统计
            total_events = len(period_events)
            unique_users = len(set(event.user_id for event in period_events if event.user_id))
            
            # 事件类型分布
            event_types = Counter([event.event_type.value for event in period_events])
            
            # 每日统计
            daily_stats = defaultdict(lambda: {
                "events": 0,
                "users": set(),
                "sessions": set(),
                "errors": 0
            })
            
            for event in period_events:
                date_key = event.timestamp.date().isoformat()
                daily_stats[date_key]["events"] += 1
                if event.user_id:
                    daily_stats[date_key]["users"].add(event.user_id)
                if event.session_id:
                    daily_stats[date_key]["sessions"].add(event.session_id)
                if event.event_type == EventType.ERROR_OCCURRED:
                    daily_stats[date_key]["errors"] += 1
            
            # 转换为可序列化格式
            daily_metrics = {}
            for date, stats in daily_stats.items():
                daily_metrics[date] = {
                    "events": stats["events"],
                    "unique_users": len(stats["users"]),
                    "unique_sessions": len(stats["sessions"]),
                    "errors": stats["errors"],
                    "error_rate": stats["errors"] / max(stats["events"], 1)
                }
            
            # 功能使用统计
            feature_usage = defaultdict(int)
            for event in period_events:
                if event.event_type == EventType.FEATURE_USED:
                    feature_name = event.properties.get("feature_name")
                    if feature_name:
                        feature_usage[feature_name] += 1
            
            # 性能指标
            recent_metrics = self.system_metrics_history[-days*24:] if self.system_metrics_history else []
            
            performance_summary = {}
            if recent_metrics:
                performance_summary = {
                    "avg_response_time": statistics.mean([m.avg_response_time for m in recent_metrics]),
                    "avg_error_rate": statistics.mean([m.error_rate for m in recent_metrics]),
                    "avg_cpu_usage": statistics.mean([m.cpu_usage for m in recent_metrics]),
                    "avg_memory_usage": statistics.mean([m.memory_usage for m in recent_metrics])
                }
            
            return {
                "period": f"{days}天",
                "summary": {
                    "total_events": total_events,
                    "unique_users": unique_users,
                    "avg_daily_events": total_events / days,
                    "avg_daily_users": unique_users / days
                },
                "event_distribution": dict(event_types),
                "daily_metrics": daily_metrics,
                "feature_usage": dict(feature_usage),
                "performance_summary": performance_summary
            }
            
        except Exception as e:
            logger.error(f"获取系统分析失败: {str(e)}")
            return {"error": str(e)}
    
    async def generate_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        生成用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户画像
        """
        try:
            # 检查缓存
            if user_id in self.user_profiles_cache:
                return self.user_profiles_cache[user_id]
            
            # 获取用户基础信息
            # 这里应该从数据库获取，暂时使用模拟数据
            user_info = {
                "username": f"用户{user_id}",
                "registration_date": datetime.now() - timedelta(days=30)
            }
            
            # 获取用户事件
            user_events = [
                event for event in self.events_buffer
                if event.user_id == user_id
            ]
            
            if not user_events:
                return None
            
            # 计算基础指标
            last_active = max(event.timestamp for event in user_events)
            
            # 会话分析
            user_sessions = [
                session for session in self.user_sessions.values()
                if session["user_id"] == user_id
            ]
            
            total_sessions = len(user_sessions)
            total_messages = sum(session["message_count"] for session in user_sessions)
            
            session_durations = []
            all_features = set()
            
            for session in user_sessions:
                start_time = session["start_time"]
                last_activity = session["last_activity"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity)
                
                duration = (last_activity - start_time).total_seconds() / 60
                session_durations.append(duration)
                all_features.update(session["features_used"])
            
            avg_session_duration = statistics.mean(session_durations) if session_durations else 0
            
            # 功能偏好分析
            feature_usage = Counter()
            for event in user_events:
                if event.event_type == EventType.FEATURE_USED:
                    feature_name = event.properties.get("feature_name")
                    if feature_name:
                        feature_usage[feature_name] += 1
            
            favorite_features = [feature for feature, _ in feature_usage.most_common(5)]
            
            # 用户分群
            user_segment = self._classify_user_segment(
                total_sessions, total_messages, avg_session_duration, len(favorite_features)
            )
            
            # 参与度评分
            engagement_score = self._calculate_engagement_score(
                total_sessions, total_messages, avg_session_duration, len(user_events)
            )
            
            # 满意度评分（基于错误率和使用频率）
            error_events = [e for e in user_events if e.event_type == EventType.ERROR_OCCURRED]
            error_rate = len(error_events) / len(user_events) if user_events else 0
            satisfaction_score = max(0, 1 - error_rate) * engagement_score
            
            profile = UserProfile(
                user_id=user_id,
                username=user_info["username"],
                registration_date=user_info["registration_date"],
                last_active=last_active,
                total_sessions=total_sessions,
                total_messages=total_messages,
                avg_session_duration=avg_session_duration,
                favorite_features=favorite_features,
                user_segment=user_segment,
                engagement_score=engagement_score,
                satisfaction_score=satisfaction_score
            )
            
            # 缓存结果
            self.user_profiles_cache[user_id] = profile
            
            return profile
            
        except Exception as e:
            logger.error(f"生成用户画像失败: {str(e)}")
            return None
    
    def _classify_user_segment(
        self,
        total_sessions: int,
        total_messages: int,
        avg_session_duration: float,
        feature_count: int
    ) -> str:
        """用户分群"""
        try:
            # 简单的规则分群
            if total_sessions >= 20 and total_messages >= 100:
                return "高价值用户"
            elif total_sessions >= 10 and total_messages >= 50:
                return "活跃用户"
            elif total_sessions >= 5:
                return "普通用户"
            elif total_sessions >= 1:
                return "新用户"
            else:
                return "潜在用户"
                
        except Exception:
            return "未分类"
    
    def _calculate_engagement_score(
        self,
        total_sessions: int,
        total_messages: int,
        avg_session_duration: float,
        total_events: int
    ) -> float:
        """计算参与度评分"""
        try:
            # 归一化各项指标
            session_score = min(total_sessions / 20, 1.0)  # 最多20个会话得满分
            message_score = min(total_messages / 100, 1.0)  # 最多100条消息得满分
            duration_score = min(avg_session_duration / 30, 1.0)  # 平均30分钟得满分
            activity_score = min(total_events / 200, 1.0)  # 最多200个事件得满分
            
            # 加权平均
            engagement_score = (
                session_score * 0.3 +
                message_score * 0.3 +
                duration_score * 0.2 +
                activity_score * 0.2
            )
            
            return round(engagement_score, 2)
            
        except Exception:
            return 0.0
    
    async def get_user_segments(self) -> Dict[str, Any]:
        """获取用户分群统计"""
        try:
            segments = defaultdict(int)
            
            # 生成所有用户的画像
            unique_users = set(event.user_id for event in self.events_buffer if event.user_id)
            
            for user_id in unique_users:
                profile = await self.generate_user_profile(user_id)
                if profile:
                    segments[profile.user_segment] += 1
            
            total_users = sum(segments.values())
            
            segment_analysis = {}
            for segment, count in segments.items():
                segment_analysis[segment] = {
                    "count": count,
                    "percentage": round(count / total_users * 100, 1) if total_users > 0 else 0
                }
            
            return {
                "total_users": total_users,
                "segments": segment_analysis
            }
            
        except Exception as e:
            logger.error(f"获取用户分群失败: {str(e)}")
            return {"error": str(e)}
    
    async def predict_user_churn(self, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """预测用户流失"""
        try:
            current_time = datetime.now()
            churn_threshold = current_time - timedelta(days=days_threshold)
            
            at_risk_users = []
            
            # 获取所有用户
            unique_users = set(event.user_id for event in self.events_buffer if event.user_id)
            
            for user_id in unique_users:
                # 获取用户最后活动时间
                user_events = [e for e in self.events_buffer if e.user_id == user_id]
                if not user_events:
                    continue
                
                last_activity = max(event.timestamp for event in user_events)
                
                if last_activity < churn_threshold:
                    # 计算流失风险评分
                    days_inactive = (current_time - last_activity).days
                    risk_score = min(days_inactive / 30, 1.0)  # 30天无活动为最高风险
                    
                    profile = await self.generate_user_profile(user_id)
                    
                    at_risk_users.append({
                        "user_id": user_id,
                        "last_activity": last_activity.isoformat(),
                        "days_inactive": days_inactive,
                        "risk_score": round(risk_score, 2),
                        "user_segment": profile.user_segment if profile else "未知",
                        "engagement_score": profile.engagement_score if profile else 0
                    })
            
            # 按风险评分排序
            at_risk_users.sort(key=lambda x: x["risk_score"], reverse=True)
            
            return at_risk_users
            
        except Exception as e:
            logger.error(f"预测用户流失失败: {str(e)}")
            return []
    
    async def _process_events_task(self):
        """处理事件的后台任务"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟处理一次
                
                if len(self.events_buffer) > 10000:
                    # 保留最近的事件，删除旧事件
                    self.events_buffer = self.events_buffer[-5000:]
                    logger.info("清理旧事件，保留最近5000条")
                
                # 清理过期的用户画像缓存
                if len(self.user_profiles_cache) > 1000:
                    self.user_profiles_cache.clear()
                    logger.info("清理用户画像缓存")
                
            except Exception as e:
                logger.error(f"处理事件任务失败: {str(e)}")
    
    async def _collect_metrics_task(self):
        """收集系统指标的后台任务"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时收集一次
                
                # 模拟系统指标收集
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    active_users=len(set(
                        session["user_id"] for session in self.user_sessions.values()
                        if (datetime.now() - session["last_activity"]).total_seconds() < 3600
                    )),
                    total_sessions=len(self.user_sessions),
                    avg_response_time=0.5,  # 模拟值
                    error_rate=0.01,  # 模拟值
                    cpu_usage=0.3,  # 模拟值
                    memory_usage=0.6,  # 模拟值
                    disk_usage=0.4,  # 模拟值
                    network_io=1024  # 模拟值
                )
                
                self.system_metrics_history.append(metrics)
                
                # 保留最近7天的指标
                if len(self.system_metrics_history) > 7 * 24:
                    self.system_metrics_history = self.system_metrics_history[-7*24:]
                
            except Exception as e:
                logger.error(f"收集系统指标失败: {str(e)}")


# 全局分析服务实例
analytics_service = AnalyticsService()
