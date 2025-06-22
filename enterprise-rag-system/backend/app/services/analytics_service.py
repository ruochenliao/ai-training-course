"""
数据分析和报表服务
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from app.models.conversation import Conversation
from app.models.knowledge import KnowledgeBase, Document
from app.models.user import User
from loguru import logger

from app.core.exceptions import AnalyticsException


class MetricType(Enum):
    """指标类型"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    RATE = "rate"
    PERCENTAGE = "percentage"


class TimeGranularity(Enum):
    """时间粒度"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class AnalyticsQuery:
    """分析查询"""
    metrics: List[str]
    dimensions: List[str] = None
    filters: Dict[str, Any] = None
    time_range: Tuple[datetime, datetime] = None
    granularity: TimeGranularity = TimeGranularity.DAY
    limit: int = 1000
    
    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = []
        if self.filters is None:
            self.filters = {}


@dataclass
class AnalyticsResult:
    """分析结果"""
    data: List[Dict[str, Any]]
    total: int
    aggregations: Dict[str, float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.aggregations is None:
            self.aggregations = {}
        if self.metadata is None:
            self.metadata = {}


class AnalyticsService:
    """数据分析服务类"""

    def __init__(self):
        """初始化分析服务"""
        # 预定义指标
        self.metrics_config = {
            "user_count": {
                "type": MetricType.COUNT,
                "model": User,
                "field": "id",
                "description": "用户数量"
            },
            "document_count": {
                "type": MetricType.COUNT,
                "model": Document,
                "field": "id",
                "description": "文档数量"
            },
            "conversation_count": {
                "type": MetricType.COUNT,
                "model": Conversation,
                "field": "id",
                "description": "对话数量"
            },
            "knowledge_base_count": {
                "type": MetricType.COUNT,
                "model": KnowledgeBase,
                "field": "id",
                "description": "知识库数量"
            },
            "avg_response_time": {
                "type": MetricType.AVG,
                "model": Conversation,
                "field": "response_time",
                "description": "平均响应时间"
            },
            "user_satisfaction": {
                "type": MetricType.AVG,
                "model": Conversation,
                "field": "satisfaction_score",
                "description": "用户满意度"
            }
        }

        logger.info("数据分析服务初始化完成")
    
    async def get_overview_stats(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取概览统计"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 基础统计
            stats = {}
            
            # 用户统计
            user_count = await User.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            total_users = await User.all().count()
            
            # 文档统计
            document_count = await Document.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            total_documents = await Document.all().count()
            
            # 知识库统计
            kb_count = await KnowledgeBase.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            total_kbs = await KnowledgeBase.all().count()
            
            # 对话统计
            conversation_count = await Conversation.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            total_conversations = await Conversation.all().count()
            
            stats = {
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "users": {
                    "new": user_count,
                    "total": total_users,
                    "growth_rate": self._calculate_growth_rate(user_count, total_users)
                },
                "documents": {
                    "new": document_count,
                    "total": total_documents,
                    "growth_rate": self._calculate_growth_rate(document_count, total_documents)
                },
                "knowledge_bases": {
                    "new": kb_count,
                    "total": total_kbs,
                    "growth_rate": self._calculate_growth_rate(kb_count, total_kbs)
                },
                "conversations": {
                    "new": conversation_count,
                    "total": total_conversations,
                    "growth_rate": self._calculate_growth_rate(conversation_count, total_conversations)
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取概览统计失败: {e}")
            raise AnalyticsException(f"获取概览统计失败: {e}")
    
    async def get_user_analytics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        granularity: TimeGranularity = TimeGranularity.DAY
    ) -> Dict[str, Any]:
        """获取用户分析数据"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 用户注册趋势
            registration_trend = await self._get_time_series_data(
                User, "created_at", start_date, end_date, granularity
            )
            
            # 活跃用户统计
            active_users = await self._get_active_users_stats(start_date, end_date)
            
            # 用户行为分析
            user_behavior = await self._get_user_behavior_stats(start_date, end_date)
            
            return {
                "registration_trend": registration_trend,
                "active_users": active_users,
                "user_behavior": user_behavior,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户分析失败: {e}")
            raise AnalyticsException(f"获取用户分析失败: {e}")
    
    async def get_document_analytics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取文档分析数据"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 文档上传趋势
            upload_trend = await self._get_time_series_data(
                Document, "created_at", start_date, end_date, TimeGranularity.DAY
            )
            
            # 文档类型分布
            type_distribution = await self._get_document_type_distribution(start_date, end_date)
            
            # 文档处理状态
            processing_stats = await self._get_document_processing_stats(start_date, end_date)
            
            # 文档大小统计
            size_stats = await self._get_document_size_stats(start_date, end_date)
            
            return {
                "upload_trend": upload_trend,
                "type_distribution": type_distribution,
                "processing_stats": processing_stats,
                "size_stats": size_stats,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取文档分析失败: {e}")
            raise AnalyticsException(f"获取文档分析失败: {e}")
    
    async def get_conversation_analytics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取对话分析数据"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 对话量趋势
            conversation_trend = await self._get_time_series_data(
                Conversation, "created_at", start_date, end_date, TimeGranularity.DAY
            )
            
            # 响应时间分析
            response_time_stats = await self._get_response_time_stats(start_date, end_date)
            
            # 满意度分析
            satisfaction_stats = await self._get_satisfaction_stats(start_date, end_date)
            
            # 热门问题分析
            popular_questions = await self._get_popular_questions(start_date, end_date)
            
            return {
                "conversation_trend": conversation_trend,
                "response_time_stats": response_time_stats,
                "satisfaction_stats": satisfaction_stats,
                "popular_questions": popular_questions,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取对话分析失败: {e}")
            raise AnalyticsException(f"获取对话分析失败: {e}")
    
    async def get_knowledge_base_analytics(
        self,
        knowledge_base_id: Optional[int] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """获取知识库分析数据"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 知识库使用统计
            usage_stats = await self._get_kb_usage_stats(knowledge_base_id, start_date, end_date)
            
            # 文档分布
            document_distribution = await self._get_kb_document_distribution(knowledge_base_id)
            
            # 查询热度
            query_heatmap = await self._get_kb_query_heatmap(knowledge_base_id, start_date, end_date)
            
            return {
                "usage_stats": usage_stats,
                "document_distribution": document_distribution,
                "query_heatmap": query_heatmap,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"获取知识库分析失败: {e}")
            raise AnalyticsException(f"获取知识库分析失败: {e}")
    
    async def generate_report(
        self,
        report_type: str,
        time_range: Tuple[datetime, datetime],
        format: str = "json"
    ) -> Dict[str, Any]:
        """生成分析报告"""
        try:
            report_data = {}
            
            if report_type == "comprehensive":
                # 综合报告
                report_data = {
                    "overview": await self.get_overview_stats(time_range),
                    "users": await self.get_user_analytics(time_range),
                    "documents": await self.get_document_analytics(time_range),
                    "conversations": await self.get_conversation_analytics(time_range),
                    "knowledge_bases": await self.get_knowledge_base_analytics(None, time_range)
                }
            elif report_type == "user":
                report_data = await self.get_user_analytics(time_range)
            elif report_type == "document":
                report_data = await self.get_document_analytics(time_range)
            elif report_type == "conversation":
                report_data = await self.get_conversation_analytics(time_range)
            else:
                raise AnalyticsException(f"不支持的报告类型: {report_type}")
            
            # 添加报告元数据
            report_data["metadata"] = {
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "format": format
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise AnalyticsException(f"生成报告失败: {e}")
    
    # 私有辅助方法
    async def _get_time_series_data(
        self,
        model_class,
        date_field: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity
    ) -> List[Dict[str, Any]]:
        """获取时间序列数据"""
        try:
            # 使用Tortoise ORM进行查询
            # 由于Tortoise ORM对复杂的日期分组支持有限，我们先获取数据然后在Python中处理
            records = await model_class.filter(
                **{f"{date_field}__gte": start_date, f"{date_field}__lte": end_date}
            ).values(date_field)

            # 在Python中按粒度分组
            grouped_data = {}
            for record in records:
                date_value = record[date_field]

                # 根据粒度格式化日期
                if granularity == TimeGranularity.HOUR:
                    period = date_value.strftime("%Y-%m-%d %H:00:00")
                elif granularity == TimeGranularity.DAY:
                    period = date_value.strftime("%Y-%m-%d")
                elif granularity == TimeGranularity.WEEK:
                    period = f"{date_value.year}-W{date_value.isocalendar()[1]:02d}"
                elif granularity == TimeGranularity.MONTH:
                    period = date_value.strftime("%Y-%m")
                elif granularity == TimeGranularity.QUARTER:
                    quarter = (date_value.month - 1) // 3 + 1
                    period = f"{date_value.year}-Q{quarter}"
                else:  # YEAR
                    period = date_value.strftime("%Y")

                grouped_data[period] = grouped_data.get(period, 0) + 1

            # 转换为列表格式并排序
            result = [{"period": period, "count": count} for period, count in grouped_data.items()]
            result.sort(key=lambda x: x["period"])

            return result

        except Exception as e:
            logger.error(f"获取时间序列数据失败: {e}")
            return []
    
    async def _get_active_users_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取活跃用户统计"""
        # 这里需要根据实际的用户活动表来实现
        # 目前返回模拟数据
        return {
            "daily_active": 150,
            "weekly_active": 800,
            "monthly_active": 2500
        }
    
    async def _get_user_behavior_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取用户行为统计"""
        # 模拟用户行为数据
        return {
            "avg_session_duration": 25.5,
            "avg_queries_per_session": 3.2,
            "bounce_rate": 0.15,
            "return_rate": 0.65
        }
    
    def _calculate_growth_rate(self, new_count: int, total_count: int) -> float:
        """计算增长率"""
        if total_count == 0:
            return 0.0
        return (new_count / total_count) * 100
    
    async def _get_document_type_distribution(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取文档类型分布"""
        documents = await Document.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values("file_type")
        
        # 统计各类型数量
        type_counts = {}
        for doc in documents:
            file_type = doc["file_type"]
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        return [
            {"type": file_type, "count": count}
            for file_type, count in type_counts.items()
        ]
    
    async def _get_document_processing_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取文档处理统计"""
        documents = await Document.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values("status")
        
        status_counts = {}
        for doc in documents:
            status = doc["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total = len(documents)
        return {
            "total": total,
            "processed": status_counts.get("processed", 0),
            "processing": status_counts.get("processing", 0),
            "failed": status_counts.get("failed", 0),
            "pending": status_counts.get("pending", 0),
            "success_rate": (status_counts.get("processed", 0) / total * 100) if total > 0 else 0
        }
    
    async def _get_document_size_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取文档大小统计"""
        documents = await Document.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values("file_size")
        
        sizes = [doc["file_size"] for doc in documents if doc["file_size"]]
        
        if not sizes:
            return {"total_size": 0, "avg_size": 0, "max_size": 0, "min_size": 0}
        
        return {
            "total_size": sum(sizes),
            "avg_size": sum(sizes) / len(sizes),
            "max_size": max(sizes),
            "min_size": min(sizes)
        }
    
    async def _get_response_time_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取响应时间统计"""
        # 模拟响应时间数据
        return {
            "avg_response_time": 1.5,
            "p50_response_time": 1.2,
            "p95_response_time": 3.8,
            "p99_response_time": 8.5
        }
    
    async def _get_satisfaction_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取满意度统计"""
        # 模拟满意度数据
        return {
            "avg_satisfaction": 4.2,
            "satisfaction_distribution": {
                "5": 45,
                "4": 30,
                "3": 15,
                "2": 7,
                "1": 3
            }
        }
    
    async def _get_popular_questions(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取热门问题"""
        # 模拟热门问题数据
        return [
            {"question": "如何使用这个系统？", "count": 156},
            {"question": "支持哪些文件格式？", "count": 134},
            {"question": "如何上传文档？", "count": 98},
            {"question": "系统有什么功能？", "count": 87},
            {"question": "如何创建知识库？", "count": 76}
        ][:limit]
    
    async def _get_kb_usage_stats(
        self,
        knowledge_base_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取知识库使用统计"""
        # 模拟知识库使用数据
        return {
            "total_queries": 1250,
            "unique_users": 89,
            "avg_queries_per_user": 14.0,
            "most_active_time": "14:00-16:00"
        }
    
    async def _get_kb_document_distribution(
        self,
        knowledge_base_id: Optional[int]
    ) -> Dict[str, Any]:
        """获取知识库文档分布"""
        # 模拟文档分布数据
        return {
            "total_documents": 245,
            "by_type": {
                "pdf": 120,
                "docx": 85,
                "txt": 25,
                "pptx": 15
            },
            "by_size": {
                "small": 180,
                "medium": 50,
                "large": 15
            }
        }
    
    async def _get_kb_query_heatmap(
        self,
        knowledge_base_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取知识库查询热力图数据"""
        # 模拟查询热力图数据
        heatmap_data = []
        for hour in range(24):
            for day in range(7):
                heatmap_data.append({
                    "hour": hour,
                    "day": day,
                    "count": np.random.randint(0, 50)
                })
        return heatmap_data


# 全局分析服务实例
analytics_service = AnalyticsService()
