"""
高级分析API
提供用户行为分析、数据洞察、性能监控、趋势预测等接口
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import json

from ...services.analytics_service import analytics_service, EventType
from ...core.dependency import DependPermission

logger = logging.getLogger(__name__)

analytics_router = APIRouter()


class TrackEventRequest(BaseModel):
    """跟踪事件请求"""
    event_type: str = Field(..., description="事件类型")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    properties: Optional[Dict[str, Any]] = Field(None, description="事件属性")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


@analytics_router.post("/events", summary="跟踪事件")
async def track_event(request: TrackEventRequest):
    """
    跟踪用户事件
    
    记录用户行为事件用于分析
    """
    try:
        # 验证事件类型
        try:
            event_type = EventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {request.event_type}"
            )
        
        # 跟踪事件
        await analytics_service.track_event(
            event_type=event_type,
            user_id=request.user_id,
            session_id=request.session_id,
            properties=request.properties,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "message": "事件跟踪成功"
        }
        
    except Exception as e:
        logger.error(f"跟踪事件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/users/{user_id}", summary="获取用户分析")
async def get_user_analytics(
    user_id: str,
    days: int = Query(30, description="分析天数", ge=1, le=365)
):
    """
    获取用户行为分析
    
    返回指定用户的详细行为分析数据
    """
    try:
        analytics_data = await analytics_service.get_user_analytics(
            user_id=user_id,
            days=days
        )
        
        return {
            "success": True,
            "analytics": analytics_data
        }
        
    except Exception as e:
        logger.error(f"获取用户分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/system", summary="获取系统分析")
async def get_system_analytics(
    days: int = Query(7, description="分析天数", ge=1, le=90)
):
    """
    获取系统分析数据
    
    返回系统整体的使用分析数据
    """
    try:
        analytics_data = await analytics_service.get_system_analytics(days=days)
        
        return {
            "success": True,
            "analytics": analytics_data
        }
        
    except Exception as e:
        logger.error(f"获取系统分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/users/{user_id}/profile", summary="获取用户画像")
async def get_user_profile(user_id: str):
    """
    获取用户画像
    
    返回用户的详细画像信息
    """
    try:
        profile = await analytics_service.generate_user_profile(user_id)
        
        if profile:
            return {
                "success": True,
                "profile": profile.to_dict()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="用户画像不存在"
            )
        
    except Exception as e:
        logger.error(f"获取用户画像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/segments", summary="获取用户分群")
async def get_user_segments():
    """
    获取用户分群统计
    
    返回系统的用户分群分析
    """
    try:
        segments = await analytics_service.get_user_segments()
        
        return {
            "success": True,
            "segments": segments
        }
        
    except Exception as e:
        logger.error(f"获取用户分群失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/churn-prediction", summary="用户流失预测")
async def predict_user_churn(
    days_threshold: int = Query(7, description="流失阈值天数", ge=1, le=30)
):
    """
    预测用户流失
    
    返回可能流失的用户列表
    """
    try:
        at_risk_users = await analytics_service.predict_user_churn(
            days_threshold=days_threshold
        )
        
        return {
            "success": True,
            "at_risk_users": at_risk_users,
            "count": len(at_risk_users),
            "threshold_days": days_threshold
        }
        
    except Exception as e:
        logger.error(f"用户流失预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/dashboard", summary="获取分析仪表板")
async def get_analytics_dashboard():
    """
    获取分析仪表板数据
    
    返回综合的分析仪表板数据
    """
    try:
        # 获取系统分析（最近7天）
        system_analytics = await analytics_service.get_system_analytics(days=7)
        
        # 获取用户分群
        user_segments = await analytics_service.get_user_segments()
        
        # 获取流失预测
        churn_prediction = await analytics_service.predict_user_churn(days_threshold=7)
        
        # 构建仪表板数据
        dashboard_data = {
            "overview": {
                "total_events": system_analytics.get("summary", {}).get("total_events", 0),
                "unique_users": system_analytics.get("summary", {}).get("unique_users", 0),
                "avg_daily_events": system_analytics.get("summary", {}).get("avg_daily_events", 0),
                "avg_daily_users": system_analytics.get("summary", {}).get("avg_daily_users", 0)
            },
            "user_segments": user_segments,
            "at_risk_users": {
                "count": len(churn_prediction),
                "high_risk": len([u for u in churn_prediction if u["risk_score"] > 0.7]),
                "medium_risk": len([u for u in churn_prediction if 0.3 < u["risk_score"] <= 0.7]),
                "low_risk": len([u for u in churn_prediction if u["risk_score"] <= 0.3])
            },
            "feature_usage": system_analytics.get("feature_usage", {}),
            "daily_metrics": system_analytics.get("daily_metrics", {}),
            "performance": system_analytics.get("performance_summary", {})
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取分析仪表板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/trends", summary="获取趋势分析")
async def get_trends_analysis(
    metric: str = Query("events", description="分析指标"),
    days: int = Query(30, description="分析天数", ge=7, le=90)
):
    """
    获取趋势分析
    
    返回指定指标的趋势分析数据
    """
    try:
        # 获取系统分析数据
        analytics_data = await analytics_service.get_system_analytics(days=days)
        
        daily_metrics = analytics_data.get("daily_metrics", {})
        
        # 提取趋势数据
        trend_data = []
        for date, metrics in sorted(daily_metrics.items()):
            if metric == "events":
                value = metrics.get("events", 0)
            elif metric == "users":
                value = metrics.get("unique_users", 0)
            elif metric == "sessions":
                value = metrics.get("unique_sessions", 0)
            elif metric == "errors":
                value = metrics.get("errors", 0)
            elif metric == "error_rate":
                value = metrics.get("error_rate", 0)
            else:
                value = 0
            
            trend_data.append({
                "date": date,
                "value": value
            })
        
        # 计算趋势指标
        values = [item["value"] for item in trend_data]
        if len(values) >= 2:
            # 简单的趋势计算
            recent_avg = sum(values[-7:]) / min(7, len(values))  # 最近7天平均
            previous_avg = sum(values[:-7]) / max(1, len(values) - 7)  # 之前的平均
            
            if previous_avg > 0:
                trend_percentage = ((recent_avg - previous_avg) / previous_avg) * 100
            else:
                trend_percentage = 0
            
            trend_direction = "up" if trend_percentage > 5 else "down" if trend_percentage < -5 else "stable"
        else:
            trend_percentage = 0
            trend_direction = "stable"
        
        return {
            "success": True,
            "trends": {
                "metric": metric,
                "period": f"{days}天",
                "data": trend_data,
                "summary": {
                    "trend_direction": trend_direction,
                    "trend_percentage": round(trend_percentage, 2),
                    "total_value": sum(values),
                    "avg_value": sum(values) / len(values) if values else 0,
                    "max_value": max(values) if values else 0,
                    "min_value": min(values) if values else 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/event-types", summary="获取事件类型")
async def get_event_types():
    """
    获取支持的事件类型
    
    返回系统支持的所有事件类型
    """
    try:
        event_types = [
            {
                "type": EventType.USER_LOGIN.value,
                "name": "用户登录",
                "description": "用户登录系统"
            },
            {
                "type": EventType.USER_LOGOUT.value,
                "name": "用户登出",
                "description": "用户登出系统"
            },
            {
                "type": EventType.CHAT_START.value,
                "name": "开始聊天",
                "description": "用户开始聊天会话"
            },
            {
                "type": EventType.CHAT_END.value,
                "name": "结束聊天",
                "description": "用户结束聊天会话"
            },
            {
                "type": EventType.MESSAGE_SENT.value,
                "name": "发送消息",
                "description": "用户发送消息"
            },
            {
                "type": EventType.MESSAGE_RECEIVED.value,
                "name": "接收消息",
                "description": "用户接收消息"
            },
            {
                "type": EventType.VOICE_USED.value,
                "name": "使用语音",
                "description": "用户使用语音功能"
            },
            {
                "type": EventType.IMAGE_GENERATED.value,
                "name": "生成图像",
                "description": "用户生成图像"
            },
            {
                "type": EventType.DOCUMENT_UPLOADED.value,
                "name": "上传文档",
                "description": "用户上传文档"
            },
            {
                "type": EventType.KNOWLEDGE_SEARCHED.value,
                "name": "搜索知识",
                "description": "用户搜索知识库"
            },
            {
                "type": EventType.ERROR_OCCURRED.value,
                "name": "发生错误",
                "description": "系统发生错误"
            },
            {
                "type": EventType.FEATURE_USED.value,
                "name": "使用功能",
                "description": "用户使用特定功能"
            }
        ]
        
        return {
            "success": True,
            "event_types": event_types
        }
        
    except Exception as e:
        logger.error(f"获取事件类型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/reports/user-engagement", summary="用户参与度报告")
async def get_user_engagement_report(
    days: int = Query(30, description="报告天数", ge=7, le=90)
):
    """
    获取用户参与度报告
    
    返回详细的用户参与度分析报告
    """
    try:
        # 获取系统分析数据
        system_analytics = await analytics_service.get_system_analytics(days=days)
        
        # 获取用户分群
        user_segments = await analytics_service.get_user_segments()
        
        # 构建参与度报告
        engagement_report = {
            "period": f"{days}天",
            "summary": system_analytics.get("summary", {}),
            "user_segments": user_segments,
            "daily_activity": system_analytics.get("daily_metrics", {}),
            "feature_adoption": system_analytics.get("feature_usage", {}),
            "engagement_metrics": {
                "active_user_rate": 0,  # 活跃用户率
                "retention_rate": 0,    # 留存率
                "session_frequency": 0, # 会话频率
                "feature_usage_rate": 0 # 功能使用率
            }
        }
        
        # 计算参与度指标
        total_users = user_segments.get("total_users", 0)
        if total_users > 0:
            high_value_users = user_segments.get("segments", {}).get("高价值用户", {}).get("count", 0)
            active_users = user_segments.get("segments", {}).get("活跃用户", {}).get("count", 0)
            
            engagement_report["engagement_metrics"]["active_user_rate"] = (
                (high_value_users + active_users) / total_users * 100
            )
        
        return {
            "success": True,
            "report": engagement_report,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取用户参与度报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/test", summary="测试分析功能")
async def test_analytics():
    """
    测试分析功能
    
    执行基础的分析功能测试
    """
    try:
        test_results = {
            "event_tracking": False,
            "user_analytics": False,
            "system_analytics": False,
            "user_segments": False,
            "errors": []
        }
        
        # 测试事件跟踪
        try:
            await analytics_service.track_event(
                event_type=EventType.FEATURE_USED,
                user_id="test_user",
                properties={"feature_name": "analytics_test"}
            )
            test_results["event_tracking"] = True
        except Exception as e:
            test_results["errors"].append(f"事件跟踪测试失败: {str(e)}")
        
        # 测试用户分析
        try:
            user_analytics = await analytics_service.get_user_analytics("test_user", days=1)
            test_results["user_analytics"] = "error" not in user_analytics
        except Exception as e:
            test_results["errors"].append(f"用户分析测试失败: {str(e)}")
        
        # 测试系统分析
        try:
            system_analytics = await analytics_service.get_system_analytics(days=1)
            test_results["system_analytics"] = "error" not in system_analytics
        except Exception as e:
            test_results["errors"].append(f"系统分析测试失败: {str(e)}")
        
        # 测试用户分群
        try:
            segments = await analytics_service.get_user_segments()
            test_results["user_segments"] = "error" not in segments
        except Exception as e:
            test_results["errors"].append(f"用户分群测试失败: {str(e)}")
        
        # 总体测试结果
        test_results["overall_success"] = (
            test_results["event_tracking"] and
            test_results["user_analytics"] and
            test_results["system_analytics"] and
            test_results["user_segments"]
        )
        
        return {
            "success": True,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"分析功能测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
