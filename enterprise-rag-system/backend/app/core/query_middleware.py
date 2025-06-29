"""
数据库查询监控中间件
"""

import time
import asyncio
from typing import Callable, Any
from contextlib import asynccontextmanager

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from tortoise import Tortoise

from app.core.database_optimizer import get_db_optimizer


class QueryMonitoringMiddleware(BaseHTTPMiddleware):
    """数据库查询监控中间件"""
    
    def __init__(self, app, enable_monitoring: bool = True, log_slow_queries: bool = True):
        super().__init__(app)
        self.enable_monitoring = enable_monitoring
        self.log_slow_queries = log_slow_queries
        self.db_optimizer = get_db_optimizer()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enable_monitoring:
            return await call_next(request)
        
        # 记录请求开始时的数据库连接状态
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        # 在请求处理前获取查询统计
        initial_stats = self.db_optimizer.get_query_stats()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算请求处理时间
            process_time = time.time() - start_time
            
            # 获取请求处理后的查询统计
            final_stats = self.db_optimizer.get_query_stats()
            
            # 计算本次请求的查询统计
            queries_in_request = final_stats["total_queries"] - initial_stats["total_queries"]
            slow_queries_in_request = final_stats["slow_queries"] - initial_stats["slow_queries"]
            
            # 记录查询统计
            if queries_in_request > 0:
                logger.debug(
                    f"请求查询统计: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "queries_count": queries_in_request,
                        "slow_queries_count": slow_queries_in_request,
                        "process_time": process_time,
                        "avg_query_time": (
                            (final_stats["avg_execution_time"] * final_stats["total_queries"] - 
                             initial_stats["avg_execution_time"] * initial_stats["total_queries"]) / 
                            queries_in_request if queries_in_request > 0 else 0
                        )
                    }
                )
            
            # 如果有慢查询，记录警告
            if slow_queries_in_request > 0 and self.log_slow_queries:
                logger.warning(
                    f"请求包含慢查询: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "slow_queries_count": slow_queries_in_request,
                        "total_queries": queries_in_request,
                        "process_time": process_time
                    }
                )
            
            # 添加查询统计到响应头（开发环境）
            if hasattr(request.app.state, "debug") and request.app.state.debug:
                response.headers["X-DB-Queries"] = str(queries_in_request)
                response.headers["X-DB-Slow-Queries"] = str(slow_queries_in_request)
                response.headers["X-DB-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # 记录异常情况下的查询统计
            process_time = time.time() - start_time
            final_stats = self.db_optimizer.get_query_stats()
            queries_in_request = final_stats["total_queries"] - initial_stats["total_queries"]
            
            logger.error(
                f"请求异常时的查询统计: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "queries_count": queries_in_request,
                    "process_time": process_time,
                    "exception": str(e)
                }
            )
            
            raise


class DatabaseConnectionPoolMonitor:
    """数据库连接池监控器"""
    
    def __init__(self):
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "max_connections": 0,
            "connection_errors": 0,
        }
    
    async def get_connection_pool_stats(self) -> dict:
        """获取连接池统计信息"""
        try:
            # 获取Tortoise连接池信息
            connections = Tortoise.get_connection("default")
            
            if hasattr(connections, '_pool'):
                pool = connections._pool
                
                self.connection_stats.update({
                    "total_connections": getattr(pool, 'size', 0),
                    "active_connections": getattr(pool, '_used', 0),
                    "idle_connections": getattr(pool, '_queue', {}).qsize() if hasattr(getattr(pool, '_queue', None), 'qsize') else 0,
                    "max_connections": getattr(pool, 'maxsize', 0),
                })
            
            return self.connection_stats
            
        except Exception as e:
            logger.error(f"获取连接池统计失败: {e}")
            return {"error": str(e)}
    
    async def check_connection_health(self) -> dict:
        """检查数据库连接健康状态"""
        try:
            start_time = time.time()
            
            # 执行简单的健康检查查询
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1")
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"数据库连接健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }


# 查询优化工具函数
async def optimize_user_queries():
    """优化用户相关查询"""
    from app.models import User
    
    # 常见的用户查询优化
    optimizations = []
    
    # 1. 用户角色查询优化
    try:
        # 原始查询（可能存在N+1问题）
        start_time = time.time()
        users = await User.all().limit(10)
        for user in users:
            roles = await user.get_roles()  # 这里可能触发N+1查询
        original_time = time.time() - start_time
        
        # 优化后的查询
        start_time = time.time()
        from app.models.rbac import UserRole
        users_with_roles = await User.all().prefetch_related("userrole_set__role").limit(10)
        optimized_time = time.time() - start_time
        
        optimizations.append({
            "query_type": "user_roles",
            "original_time": original_time,
            "optimized_time": optimized_time,
            "improvement": (original_time - optimized_time) / original_time if original_time > 0 else 0,
            "recommendation": "使用 prefetch_related('userrole_set__role') 预加载角色信息"
        })
        
    except Exception as e:
        logger.error(f"用户角色查询优化分析失败: {e}")
    
    # 2. 用户权限查询优化
    try:
        # 分析用户权限查询
        start_time = time.time()
        users = await User.all().limit(5)
        for user in users:
            permissions = await user.get_permissions()  # 复杂的权限查询
        original_time = time.time() - start_time
        
        optimizations.append({
            "query_type": "user_permissions",
            "original_time": original_time,
            "recommendation": "考虑实现权限缓存机制，避免重复查询"
        })
        
    except Exception as e:
        logger.error(f"用户权限查询优化分析失败: {e}")
    
    return optimizations


async def optimize_knowledge_base_queries():
    """优化知识库相关查询"""
    from app.models import KnowledgeBase, Document
    
    optimizations = []
    
    # 1. 知识库文档查询优化
    try:
        # 原始查询
        start_time = time.time()
        kbs = await KnowledgeBase.all().limit(5)
        for kb in kbs:
            documents = await kb.get_documents()  # 可能的N+1查询
        original_time = time.time() - start_time
        
        # 优化后的查询
        start_time = time.time()
        kbs_with_docs = await KnowledgeBase.all().prefetch_related("documents").limit(5)
        optimized_time = time.time() - start_time
        
        optimizations.append({
            "query_type": "knowledge_base_documents",
            "original_time": original_time,
            "optimized_time": optimized_time,
            "improvement": (original_time - optimized_time) / original_time if original_time > 0 else 0,
            "recommendation": "使用 prefetch_related('documents') 预加载文档信息"
        })
        
    except Exception as e:
        logger.error(f"知识库文档查询优化分析失败: {e}")
    
    # 2. 文档统计查询优化
    try:
        # 分析文档统计查询
        start_time = time.time()
        
        # 使用聚合查询替代循环查询
        from tortoise.functions import Count, Sum
        kb_stats = await KnowledgeBase.annotate(
            doc_count=Count("documents"),
            total_size=Sum("documents__file_size")
        ).all()
        
        optimized_time = time.time() - start_time
        
        optimizations.append({
            "query_type": "knowledge_base_statistics",
            "optimized_time": optimized_time,
            "recommendation": "使用聚合查询 annotate(Count, Sum) 替代循环统计"
        })
        
    except Exception as e:
        logger.error(f"知识库统计查询优化分析失败: {e}")
    
    return optimizations


async def run_comprehensive_query_analysis():
    """运行综合查询分析"""
    logger.info("开始运行综合查询分析...")
    
    analysis_results = {
        "timestamp": time.time(),
        "user_query_optimizations": [],
        "knowledge_base_optimizations": [],
        "connection_pool_stats": {},
        "general_recommendations": []
    }
    
    # 数据库连接池监控
    pool_monitor = DatabaseConnectionPoolMonitor()
    analysis_results["connection_pool_stats"] = await pool_monitor.get_connection_pool_stats()
    
    # 用户查询优化分析
    try:
        user_optimizations = await optimize_user_queries()
        analysis_results["user_query_optimizations"] = user_optimizations
    except Exception as e:
        logger.error(f"用户查询优化分析失败: {e}")
    
    # 知识库查询优化分析
    try:
        kb_optimizations = await optimize_knowledge_base_queries()
        analysis_results["knowledge_base_optimizations"] = kb_optimizations
    except Exception as e:
        logger.error(f"知识库查询优化分析失败: {e}")
    
    # 通用建议
    analysis_results["general_recommendations"] = [
        {
            "category": "索引优化",
            "recommendation": "为经常查询的字段添加数据库索引",
            "priority": "high",
            "impact": "显著提升查询性能"
        },
        {
            "category": "查询优化",
            "recommendation": "使用 select_related 和 prefetch_related 避免N+1查询",
            "priority": "high",
            "impact": "减少数据库查询次数"
        },
        {
            "category": "缓存策略",
            "recommendation": "对频繁查询的数据实现缓存机制",
            "priority": "medium",
            "impact": "减少数据库负载"
        },
        {
            "category": "分页优化",
            "recommendation": "对大数据集查询使用游标分页替代偏移分页",
            "priority": "medium",
            "impact": "提升大数据集查询性能"
        }
    ]
    
    logger.info("综合查询分析完成")
    return analysis_results


# 全局连接池监控器
connection_pool_monitor = DatabaseConnectionPoolMonitor()


def get_connection_pool_monitor() -> DatabaseConnectionPoolMonitor:
    """获取连接池监控器实例"""
    return connection_pool_monitor
