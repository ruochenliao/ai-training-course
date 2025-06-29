"""
业务指标监控服务
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from loguru import logger
from tortoise.expressions import Q
from tortoise.functions import Count

from app.models import User, KnowledgeBase, Document, Conversation


@dataclass
class BusinessMetrics:
    """业务指标数据类"""
    timestamp: float
    user_metrics: Dict[str, Any]
    knowledge_base_metrics: Dict[str, Any]
    document_metrics: Dict[str, Any]
    conversation_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]


class BusinessMetricsService:
    """业务指标监控服务"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000
    
    async def collect_all_metrics(self) -> BusinessMetrics:
        """收集所有业务指标"""
        current_time = time.time()
        
        # 并行收集各类指标
        user_metrics = await self._collect_user_metrics()
        kb_metrics = await self._collect_knowledge_base_metrics()
        doc_metrics = await self._collect_document_metrics()
        conv_metrics = await self._collect_conversation_metrics()
        sys_metrics = await self._collect_system_metrics()
        
        metrics = BusinessMetrics(
            timestamp=current_time,
            user_metrics=user_metrics,
            knowledge_base_metrics=kb_metrics,
            document_metrics=doc_metrics,
            conversation_metrics=conv_metrics,
            system_metrics=sys_metrics
        )
        
        # 保存到历史记录
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    async def _collect_user_metrics(self) -> Dict[str, Any]:
        """收集用户相关指标"""
        try:
            # 总用户数
            total_users = await User.all().count()
            
            # 活跃用户数（最近24小时有登录）
            yesterday = datetime.now() - timedelta(days=1)
            active_users = await User.filter(
                last_login__gte=yesterday
            ).count()
            
            # 新注册用户数（最近24小时）
            new_users = await User.filter(
                created_at__gte=yesterday
            ).count()
            
            # 超级用户数
            superusers = await User.filter(is_superuser=True).count()
            
            # 被锁定用户数
            locked_users = await User.filter(
                Q(status="locked") | Q(is_active=False)
            ).count()
            
            # 用户活跃度
            activity_rate = (active_users / total_users) if total_users > 0 else 0
            
            return {
                "total_users": total_users,
                "active_users_24h": active_users,
                "new_users_24h": new_users,
                "superusers": superusers,
                "locked_users": locked_users,
                "activity_rate": round(activity_rate, 4),
                "user_growth_rate": round((new_users / max(total_users - new_users, 1)), 4)
            }
            
        except Exception as e:
            logger.error(f"收集用户指标失败: {e}")
            return {"error": str(e)}
    
    async def _collect_knowledge_base_metrics(self) -> Dict[str, Any]:
        """收集知识库相关指标"""
        try:
            # 总知识库数
            total_kbs = await KnowledgeBase.filter(is_deleted=False).count()
            
            # 公开知识库数
            public_kbs = await KnowledgeBase.filter(
                is_deleted=False,
                visibility="public"
            ).count()
            
            # 私有知识库数
            private_kbs = total_kbs - public_kbs
            
            # 最近24小时创建的知识库
            yesterday = datetime.now() - timedelta(days=1)
            new_kbs = await KnowledgeBase.filter(
                is_deleted=False,
                created_at__gte=yesterday
            ).count()
            
            # 按类型统计
            kb_types = await KnowledgeBase.filter(
                is_deleted=False
            ).group_by("knowledge_type").values(
                "knowledge_type"
            ).annotate(count=Count("id"))
            
            type_distribution = {
                item["knowledge_type"]: item["count"] 
                for item in kb_types
            }
            
            # 平均每个用户的知识库数
            user_count = await User.all().count()
            avg_kbs_per_user = total_kbs / user_count if user_count > 0 else 0
            
            return {
                "total_knowledge_bases": total_kbs,
                "public_knowledge_bases": public_kbs,
                "private_knowledge_bases": private_kbs,
                "new_knowledge_bases_24h": new_kbs,
                "type_distribution": type_distribution,
                "avg_kbs_per_user": round(avg_kbs_per_user, 2),
                "public_ratio": round((public_kbs / total_kbs), 4) if total_kbs > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"收集知识库指标失败: {e}")
            return {"error": str(e)}
    
    async def _collect_document_metrics(self) -> Dict[str, Any]:
        """收集文档相关指标"""
        try:
            # 总文档数
            total_docs = await Document.filter(is_deleted=False).count()
            
            # 最近24小时上传的文档
            yesterday = datetime.now() - timedelta(days=1)
            new_docs = await Document.filter(
                is_deleted=False,
                created_at__gte=yesterday
            ).count()
            
            # 按状态统计
            processing_docs = await Document.filter(
                is_deleted=False,
                status="processing"
            ).count()
            
            processed_docs = await Document.filter(
                is_deleted=False,
                status="processed"
            ).count()
            
            failed_docs = await Document.filter(
                is_deleted=False,
                status="failed"
            ).count()
            
            # 按文件类型统计
            doc_types = await Document.filter(
                is_deleted=False
            ).group_by("file_type").values(
                "file_type"
            ).annotate(count=Count("id"))
            
            type_distribution = {
                item["file_type"]: item["count"] 
                for item in doc_types
            }
            
            # 处理成功率
            success_rate = (processed_docs / total_docs) if total_docs > 0 else 0
            
            # 平均每个知识库的文档数
            kb_count = await KnowledgeBase.filter(is_deleted=False).count()
            avg_docs_per_kb = total_docs / kb_count if kb_count > 0 else 0
            
            return {
                "total_documents": total_docs,
                "new_documents_24h": new_docs,
                "processing_documents": processing_docs,
                "processed_documents": processed_docs,
                "failed_documents": failed_docs,
                "type_distribution": type_distribution,
                "processing_success_rate": round(success_rate, 4),
                "avg_docs_per_kb": round(avg_docs_per_kb, 2)
            }
            
        except Exception as e:
            logger.error(f"收集文档指标失败: {e}")
            return {"error": str(e)}
    
    async def _collect_conversation_metrics(self) -> Dict[str, Any]:
        """收集对话相关指标"""
        try:
            # 总对话数
            total_conversations = await Conversation.all().count()
            
            # 最近24小时的对话
            yesterday = datetime.now() - timedelta(days=1)
            new_conversations = await Conversation.filter(
                created_at__gte=yesterday
            ).count()
            
            # 活跃对话数（最近24小时有更新）
            active_conversations = await Conversation.filter(
                updated_at__gte=yesterday
            ).count()
            
            # 平均每个用户的对话数
            user_count = await User.all().count()
            avg_conversations_per_user = total_conversations / user_count if user_count > 0 else 0
            
            # 对话活跃度
            activity_rate = (active_conversations / total_conversations) if total_conversations > 0 else 0
            
            return {
                "total_conversations": total_conversations,
                "new_conversations_24h": new_conversations,
                "active_conversations_24h": active_conversations,
                "avg_conversations_per_user": round(avg_conversations_per_user, 2),
                "conversation_activity_rate": round(activity_rate, 4)
            }
            
        except Exception as e:
            logger.error(f"收集对话指标失败: {e}")
            return {"error": str(e)}
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统相关指标"""
        try:
            # 获取错误监控指标
            from app.core.error_monitoring import get_error_monitor
            error_monitor = get_error_monitor()
            
            performance_metrics = error_monitor.get_performance_metrics(3600)  # 1小时窗口
            error_stats = error_monitor.get_error_statistics(3600)
            
            # 获取权限缓存指标
            from app.core.permission_cache import get_permission_cache
            permission_cache = get_permission_cache()
            cache_stats = permission_cache.get_stats()
            
            # 获取审计指标
            from app.core.permission_audit import get_permission_auditor
            auditor = get_permission_auditor()
            audit_stats = auditor.get_stats()
            
            return {
                "performance": {
                    "total_requests_1h": performance_metrics.get("total_requests", 0),
                    "avg_response_time": performance_metrics.get("avg_response_time", 0),
                    "p95_response_time": performance_metrics.get("p95_response_time", 0),
                    "error_rate": performance_metrics.get("error_rate", 0)
                },
                "errors": {
                    "total_errors_1h": error_stats.get("total_errors", 0),
                    "error_types": len(error_stats.get("error_breakdown", {}))
                },
                "cache": {
                    "hit_rate": cache_stats.get("hit_rate", 0),
                    "total_cache_size": cache_stats.get("total_cache_size", 0)
                },
                "audit": {
                    "total_audit_logs": audit_stats.get("total_logs", 0),
                    "success_rate": audit_stats.get("success_rate", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {"error": str(e)}
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics_history:
            return {"message": "暂无指标数据"}
        
        # 获取最新指标
        latest_metrics = self.metrics_history[-1]
        
        # 计算时间范围内的趋势
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if len(recent_metrics) < 2:
            return {
                "latest_metrics": latest_metrics,
                "trend_analysis": "数据不足，无法分析趋势"
            }
        
        # 简单的趋势分析
        first_metrics = recent_metrics[0]
        
        user_growth = (
            latest_metrics.user_metrics.get("total_users", 0) - 
            first_metrics.user_metrics.get("total_users", 0)
        )
        
        kb_growth = (
            latest_metrics.knowledge_base_metrics.get("total_knowledge_bases", 0) - 
            first_metrics.knowledge_base_metrics.get("total_knowledge_bases", 0)
        )
        
        doc_growth = (
            latest_metrics.document_metrics.get("total_documents", 0) - 
            first_metrics.document_metrics.get("total_documents", 0)
        )
        
        return {
            "latest_metrics": latest_metrics,
            "trend_analysis": {
                "time_range_hours": hours,
                "user_growth": user_growth,
                "knowledge_base_growth": kb_growth,
                "document_growth": doc_growth,
                "data_points": len(recent_metrics)
            }
        }


# 全局业务指标服务实例
business_metrics_service = BusinessMetricsService()


def get_business_metrics_service() -> BusinessMetricsService:
    """获取业务指标服务实例"""
    return business_metrics_service
