"""
系统管理API端点
"""

from typing import Any, Optional
from datetime import datetime, timedelta

from app.core.security import get_current_superuser
from app.models.user import User
from fastapi import APIRouter, Depends, Query
from loguru import logger

router = APIRouter()


@router.get("/stats", summary="获取系统统计")
async def get_system_stats(
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    获取系统统计信息，用于数据分析页面
    """
    try:
        # 这里应该从数据库获取真实数据
        # 暂时返回模拟数据

        # 模拟基础统计
        stats = {
            "overview": {
                "totalUsers": 1248,
                "totalKnowledgeBases": 45,
                "totalDocuments": 3567,
                "totalConversations": 8934,
                "totalMessages": 15672,
                "avgResponseTime": 1.2,
                "systemUptime": 99.8
            },
            "trends": {
                "userGrowth": [
                    {"date": "2024-01", "users": 800, "documents": 2100, "conversations": 5200},
                    {"date": "2024-02", "users": 950, "documents": 2800, "conversations": 6800},
                    {"date": "2024-03", "users": 1100, "documents": 3200, "conversations": 7900},
                    {"date": "2024-04", "users": 1248, "documents": 3567, "conversations": 8934},
                ],
                "dailyActivity": [
                    {"hour": f"{i:02d}", "searches": 45 + i * 5, "conversations": 23 + i * 3}
                    for i in range(24)
                ]
            },
            "distribution": {
                "documentTypes": [
                    {"name": "PDF", "value": 45, "color": "#8884d8"},
                    {"name": "Word", "value": 30, "color": "#82ca9d"},
                    {"name": "Text", "value": 15, "color": "#ffc658"},
                    {"name": "Markdown", "value": 10, "color": "#ff7300"}
                ],
                "knowledgeBases": [
                    {"name": "技术文档", "documents": 1200, "conversations": 3400},
                    {"name": "业务知识", "documents": 890, "conversations": 2100},
                    {"name": "法律法规", "documents": 567, "conversations": 1800},
                    {"name": "产品手册", "documents": 910, "conversations": 1634}
                ],
                "userActivity": [
                    {"level": "高活跃", "count": 156, "percentage": 12.5},
                    {"level": "中活跃", "count": 487, "percentage": 39.0},
                    {"level": "低活跃", "count": 605, "percentage": 48.5}
                ]
            },
            "performance": {
                "responseTime": [
                    {"date": f"2024-04-{i:02d}", "avgTime": 1.0 + (i % 5) * 0.1, "p95Time": 2.0 + (i % 5) * 0.2}
                    for i in range(1, 8)
                ],
                "searchAccuracy": [
                    {"type": "向量搜索", "accuracy": 85.6, "count": 5678},
                    {"type": "图谱搜索", "accuracy": 78.9, "count": 3456},
                    {"type": "混合搜索", "accuracy": 91.2, "count": 6538}
                ]
            }
        }

        return stats

    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        # 返回默认统计数据
        return {
            "overview": {
                "totalUsers": 0,
                "totalKnowledgeBases": 0,
                "totalDocuments": 0,
                "totalConversations": 0,
                "totalMessages": 0,
                "avgResponseTime": 0,
                "systemUptime": 0
            },
            "trends": {"userGrowth": [], "dailyActivity": []},
            "distribution": {"documentTypes": [], "knowledgeBases": [], "userActivity": []},
            "performance": {"responseTime": [], "searchAccuracy": []}
        }


@router.get("/logs", summary="获取系统日志")
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    获取系统日志
    """
    # 模拟日志数据
    logs = [
        {
            "id": "1",
            "level": "error",
            "message": "嵌入模型API连接失败，请检查网络连接",
            "timestamp": datetime.now().isoformat(),
            "service": "embedding-service"
        },
        {
            "id": "2",
            "level": "warning",
            "message": "Milvus向量数据库响应时间过长",
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "service": "vector-db"
        },
        {
            "id": "3",
            "level": "info",
            "message": "用户登录成功",
            "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "service": "auth-service"
        },
        {
            "id": "4",
            "level": "info",
            "message": "文档处理完成",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "service": "document-processor"
        },
        {
            "id": "5",
            "level": "warning",
            "message": "内存使用率超过60%",
            "timestamp": (datetime.now() - timedelta(minutes=20)).isoformat(),
            "service": "system-monitor"
        }
    ]

    # 根据级别过滤
    if level:
        logs = [log for log in logs if log["level"] == level]

    # 限制数量
    logs = logs[:limit]

    return logs
