"""
用户行为分析API端点
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.services.user_behavior_service import (
    user_behavior_service,
    UserEvent,
    EventType
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.exceptions import AnalyticsException

router = APIRouter()


class EventTrackingRequest(BaseModel):
    """事件跟踪请求"""
    event_type: EventType
    properties: Dict[str, Any] = {}
    session_id: str = ""


class BehaviorAnalysisResponse(BaseModel):
    """行为分析响应"""
    success: bool = True
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}


@router.post("/track")
async def track_user_event(
    request: EventTrackingRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    跟踪用户事件
    """
    try:
        # 获取客户端信息
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # 创建用户事件
        event = UserEvent(
            user_id=current_user.id,
            event_type=request.event_type,
            timestamp=datetime.now(),
            properties=request.properties,
            session_id=request.session_id or f"session_{current_user.id}_{datetime.now().timestamp()}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 记录事件
        success = await user_behavior_service.track_event(event)
        
        return {
            "success": success,
            "event_id": f"{event.user_id}_{event.timestamp.timestamp()}",
            "timestamp": event.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"事件跟踪失败: {str(e)}")


@router.get("/profile/{user_id}", response_model=BehaviorAnalysisResponse)
async def get_user_behavior_profile(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取用户行为画像
    """
    try:
        # 检查权限（只能查看自己的或管理员权限）
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")
        
        profile = await user_behavior_service.get_user_behavior_profile(user_id)
        
        return BehaviorAnalysisResponse(
            data={
                "user_id": profile.user_id,
                "total_sessions": profile.total_sessions,
                "total_events": profile.total_events,
                "avg_session_duration": profile.avg_session_duration,
                "most_active_time": profile.most_active_time,
                "preferred_features": profile.preferred_features,
                "engagement_score": profile.engagement_score,
                "last_activity": profile.last_activity.isoformat(),
                "behavior_patterns": profile.behavior_patterns
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "profile_version": "1.0"
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户行为画像失败: {str(e)}")


@router.get("/journey/{user_id}", response_model=BehaviorAnalysisResponse)
async def get_user_journey(
    user_id: int,
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户行为路径
    """
    try:
        # 检查权限
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        journey = await user_behavior_service.get_user_journey(
            user_id, (start_date, end_date)
        )
        
        return BehaviorAnalysisResponse(
            data={
                "user_id": user_id,
                "journey": journey,
                "session_count": len(journey),
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "analysis_period_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户行为路径失败: {str(e)}")


@router.get("/cohort-analysis", response_model=BehaviorAnalysisResponse)
async def get_cohort_analysis(
    days: int = Query(90, ge=30, le=365, description="分析天数"),
    period: str = Query("week", description="队列周期"),
    current_user: User = Depends(get_current_user)
):
    """
    获取队列分析
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cohort_analysis = await user_behavior_service.get_cohort_analysis(
            start_date, end_date, period
        )
        
        return BehaviorAnalysisResponse(
            data=cohort_analysis,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "cohort",
                "period": period
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"队列分析失败: {str(e)}")


@router.get("/funnel-analysis", response_model=BehaviorAnalysisResponse)
async def get_funnel_analysis(
    steps: List[EventType] = Query(..., description="漏斗步骤"),
    days: int = Query(30, ge=1, le=90, description="分析天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取漏斗分析
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        funnel_analysis = await user_behavior_service.get_funnel_analysis(
            steps, (start_date, end_date)
        )
        
        return BehaviorAnalysisResponse(
            data=funnel_analysis,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "funnel",
                "steps_count": len(steps)
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"漏斗分析失败: {str(e)}")


@router.get("/feature-usage", response_model=BehaviorAnalysisResponse)
async def get_feature_usage_stats(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取功能使用统计
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        feature_stats = await user_behavior_service.get_feature_usage_stats(
            (start_date, end_date)
        )
        
        return BehaviorAnalysisResponse(
            data=feature_stats,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "analysis_period_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能使用统计失败: {str(e)}")


@router.get("/anomalies", response_model=BehaviorAnalysisResponse)
async def detect_behavior_anomalies(
    user_id: Optional[int] = Query(None, description="特定用户ID"),
    days: int = Query(7, ge=1, le=30, description="检测天数"),
    current_user: User = Depends(get_current_user)
):
    """
    检测异常行为
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        anomalies = await user_behavior_service.detect_anomalies(
            user_id, (start_date, end_date)
        )
        
        return BehaviorAnalysisResponse(
            data={
                "anomalies": anomalies,
                "total_count": len(anomalies),
                "severity_distribution": {
                    "high": len([a for a in anomalies if a.get("severity") == "high"]),
                    "medium": len([a for a in anomalies if a.get("severity") == "medium"]),
                    "low": len([a for a in anomalies if a.get("severity") == "low"])
                }
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "detection_period_days": days,
                "target_user": user_id
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"异常行为检测失败: {str(e)}")


@router.get("/heatmap")
async def get_activity_heatmap(
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取活动热力图数据
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 生成24小时x7天的热力图数据
        heatmap_data = []
        
        # 这里应该从实际数据生成热力图
        # 目前使用模拟数据
        import random
        
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day_idx, day in enumerate(days_of_week):
            for hour in range(24):
                # 模拟活动强度（工作时间更高）
                if 9 <= hour <= 17 and day_idx < 5:  # 工作日工作时间
                    intensity = random.randint(50, 100)
                elif 19 <= hour <= 22:  # 晚上时间
                    intensity = random.randint(20, 60)
                else:
                    intensity = random.randint(0, 30)
                
                heatmap_data.append({
                    "day": day,
                    "hour": hour,
                    "intensity": intensity,
                    "event_count": intensity * 2
                })
        
        return BehaviorAnalysisResponse(
            data={
                "heatmap": heatmap_data,
                "max_intensity": max(item["intensity"] for item in heatmap_data),
                "total_events": sum(item["event_count"] for item in heatmap_data)
            },
            metadata={
                "generated_at": datetime.now().isoformat(),
                "data_type": "activity_heatmap",
                "period_days": days
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动热力图失败: {str(e)}")


@router.get("/event-types")
async def get_supported_event_types():
    """
    获取支持的事件类型
    """
    try:
        event_types = [
            {
                "value": event_type.value,
                "name": event_type.name,
                "description": _get_event_type_description(event_type)
            }
            for event_type in EventType
        ]
        
        return {
            "success": True,
            "data": {
                "event_types": event_types,
                "total_count": len(event_types)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件类型失败: {str(e)}")


@router.post("/batch-track")
async def batch_track_events(
    events: List[EventTrackingRequest],
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    批量跟踪用户事件
    """
    try:
        if len(events) > 100:
            raise HTTPException(status_code=400, detail="批量事件数量不能超过100个")
        
        # 获取客户端信息
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # 批量处理事件
        results = []
        for event_req in events:
            event = UserEvent(
                user_id=current_user.id,
                event_type=event_req.event_type,
                timestamp=datetime.now(),
                properties=event_req.properties,
                session_id=event_req.session_id or f"session_{current_user.id}_{datetime.now().timestamp()}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            success = await user_behavior_service.track_event(event)
            results.append({
                "event_type": event_req.event_type.value,
                "success": success,
                "timestamp": event.timestamp.isoformat()
            })
        
        successful_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_events": len(events),
                "successful_count": successful_count,
                "failed_count": len(events) - successful_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量事件跟踪失败: {str(e)}")


def _get_event_type_description(event_type: EventType) -> str:
    """获取事件类型描述"""
    descriptions = {
        EventType.LOGIN: "用户登录",
        EventType.LOGOUT: "用户登出",
        EventType.SEARCH: "搜索操作",
        EventType.CHAT: "聊天对话",
        EventType.UPLOAD: "文件上传",
        EventType.VIEW_DOCUMENT: "查看文档",
        EventType.CREATE_KB: "创建知识库",
        EventType.DELETE_KB: "删除知识库",
        EventType.RATE_ANSWER: "评价答案",
        EventType.EXPORT_DATA: "导出数据"
    }
    return descriptions.get(event_type, "未知事件类型")
