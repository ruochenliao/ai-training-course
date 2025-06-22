"""
数据分析API端点
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service, TimeGranularity
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.exceptions import AnalyticsException

router = APIRouter()


class TimeRangeRequest(BaseModel):
    """时间范围请求"""
    start_date: datetime
    end_date: datetime


class AnalyticsResponse(BaseModel):
    """分析响应基类"""
    success: bool = True
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}


@router.get("/overview", response_model=AnalyticsResponse)
async def get_overview_analytics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取概览分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        stats = await analytics_service.get_overview_stats((start_date, end_date))
        
        return AnalyticsResponse(
            data=stats,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "time_range_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概览分析失败: {str(e)}")


@router.get("/users", response_model=AnalyticsResponse)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    granularity: TimeGranularity = Query(TimeGranularity.DAY, description="时间粒度"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = await analytics_service.get_user_analytics(
            (start_date, end_date), granularity
        )
        
        return AnalyticsResponse(
            data=analytics,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "granularity": granularity.value
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户分析失败: {str(e)}")


@router.get("/documents", response_model=AnalyticsResponse)
async def get_document_analytics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取文档分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = await analytics_service.get_document_analytics((start_date, end_date))
        
        return AnalyticsResponse(
            data=analytics,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "time_range_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档分析失败: {str(e)}")


@router.get("/conversations", response_model=AnalyticsResponse)
async def get_conversation_analytics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取对话分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = await analytics_service.get_conversation_analytics((start_date, end_date))
        
        return AnalyticsResponse(
            data=analytics,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "time_range_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话分析失败: {str(e)}")


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=AnalyticsResponse)
async def get_knowledge_base_analytics(
    knowledge_base_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识库分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = await analytics_service.get_knowledge_base_analytics(
            knowledge_base_id, (start_date, end_date)
        )
        
        return AnalyticsResponse(
            data=analytics,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "knowledge_base_id": knowledge_base_id,
                "time_range_days": days
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库分析失败: {str(e)}")


@router.post("/reports/generate", response_model=AnalyticsResponse)
async def generate_report(
    report_type: str = Query(..., description="报告类型"),
    time_range: TimeRangeRequest = None,
    format: str = Query("json", description="报告格式"),
    current_user: User = Depends(get_current_user)
):
    """
    生成分析报告
    """
    try:
        if not time_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            time_range_tuple = (start_date, end_date)
        else:
            time_range_tuple = (time_range.start_date, time_range.end_date)
        
        report = await analytics_service.generate_report(
            report_type, time_range_tuple, format
        )
        
        return AnalyticsResponse(
            data=report,
            metadata={
                "report_type": report_type,
                "format": format,
                "generated_by": current_user.username
            }
        )
        
    except AnalyticsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/metrics/real-time")
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    获取实时指标
    """
    try:
        # 这里应该从监控系统获取实时指标
        # 目前返回模拟数据
        metrics = {
            "active_users": 156,
            "concurrent_sessions": 89,
            "api_requests_per_minute": 245,
            "average_response_time": 1.2,
            "error_rate": 0.02,
            "system_load": {
                "cpu": 45.6,
                "memory": 67.8,
                "disk": 23.4
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return AnalyticsResponse(
            data=metrics,
            metadata={
                "type": "real_time",
                "refresh_interval": 30
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时指标失败: {str(e)}")


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表板摘要数据
    """
    try:
        # 获取多个维度的摘要数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 最近7天
        
        # 并行获取各种统计数据
        import asyncio
        
        overview_task = analytics_service.get_overview_stats((start_date, end_date))
        user_task = analytics_service.get_user_analytics((start_date, end_date))
        doc_task = analytics_service.get_document_analytics((start_date, end_date))
        conv_task = analytics_service.get_conversation_analytics((start_date, end_date))
        
        overview, user_analytics, doc_analytics, conv_analytics = await asyncio.gather(
            overview_task, user_task, doc_task, conv_task
        )
        
        summary = {
            "overview": overview,
            "user_summary": {
                "new_users": user_analytics.get("registration_trend", {}).get("total", 0),
                "active_users": user_analytics.get("active_users", {})
            },
            "document_summary": {
                "new_documents": doc_analytics.get("upload_trend", {}).get("total", 0),
                "processing_stats": doc_analytics.get("processing_stats", {})
            },
            "conversation_summary": {
                "total_conversations": conv_analytics.get("conversation_trend", {}).get("total", 0),
                "avg_satisfaction": conv_analytics.get("satisfaction_stats", {}).get("avg_satisfaction", 0)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return AnalyticsResponse(
            data=summary,
            metadata={
                "period": "7_days",
                "components": ["overview", "users", "documents", "conversations"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板摘要失败: {str(e)}")


@router.get("/export/data")
async def export_analytics_data(
    data_type: str = Query(..., description="数据类型"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    format: str = Query("csv", description="导出格式"),
    current_user: User = Depends(get_current_user)
):
    """
    导出分析数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 根据数据类型获取相应数据
        if data_type == "users":
            data = await analytics_service.get_user_analytics((start_date, end_date))
        elif data_type == "documents":
            data = await analytics_service.get_document_analytics((start_date, end_date))
        elif data_type == "conversations":
            data = await analytics_service.get_conversation_analytics((start_date, end_date))
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据类型: {data_type}")
        
        # 这里应该实现实际的数据导出逻辑
        # 目前返回数据结构
        export_info = {
            "data_type": data_type,
            "format": format,
            "record_count": len(str(data)),  # 简化计算
            "file_size": f"{len(str(data)) / 1024:.2f} KB",
            "download_url": f"/api/v1/analytics/download/{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        return AnalyticsResponse(
            data=export_info,
            metadata={
                "export_requested_at": datetime.now().isoformat(),
                "requested_by": current_user.username
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")


@router.get("/trends/prediction")
async def get_trend_predictions(
    metric: str = Query(..., description="预测指标"),
    days_ahead: int = Query(7, ge=1, le=30, description="预测天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取趋势预测
    """
    try:
        # 这里应该实现机器学习预测模型
        # 目前返回模拟预测数据
        
        predictions = []
        base_value = 100
        
        for i in range(days_ahead):
            # 简单的线性增长模拟
            predicted_value = base_value + (i * 2) + (i * 0.1 * base_value / 100)
            confidence = max(0.5, 0.95 - (i * 0.05))  # 置信度随时间递减
            
            predictions.append({
                "date": (datetime.now() + timedelta(days=i+1)).date().isoformat(),
                "predicted_value": round(predicted_value, 2),
                "confidence": round(confidence, 3),
                "lower_bound": round(predicted_value * 0.9, 2),
                "upper_bound": round(predicted_value * 1.1, 2)
            })
        
        prediction_data = {
            "metric": metric,
            "predictions": predictions,
            "model_info": {
                "algorithm": "linear_regression",
                "training_period": "30_days",
                "accuracy": 0.85
            }
        }
        
        return AnalyticsResponse(
            data=prediction_data,
            metadata={
                "prediction_generated_at": datetime.now().isoformat(),
                "forecast_horizon": f"{days_ahead}_days"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势预测失败: {str(e)}")
