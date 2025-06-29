"""
数据库优化API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.core import get_current_user, PermissionChecker
from app.core.database_optimizer import get_db_optimizer
from app.core.database_indexes import get_index_optimizer
from app.core.query_middleware import run_comprehensive_query_analysis, get_connection_pool_monitor
from app.models import User

router = APIRouter()

# 权限检查器
require_db_admin = PermissionChecker("database:admin")
require_db_view = PermissionChecker("database:view")


class QueryStatsResponse(BaseModel):
    """查询统计响应"""
    total_queries: int
    slow_queries: int
    avg_execution_time: float
    slow_query_rate: float
    slow_query_threshold: float


class IndexAnalysisResponse(BaseModel):
    """索引分析响应"""
    analyzed_tables: List[Dict[str, Any]]
    recommended_indexes: List[Dict[str, Any]]
    created_indexes: List[str]
    skipped_indexes: List[Dict[str, Any]]
    errors: List[str]


class ConnectionPoolResponse(BaseModel):
    """连接池响应"""
    total_connections: int
    active_connections: int
    idle_connections: int
    max_connections: int
    connection_errors: int


@router.get("/query-stats", response_model=QueryStatsResponse, summary="获取查询统计")
async def get_query_stats(
    current_user: User = Depends(require_db_view)
) -> Any:
    """
    获取数据库查询统计信息
    """
    optimizer = get_db_optimizer()
    stats = optimizer.get_query_stats()
    
    return QueryStatsResponse(**stats)


@router.get("/slow-queries", summary="获取慢查询列表")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: User = Depends(require_db_view)
) -> Any:
    """
    获取慢查询列表
    """
    optimizer = get_db_optimizer()
    slow_queries = optimizer.get_slow_queries(limit)
    
    # 转换为可序列化格式
    result = []
    for query in slow_queries:
        result.append({
            "query_sql": query.query_sql,
            "execution_time": query.execution_time,
            "rows_examined": query.rows_examined,
            "rows_returned": query.rows_returned,
            "table_name": query.table_name,
            "operation_type": query.operation_type,
            "timestamp": query.timestamp,
            "has_index": query.has_index,
            "is_slow": query.is_slow
        })
    
    return {
        "slow_queries": result,
        "total": len(result),
        "threshold": optimizer.slow_query_threshold
    }


@router.get("/connection-pool", response_model=ConnectionPoolResponse, summary="获取连接池状态")
async def get_connection_pool_status(
    current_user: User = Depends(require_db_view)
) -> Any:
    """
    获取数据库连接池状态
    """
    monitor = get_connection_pool_monitor()
    stats = await monitor.get_connection_pool_stats()
    
    return ConnectionPoolResponse(**stats)


@router.get("/index-analysis", response_model=IndexAnalysisResponse, summary="分析索引优化")
async def analyze_indexes(
    dry_run: bool = Query(True, description="是否为试运行模式"),
    current_user: User = Depends(require_db_admin)
) -> Any:
    """
    分析数据库索引并提供优化建议
    """
    optimizer = get_index_optimizer()
    results = await optimizer.analyze_and_create_indexes(dry_run=dry_run)
    
    return IndexAnalysisResponse(**results)


@router.post("/create-indexes", summary="创建推荐的索引")
async def create_recommended_indexes(
    background_tasks: BackgroundTasks,
    table_names: Optional[List[str]] = None,
    current_user: User = Depends(require_db_admin)
) -> Any:
    """
    创建推荐的数据库索引
    """
    async def create_indexes_task():
        try:
            optimizer = get_index_optimizer()
            
            # 如果指定了表名，只处理这些表
            if table_names:
                filtered_indexes = [
                    idx for idx in optimizer.index_definitions
                    if idx["table"] in table_names
                ]
                original_definitions = optimizer.index_definitions
                optimizer.index_definitions = filtered_indexes
            
            # 执行索引创建
            results = await optimizer.analyze_and_create_indexes(dry_run=False)
            
            # 恢复原始定义
            if table_names:
                optimizer.index_definitions = original_definitions
            
            logger.info(f"索引创建任务完成: 创建了 {len(results['created_indexes'])} 个索引")
            
        except Exception as e:
            logger.error(f"索引创建任务失败: {e}")
    
    # 在后台执行索引创建
    background_tasks.add_task(create_indexes_task)
    
    return {
        "success": True,
        "message": "索引创建任务已启动",
        "tables": table_names or "all",
        "initiated_by": current_user.username
    }


@router.get("/table-indexes/{table_name}", summary="获取表索引信息")
async def get_table_indexes(
    table_name: str,
    current_user: User = Depends(require_db_view)
) -> Any:
    """
    获取指定表的索引信息
    """
    optimizer = get_index_optimizer()
    
    # 获取现有索引
    existing_indexes = await optimizer.check_existing_indexes(table_name)
    
    # 获取索引使用统计
    usage_stats = await optimizer.get_index_usage_stats(table_name)
    
    # 获取推荐的索引
    recommended_indexes = [
        idx for idx in optimizer.index_definitions
        if idx["table"] == table_name
    ]
    
    return {
        "table_name": table_name,
        "existing_indexes": existing_indexes,
        "usage_stats": usage_stats,
        "recommended_indexes": recommended_indexes
    }


@router.post("/analyze-query", summary="分析查询执行计划")
async def analyze_query_plan(
    sql_query: str,
    current_user: User = Depends(require_db_admin)
) -> Any:
    """
    分析SQL查询的执行计划
    """
    optimizer = get_db_optimizer()
    
    try:
        plan_analysis = await optimizer.analyze_query_plan(sql_query)
        
        return {
            "sql_query": sql_query,
            "execution_plan": plan_analysis,
            "recommendations": []
        }
        
    except Exception as e:
        return {
            "sql_query": sql_query,
            "error": str(e),
            "recommendations": ["请检查SQL语法是否正确"]
        }


@router.post("/run-performance-analysis", summary="运行性能分析")
async def run_performance_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_db_admin)
) -> Any:
    """
    运行综合的数据库性能分析
    """
    async def performance_analysis_task():
        try:
            # 运行数据库优化器分析
            db_optimizer = get_db_optimizer()
            db_analysis = await db_optimizer.run_performance_analysis()
            
            # 运行查询分析
            query_analysis = await run_comprehensive_query_analysis()
            
            # 合并分析结果
            combined_results = {
                "timestamp": db_analysis["timestamp"],
                "database_analysis": db_analysis,
                "query_analysis": query_analysis,
                "summary": {
                    "total_slow_queries": len(db_analysis.get("slow_queries", [])),
                    "index_suggestions": len(db_analysis.get("index_suggestions", {})),
                    "n_plus_one_issues": len(db_analysis.get("n_plus_one_detections", {})),
                    "optimization_opportunities": len(query_analysis.get("user_query_optimizations", []))
                }
            }
            
            logger.info(f"性能分析完成: {combined_results['summary']}")
            
        except Exception as e:
            logger.error(f"性能分析任务失败: {e}")
    
    # 在后台执行性能分析
    background_tasks.add_task(performance_analysis_task)
    
    return {
        "success": True,
        "message": "性能分析任务已启动",
        "initiated_by": current_user.username
    }


@router.get("/optimization-recommendations", summary="获取优化建议")
async def get_optimization_recommendations(
    current_user: User = Depends(require_db_view)
) -> Any:
    """
    获取数据库优化建议
    """
    # 获取查询统计
    db_optimizer = get_db_optimizer()
    query_stats = db_optimizer.get_query_stats()
    
    # 获取连接池状态
    pool_monitor = get_connection_pool_monitor()
    pool_stats = await pool_monitor.get_connection_pool_stats()
    
    # 生成优化建议
    recommendations = []
    
    # 慢查询建议
    if query_stats.get("slow_query_rate", 0) > 0.1:  # 慢查询率超过10%
        recommendations.append({
            "category": "查询性能",
            "priority": "high",
            "issue": f"慢查询率过高: {query_stats['slow_query_rate']:.2%}",
            "recommendation": "建议分析慢查询并添加适当的索引",
            "action": "运行索引分析和查询优化"
        })
    
    # 连接池建议
    if pool_stats.get("active_connections", 0) > pool_stats.get("max_connections", 1) * 0.8:
        recommendations.append({
            "category": "连接池",
            "priority": "medium",
            "issue": "数据库连接使用率过高",
            "recommendation": "考虑增加连接池大小或优化连接使用",
            "action": "调整连接池配置"
        })
    
    # 索引建议
    index_optimizer = get_index_optimizer()
    index_analysis = await index_optimizer.analyze_and_create_indexes(dry_run=True)
    
    if index_analysis.get("recommended_indexes"):
        recommendations.append({
            "category": "索引优化",
            "priority": "medium",
            "issue": f"发现 {len(index_analysis['recommended_indexes'])} 个索引优化机会",
            "recommendation": "创建推荐的数据库索引以提升查询性能",
            "action": "执行索引创建任务"
        })
    
    # 通用建议
    recommendations.extend([
        {
            "category": "查询优化",
            "priority": "low",
            "issue": "可能存在N+1查询问题",
            "recommendation": "使用 select_related 和 prefetch_related 优化关联查询",
            "action": "代码审查和查询优化"
        },
        {
            "category": "缓存策略",
            "priority": "low",
            "issue": "频繁查询可以通过缓存优化",
            "recommendation": "对热点数据实现Redis缓存",
            "action": "实现缓存机制"
        }
    ])
    
    return {
        "recommendations": recommendations,
        "stats_summary": {
            "query_stats": query_stats,
            "pool_stats": pool_stats,
            "index_opportunities": len(index_analysis.get("recommended_indexes", []))
        },
        "timestamp": time.time()
    }


@router.post("/optimize-table/{table_name}", summary="优化指定表")
async def optimize_table(
    table_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_db_admin)
) -> Any:
    """
    优化指定的数据库表
    """
    async def optimize_table_task():
        try:
            from tortoise import Tortoise
            
            conn = Tortoise.get_connection("default")
            
            # 执行表优化
            optimize_sql = f"OPTIMIZE TABLE {table_name}"
            await conn.execute_query(optimize_sql)
            
            # 分析表
            analyze_sql = f"ANALYZE TABLE {table_name}"
            await conn.execute_query(analyze_sql)
            
            logger.info(f"表 {table_name} 优化完成")
            
        except Exception as e:
            logger.error(f"表 {table_name} 优化失败: {e}")
    
    # 在后台执行表优化
    background_tasks.add_task(optimize_table_task)
    
    return {
        "success": True,
        "message": f"表 {table_name} 优化任务已启动",
        "table_name": table_name,
        "initiated_by": current_user.username
    }
