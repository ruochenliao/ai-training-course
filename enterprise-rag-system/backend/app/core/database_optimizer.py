"""
数据库查询性能优化工具
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from loguru import logger
from tortoise import Tortoise
from tortoise.queryset import QuerySet
from tortoise.models import Model


@dataclass
class QueryMetrics:
    """查询指标数据类"""
    query_sql: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    table_name: str
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE
    timestamp: float
    has_index: bool = True
    is_slow: bool = False


class DatabaseOptimizer:
    """数据库查询优化器"""
    
    def __init__(self, slow_query_threshold: float = 0.1):
        self.slow_query_threshold = slow_query_threshold  # 慢查询阈值（秒）
        self.query_metrics: List[QueryMetrics] = []
        self.max_metrics = 1000  # 最大保存的查询指标数量
        
        # 查询统计
        self.stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "avg_execution_time": 0,
            "queries_by_table": {},
            "queries_by_type": {},
        }
    
    @asynccontextmanager
    async def monitor_query(self, query_description: str = ""):
        """查询监控上下文管理器"""
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # 记录查询指标
            if execution_time > self.slow_query_threshold:
                logger.warning(f"慢查询检测: {query_description}, 耗时: {execution_time:.3f}s")
            
            # 更新统计信息
            self._update_stats(execution_time)
    
    def _update_stats(self, execution_time: float):
        """更新统计信息"""
        self.stats["total_queries"] += 1
        
        if execution_time > self.slow_query_threshold:
            self.stats["slow_queries"] += 1
        
        # 更新平均执行时间
        total_time = self.stats["avg_execution_time"] * (self.stats["total_queries"] - 1)
        self.stats["avg_execution_time"] = (total_time + execution_time) / self.stats["total_queries"]
    
    async def analyze_query_plan(self, sql: str) -> Dict[str, Any]:
        """分析查询执行计划"""
        try:
            conn = Tortoise.get_connection("default")
            
            # 执行EXPLAIN查询
            explain_sql = f"EXPLAIN {sql}"
            result = await conn.execute_query(explain_sql)
            
            # 解析执行计划
            plan_analysis = {
                "has_index_scan": False,
                "has_full_table_scan": False,
                "estimated_rows": 0,
                "key_used": None,
                "extra_info": []
            }
            
            for row in result[1]:
                if isinstance(row, (list, tuple)) and len(row) >= 10:
                    select_type = row[1] if len(row) > 1 else ""
                    table = row[2] if len(row) > 2 else ""
                    type_scan = row[3] if len(row) > 3 else ""
                    key = row[5] if len(row) > 5 else ""
                    rows = row[8] if len(row) > 8 else 0
                    extra = row[9] if len(row) > 9 else ""
                    
                    if type_scan in ["ALL", "index"]:
                        plan_analysis["has_full_table_scan"] = True
                    elif type_scan in ["range", "ref", "eq_ref"]:
                        plan_analysis["has_index_scan"] = True
                    
                    if key:
                        plan_analysis["key_used"] = key
                    
                    if isinstance(rows, (int, str)):
                        try:
                            plan_analysis["estimated_rows"] += int(rows)
                        except (ValueError, TypeError):
                            pass
                    
                    if extra:
                        plan_analysis["extra_info"].append(extra)
            
            return plan_analysis
            
        except Exception as e:
            logger.error(f"分析查询执行计划失败: {e}")
            return {"error": str(e)}
    
    async def suggest_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """建议索引优化"""
        try:
            conn = Tortoise.get_connection("default")
            
            # 获取表结构
            show_create_sql = f"SHOW CREATE TABLE {table_name}"
            result = await conn.execute_query(show_create_sql)
            
            # 获取表的查询统计
            table_stats_sql = f"""
                SELECT 
                    COLUMN_NAME,
                    CARDINALITY,
                    SUB_PART,
                    INDEX_NAME
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}'
                ORDER BY SEQ_IN_INDEX
            """
            
            index_stats = await conn.execute_query(table_stats_sql)
            
            suggestions = []
            
            # 分析现有索引
            existing_indexes = set()
            if index_stats[1]:
                for row in index_stats[1]:
                    if len(row) >= 4:
                        index_name = row[3]
                        column_name = row[0]
                        existing_indexes.add(f"{index_name}:{column_name}")
            
            # 基于常见查询模式建议索引
            common_patterns = [
                {"columns": ["created_at"], "reason": "时间范围查询优化"},
                {"columns": ["status"], "reason": "状态过滤优化"},
                {"columns": ["owner_id"], "reason": "所有者查询优化"},
                {"columns": ["is_deleted"], "reason": "软删除过滤优化"},
                {"columns": ["status", "is_deleted"], "reason": "复合状态查询优化"},
            ]
            
            for pattern in common_patterns:
                index_key = f"idx_{table_name}_{'_'.join(pattern['columns'])}"
                if not any(index_key in existing for existing in existing_indexes):
                    suggestions.append({
                        "table": table_name,
                        "columns": pattern["columns"],
                        "index_name": index_key,
                        "reason": pattern["reason"],
                        "sql": f"CREATE INDEX {index_key} ON {table_name} ({', '.join(pattern['columns'])})"
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成索引建议失败: {e}")
            return []
    
    async def detect_n_plus_one_queries(self, model_class: type, relation_field: str) -> Dict[str, Any]:
        """检测N+1查询问题"""
        try:
            # 模拟N+1查询检测
            start_time = time.time()
            
            # 获取主记录
            main_records = await model_class.all().limit(10)
            
            # 检测是否存在N+1查询
            individual_queries = 0
            for record in main_records:
                if hasattr(record, relation_field):
                    # 这里会触发额外的查询
                    _ = await getattr(record, relation_field)
                    individual_queries += 1
            
            total_time = time.time() - start_time
            
            # 使用prefetch_related的优化查询
            start_time_optimized = time.time()
            optimized_records = await model_class.all().prefetch_related(relation_field).limit(10)
            optimized_time = time.time() - start_time_optimized
            
            return {
                "model": model_class.__name__,
                "relation_field": relation_field,
                "individual_queries": individual_queries,
                "total_time": total_time,
                "optimized_time": optimized_time,
                "performance_gain": (total_time - optimized_time) / total_time if total_time > 0 else 0,
                "has_n_plus_one": individual_queries > 1,
                "recommendation": f"使用 .prefetch_related('{relation_field}') 优化查询"
            }
            
        except Exception as e:
            logger.error(f"检测N+1查询失败: {e}")
            return {"error": str(e)}
    
    async def optimize_queryset(self, queryset: QuerySet) -> QuerySet:
        """优化查询集"""
        # 自动添加select_related和prefetch_related
        model = queryset.model
        
        # 获取模型的外键字段
        foreign_keys = []
        many_to_many = []
        
        for field_name, field in model._meta.fields_map.items():
            if hasattr(field, 'related_model'):
                if field.field_type in ['ForeignKeyField', 'OneToOneField']:
                    foreign_keys.append(field_name)
                elif field.field_type in ['ManyToManyField', 'BackwardFKRelation']:
                    many_to_many.append(field_name)
        
        # 自动添加select_related（对于外键）
        if foreign_keys:
            queryset = queryset.select_related(*foreign_keys[:3])  # 限制数量避免过度优化
        
        # 自动添加prefetch_related（对于多对多关系）
        if many_to_many:
            queryset = queryset.prefetch_related(*many_to_many[:2])  # 限制数量
        
        return queryset
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """获取慢查询列表"""
        slow_queries = [m for m in self.query_metrics if m.is_slow]
        slow_queries.sort(key=lambda x: x.execution_time, reverse=True)
        return slow_queries[:limit]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return {
            **self.stats,
            "slow_query_threshold": self.slow_query_threshold,
            "total_metrics": len(self.query_metrics),
            "slow_query_rate": (
                self.stats["slow_queries"] / self.stats["total_queries"]
                if self.stats["total_queries"] > 0 else 0
            )
        }
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """运行性能分析"""
        analysis_results = {
            "timestamp": time.time(),
            "query_stats": self.get_query_stats(),
            "slow_queries": self.get_slow_queries(),
            "index_suggestions": {},
            "n_plus_one_detections": {}
        }
        
        # 分析主要表的索引建议
        main_tables = ["users", "knowledge_bases", "documents", "conversations", "messages"]
        for table in main_tables:
            try:
                suggestions = await self.suggest_indexes(table)
                if suggestions:
                    analysis_results["index_suggestions"][table] = suggestions
            except Exception as e:
                logger.error(f"分析表 {table} 索引建议失败: {e}")
        
        # 检测常见的N+1查询问题
        from app.models import User, KnowledgeBase, Document, Conversation
        
        n_plus_one_checks = [
            (User, "roles"),
            (KnowledgeBase, "documents"),
            (Document, "chunks"),
            (Conversation, "messages"),
        ]
        
        for model_class, relation in n_plus_one_checks:
            try:
                detection = await self.detect_n_plus_one_queries(model_class, relation)
                if detection.get("has_n_plus_one"):
                    analysis_results["n_plus_one_detections"][f"{model_class.__name__}.{relation}"] = detection
            except Exception as e:
                logger.error(f"检测 {model_class.__name__}.{relation} N+1查询失败: {e}")
        
        return analysis_results


# 全局数据库优化器实例
db_optimizer = DatabaseOptimizer()


def get_db_optimizer() -> DatabaseOptimizer:
    """获取数据库优化器实例"""
    return db_optimizer


# 查询优化装饰器
def optimize_query(func: Callable) -> Callable:
    """查询优化装饰器"""
    async def wrapper(*args, **kwargs):
        optimizer = get_db_optimizer()
        
        async with optimizer.monitor_query(f"{func.__name__}"):
            result = await func(*args, **kwargs)
            
            # 如果返回的是QuerySet，尝试优化
            if hasattr(result, 'model') and hasattr(result, 'filter'):
                result = await optimizer.optimize_queryset(result)
            
            return result
    
    return wrapper
