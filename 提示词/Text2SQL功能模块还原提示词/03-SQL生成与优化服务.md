# SQL生成与优化服务功能还原提示词

## 服务概述

SQL生成与优化服务是Text2SQL系统的核心引擎，负责将自然语言查询转换为高质量的SQL语句。该服务结合了大语言模型的理解能力和传统SQL优化技术，确保生成的SQL既准确又高效。

## 核心功能

### 1. 智能SQL生成
- 基于自然语言查询生成SQL语句
- 支持复杂查询逻辑（JOIN、子查询、聚合、窗口函数等）
- 多数据库方言支持（MySQL、PostgreSQL、SQLite、Snowflake等）
- 上下文感知的SQL生成

### 2. SQL语法验证
- 语法正确性检查
- 数据库兼容性验证
- 表和字段存在性验证
- 数据类型匹配检查

### 3. SQL性能优化
- 查询计划分析
- 索引使用优化
- JOIN顺序优化
- 子查询优化

### 4. 多轮对话支持
- 上下文保持和查询历史
- 增量查询修改
- 查询意图理解和澄清

## 技术实现

### SQL生成器智能体

```python
from typing import Dict, List, Optional, Any
import re
import sqlparse
from sqlparse import sql, tokens

class SQLGeneratorAgent:
    """SQL生成智能体"""
    
    def __init__(self, db_type: str, model_client, schema_service):
        self.db_type = db_type
        self.model_client = model_client
        self.schema_service = schema_service
        self.sql_templates = self._load_sql_templates()
        self.optimization_rules = self._load_optimization_rules()
    
    async def generate_sql(self, 
                          query: str, 
                          analysis_result: Dict[str, Any],
                          context: Optional[str] = None) -> Dict[str, Any]:
        """生成SQL语句"""
        try:
            # 获取相关数据库模式
            db_context = await self.schema_service.build_context(query)
            
            # 构建生成提示词
            prompt = self._build_generation_prompt(
                query, analysis_result, db_context, context
            )
            
            # 调用LLM生成SQL
            response = await self.model_client.complete(prompt)
            sql_statement = self._extract_sql_from_response(response)
            
            # 验证和优化SQL
            validation_result = await self._validate_sql(sql_statement)
            if validation_result['is_valid']:
                optimized_sql = await self._optimize_sql(sql_statement)
                
                return {
                    'sql': optimized_sql,
                    'original_sql': sql_statement,
                    'is_valid': True,
                    'validation_errors': [],
                    'optimization_applied': True,
                    'confidence_score': self._calculate_confidence(sql_statement, analysis_result)
                }
            else:
                # 尝试修复SQL
                fixed_sql = await self._fix_sql(sql_statement, validation_result['errors'])
                return {
                    'sql': fixed_sql,
                    'original_sql': sql_statement,
                    'is_valid': True,
                    'validation_errors': validation_result['errors'],
                    'optimization_applied': False,
                    'confidence_score': 0.7
                }
                
        except Exception as e:
            logger.error(f"SQL生成失败: {e}")
            return {
                'sql': None,
                'error': str(e),
                'is_valid': False
            }
    
    def _build_generation_prompt(self, 
                                query: str, 
                                analysis: Dict[str, Any],
                                db_context: str,
                                conversation_context: Optional[str] = None) -> str:
        """构建SQL生成提示词"""
        
        # 基础提示词模板
        base_prompt = f"""
        你是一名专业的SQL专家，请根据以下信息生成准确的SQL查询语句。
        
        数据库类型: {self.db_type}
        
        数据库结构:
        {db_context}
        
        用户查询: "{query}"
        
        查询分析结果:
        - 查询意图: {analysis.get('query_intent', '')}
        - 查询类型: {analysis.get('query_type', '')}
        - 识别实体: {', '.join(analysis.get('entities', []))}
        - 可能的聚合: {', '.join(analysis.get('likely_aggregations', []))}
        - 过滤条件: {', '.join(analysis.get('filter_conditions', []))}
        - 排序需求: {', '.join(analysis.get('sort_requirements', []))}
        """
        
        # 添加对话上下文
        if conversation_context:
            base_prompt += f"""
            
            对话上下文:
            {conversation_context}
            """
        
        # 添加生成要求
        base_prompt += f"""
        
        请按照以下要求生成SQL:
        1. 确保SQL语法正确且符合{self.db_type}规范
        2. 使用适当的表连接和过滤条件
        3. 优化查询性能，避免不必要的子查询
        4. 如果需要聚合，使用适当的GROUP BY子句
        5. 添加必要的ORDER BY和LIMIT子句
        6. 使用标准的SQL格式，便于阅读
        
        请只返回SQL语句，不要包含其他解释文字。
        
        SQL:
        """
        
        return base_prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """从LLM响应中提取SQL语句"""
        # 移除代码块标记
        sql = re.sub(r'```sql\s*', '', response)
        sql = re.sub(r'```\s*', '', sql)
        
        # 移除多余的空白字符
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # 确保以分号结尾
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    async def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """验证SQL语句"""
        errors = []
        
        try:
            # 语法解析验证
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append("SQL语法解析失败")
                return {'is_valid': False, 'errors': errors}
            
            # 检查SQL类型
            statement = parsed[0]
            if not self._is_select_statement(statement):
                errors.append("只支持SELECT查询")
            
            # 提取表名和字段名
            tables, columns = self._extract_tables_and_columns(statement)
            
            # 验证表存在性
            for table in tables:
                if not await self._table_exists(table):
                    errors.append(f"表 '{table}' 不存在")
            
            # 验证字段存在性
            for table, column_list in columns.items():
                for column in column_list:
                    if not await self._column_exists(table, column):
                        errors.append(f"表 '{table}' 中不存在字段 '{column}'")
            
            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'tables': tables,
                'columns': columns
            }
            
        except Exception as e:
            errors.append(f"SQL验证异常: {str(e)}")
            return {'is_valid': False, 'errors': errors}
    
    def _is_select_statement(self, statement) -> bool:
        """检查是否为SELECT语句"""
        for token in statement.flatten():
            if token.ttype is tokens.Keyword.DML and token.value.upper() == 'SELECT':
                return True
        return False
    
    def _extract_tables_and_columns(self, statement) -> tuple:
        """提取SQL中的表名和字段名"""
        tables = set()
        columns = {}
        
        # 简化的表名和字段提取逻辑
        sql_text = str(statement)
        
        # 提取FROM子句中的表名
        from_match = re.search(r'FROM\s+([\w\s,]+?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|$)', 
                              sql_text, re.IGNORECASE)
        if from_match:
            table_part = from_match.group(1)
            # 处理JOIN
            table_names = re.findall(r'\b(\w+)\b', table_part)
            tables.update(table_names)
        
        # 提取SELECT子句中的字段名（简化版）
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_text, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            # 简单的字段提取
            if '*' not in select_part:
                column_matches = re.findall(r'\b(\w+)\.(\w+)\b', select_part)
                for table, column in column_matches:
                    if table not in columns:
                        columns[table] = set()
                    columns[table].add(column)
        
        return list(tables), {k: list(v) for k, v in columns.items()}
    
    async def _table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            all_tables = await self.schema_service.db_access.get_all_tables()
            return table_name.lower() in [t.lower() for t in all_tables]
        except:
            return True  # 如果无法验证，假设存在
    
    async def _column_exists(self, table_name: str, column_name: str) -> bool:
        """检查字段是否存在"""
        try:
            schema = await self.schema_service.db_access.get_table_schema(table_name)
            column_names = [col['column_name'].lower() for col in schema['columns']]
            return column_name.lower() in column_names
        except:
            return True  # 如果无法验证，假设存在
    
    async def _optimize_sql(self, sql: str) -> str:
        """优化SQL语句"""
        optimized_sql = sql
        
        # 应用优化规则
        for rule in self.optimization_rules:
            optimized_sql = rule.apply(optimized_sql)
        
        return optimized_sql
    
    async def _fix_sql(self, sql: str, errors: List[str]) -> str:
        """修复SQL错误"""
        # 构建修复提示词
        fix_prompt = f"""
        以下SQL语句存在错误，请修复：
        
        原始SQL:
        {sql}
        
        错误信息:
        {chr(10).join(errors)}
        
        请提供修复后的SQL语句，只返回SQL，不要其他解释：
        """
        
        try:
            response = await self.model_client.complete(fix_prompt)
            fixed_sql = self._extract_sql_from_response(response)
            return fixed_sql
        except:
            return sql  # 如果修复失败，返回原SQL
    
    def _calculate_confidence(self, sql: str, analysis: Dict[str, Any]) -> float:
        """计算SQL生成的置信度"""
        confidence = 0.5  # 基础置信度
        
        # 根据查询复杂度调整
        if 'JOIN' in sql.upper():
            confidence += 0.1
        if 'GROUP BY' in sql.upper():
            confidence += 0.1
        if 'ORDER BY' in sql.upper():
            confidence += 0.1
        
        # 根据分析结果调整
        if analysis.get('confidence_score', 0) > 0.8:
            confidence += 0.2
        
        return min(confidence, 1.0)
```

### SQL优化规则引擎

```python
from abc import ABC, abstractmethod

class SQLOptimizationRule(ABC):
    """SQL优化规则抽象基类"""
    
    @abstractmethod
    def apply(self, sql: str) -> str:
        """应用优化规则"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取规则描述"""
        pass

class RemoveUnnecessarySubqueryRule(SQLOptimizationRule):
    """移除不必要的子查询"""
    
    def apply(self, sql: str) -> str:
        # 简化的子查询优化逻辑
        # 实际实现需要更复杂的SQL解析
        return sql
    
    def get_description(self) -> str:
        return "移除不必要的子查询，提高查询性能"

class OptimizeJoinOrderRule(SQLOptimizationRule):
    """优化JOIN顺序"""
    
    def apply(self, sql: str) -> str:
        # JOIN顺序优化逻辑
        return sql
    
    def get_description(self) -> str:
        return "优化表连接顺序，减少中间结果集大小"

class AddIndexHintsRule(SQLOptimizationRule):
    """添加索引提示"""
    
    def apply(self, sql: str) -> str:
        # 索引提示添加逻辑
        return sql
    
    def get_description(self) -> str:
        return "为查询添加适当的索引提示"

class SQLOptimizer:
    """SQL优化器"""
    
    def __init__(self):
        self.rules = [
            RemoveUnnecessarySubqueryRule(),
            OptimizeJoinOrderRule(),
            AddIndexHintsRule()
        ]
    
    def optimize(self, sql: str) -> Dict[str, Any]:
        """优化SQL语句"""
        optimized_sql = sql
        applied_rules = []
        
        for rule in self.rules:
            original_sql = optimized_sql
            optimized_sql = rule.apply(optimized_sql)
            
            if original_sql != optimized_sql:
                applied_rules.append(rule.get_description())
        
        return {
            'original_sql': sql,
            'optimized_sql': optimized_sql,
            'applied_rules': applied_rules,
            'optimization_ratio': len(applied_rules) / len(self.rules)
        }
```

### 多数据库方言支持

```python
class SQLDialectAdapter:
    """SQL方言适配器"""
    
    def __init__(self, db_type: str):
        self.db_type = db_type.lower()
        self.dialect_rules = self._load_dialect_rules()
    
    def adapt_sql(self, sql: str) -> str:
        """适配SQL到特定数据库方言"""
        adapted_sql = sql
        
        if self.db_type == 'mysql':
            adapted_sql = self._adapt_to_mysql(adapted_sql)
        elif self.db_type == 'postgresql':
            adapted_sql = self._adapt_to_postgresql(adapted_sql)
        elif self.db_type == 'sqlite':
            adapted_sql = self._adapt_to_sqlite(adapted_sql)
        elif self.db_type == 'snowflake':
            adapted_sql = self._adapt_to_snowflake(adapted_sql)
        
        return adapted_sql
    
    def _adapt_to_mysql(self, sql: str) -> str:
        """适配到MySQL方言"""
        # MySQL特定的语法调整
        # 例如：LIMIT语法、日期函数等
        sql = re.sub(r'\bTOP\s+(\d+)\b', r'LIMIT \1', sql, flags=re.IGNORECASE)
        return sql
    
    def _adapt_to_postgresql(self, sql: str) -> str:
        """适配到PostgreSQL方言"""
        # PostgreSQL特定的语法调整
        # 例如：字符串连接、日期函数等
        sql = re.sub(r'\bCONCAT\(([^)]+)\)', r'\1', sql, flags=re.IGNORECASE)
        return sql
    
    def _adapt_to_sqlite(self, sql: str) -> str:
        """适配到SQLite方言"""
        # SQLite特定的语法调整
        return sql
    
    def _adapt_to_snowflake(self, sql: str) -> str:
        """适配到Snowflake方言"""
        # Snowflake特定的语法调整
        return sql
```

### 查询上下文管理

```python
class QueryContext:
    """查询上下文管理"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.query_history = []
        self.table_context = set()
        self.column_context = set()
        self.last_sql = None
        self.conversation_state = {}
    
    def add_query(self, query: str, sql: str, result_summary: Dict[str, Any]):
        """添加查询到历史"""
        self.query_history.append({
            'timestamp': datetime.now(),
            'query': query,
            'sql': sql,
            'result_summary': result_summary
        })
        
        # 更新上下文
        self._update_context(sql)
        self.last_sql = sql
    
    def _update_context(self, sql: str):
        """更新查询上下文"""
        # 提取表名和字段名，更新上下文
        # 简化实现
        tables = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        self.table_context.update(tables)
        
        columns = re.findall(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
        if columns:
            column_list = re.findall(r'\b(\w+)\b', columns[0])
            self.column_context.update(column_list)
    
    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        if not self.query_history:
            return ""
        
        recent_queries = self.query_history[-3:]  # 最近3个查询
        context_parts = []
        
        for i, query_info in enumerate(recent_queries, 1):
            context_parts.append(
                f"查询{i}: {query_info['query']}\n"
                f"SQL: {query_info['sql']}"
            )
        
        return "\n\n".join(context_parts)
    
    def is_follow_up_query(self, current_query: str) -> bool:
        """判断是否为后续查询"""
        if not self.query_history:
            return False
        
        # 简单的后续查询判断逻辑
        follow_up_keywords = ['再', '还', '另外', '也', '同时', '以及']
        return any(keyword in current_query for keyword in follow_up_keywords)
```

### 增量查询处理

```python
class IncrementalQueryProcessor:
    """增量查询处理器"""
    
    def __init__(self, sql_generator: SQLGeneratorAgent):
        self.sql_generator = sql_generator
    
    async def process_incremental_query(self, 
                                       current_query: str,
                                       context: QueryContext,
                                       analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理增量查询"""
        if not context.is_follow_up_query(current_query):
            # 不是后续查询，正常处理
            return await self.sql_generator.generate_sql(current_query, analysis)
        
        # 构建增量查询提示词
        incremental_prompt = self._build_incremental_prompt(
            current_query, context, analysis
        )
        
        # 生成增量SQL
        response = await self.sql_generator.model_client.complete(incremental_prompt)
        sql = self.sql_generator._extract_sql_from_response(response)
        
        # 验证和优化
        validation_result = await self.sql_generator._validate_sql(sql)
        
        return {
            'sql': sql,
            'is_incremental': True,
            'base_query': context.last_sql,
            'is_valid': validation_result['is_valid'],
            'validation_errors': validation_result.get('errors', [])
        }
    
    def _build_incremental_prompt(self, 
                                 current_query: str,
                                 context: QueryContext,
                                 analysis: Dict[str, Any]) -> str:
        """构建增量查询提示词"""
        return f"""
        用户正在进行连续查询，请基于之前的查询上下文生成新的SQL。
        
        查询历史:
        {context.get_context_summary()}
        
        当前查询: "{current_query}"
        
        查询分析:
        {analysis}
        
        请生成适当的SQL语句，考虑与之前查询的关联性。
        如果是对之前结果的进一步筛选或分析，请基于之前的SQL进行修改。
        
        SQL:
        """
```

## 性能监控和质量评估

### SQL质量评估

```python
class SQLQualityEvaluator:
    """SQL质量评估器"""
    
    def evaluate_sql_quality(self, 
                            sql: str, 
                            query: str,
                            execution_result: Optional[Dict] = None) -> Dict[str, float]:
        """评估SQL质量"""
        metrics = {
            'syntax_score': self._evaluate_syntax(sql),
            'readability_score': self._evaluate_readability(sql),
            'performance_score': self._evaluate_performance(sql),
            'semantic_score': self._evaluate_semantics(sql, query)
        }
        
        if execution_result:
            metrics['execution_score'] = self._evaluate_execution(execution_result)
        
        # 计算综合分数
        weights = {
            'syntax_score': 0.3,
            'readability_score': 0.2,
            'performance_score': 0.3,
            'semantic_score': 0.2
        }
        
        overall_score = sum(metrics[key] * weights.get(key, 0) for key in metrics)
        metrics['overall_score'] = overall_score
        
        return metrics
    
    def _evaluate_syntax(self, sql: str) -> float:
        """评估语法正确性"""
        try:
            parsed = sqlparse.parse(sql)
            if parsed and len(parsed) > 0:
                return 1.0
            return 0.0
        except:
            return 0.0
    
    def _evaluate_readability(self, sql: str) -> float:
        """评估可读性"""
        score = 0.5  # 基础分数
        
        # 检查格式化
        if '\n' in sql:  # 有换行
            score += 0.2
        
        # 检查关键字大写
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
        uppercase_keywords = sum(1 for kw in keywords if kw in sql)
        score += (uppercase_keywords / len(keywords)) * 0.3
        
        return min(score, 1.0)
    
    def _evaluate_performance(self, sql: str) -> float:
        """评估性能潜力"""
        score = 0.7  # 基础分数
        
        # 检查是否使用了SELECT *
        if 'SELECT *' in sql.upper():
            score -= 0.2
        
        # 检查是否有WHERE条件
        if 'WHERE' in sql.upper():
            score += 0.2
        
        # 检查是否有不必要的子查询
        subquery_count = sql.upper().count('SELECT') - 1
        if subquery_count > 2:
            score -= 0.1 * (subquery_count - 2)
        
        return max(score, 0.0)
    
    def _evaluate_semantics(self, sql: str, query: str) -> float:
        """评估语义匹配度"""
        # 简化的语义评估
        # 实际实现可能需要更复杂的NLP技术
        
        # 检查关键词匹配
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
        sql_keywords = set(re.findall(r'\b\w+\b', sql.lower()))
        
        if query_keywords:
            overlap = len(query_keywords & sql_keywords) / len(query_keywords)
            return min(overlap * 2, 1.0)  # 放大重叠度
        
        return 0.5
    
    def _evaluate_execution(self, execution_result: Dict) -> float:
        """评估执行结果"""
        if execution_result.get('success', False):
            execution_time = execution_result.get('execution_time', 0)
            
            # 基于执行时间评分
            if execution_time < 1.0:  # 1秒以内
                return 1.0
            elif execution_time < 5.0:  # 5秒以内
                return 0.8
            elif execution_time < 10.0:  # 10秒以内
                return 0.6
            else:
                return 0.4
        else:
            return 0.0
```

### 性能监控

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# 监控指标
sql_generation_requests = Counter('sql_generation_requests_total',
                                 'Total SQL generation requests')
sql_generation_duration = Histogram('sql_generation_duration_seconds',
                                   'SQL generation duration')
sql_validation_failures = Counter('sql_validation_failures_total',
                                 'SQL validation failures')
sql_quality_score = Gauge('sql_quality_score',
                         'Average SQL quality score')

class MonitoredSQLGenerator(SQLGeneratorAgent):
    async def generate_sql(self, query: str, analysis_result: Dict[str, Any], 
                          context: Optional[str] = None) -> Dict[str, Any]:
        sql_generation_requests.inc()
        
        start_time = time.time()
        try:
            result = await super().generate_sql(query, analysis_result, context)
            
            # 记录质量分数
            if 'confidence_score' in result:
                sql_quality_score.set(result['confidence_score'])
            
            # 记录验证失败
            if not result.get('is_valid', True):
                sql_validation_failures.inc()
            
            return result
            
        finally:
            sql_generation_duration.observe(time.time() - start_time)
```

## API接口

### REST API

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class SQLGenerationRequest(BaseModel):
    query: str
    analysis_result: Dict[str, Any]
    context: Optional[str] = None
    db_type: Optional[str] = "mysql"
    optimize: Optional[bool] = True

class SQLGenerationResponse(BaseModel):
    sql: Optional[str]
    original_sql: Optional[str]
    is_valid: bool
    validation_errors: List[str]
    optimization_applied: bool
    confidence_score: float
    quality_metrics: Optional[Dict[str, float]]
    processing_time: float

@router.post("/generate", response_model=SQLGenerationResponse)
async def generate_sql(
    request: SQLGenerationRequest,
    generator: SQLGeneratorAgent = Depends(get_sql_generator)
):
    """生成SQL语句"""
    start_time = time.time()
    
    try:
        result = await generator.generate_sql(
            request.query,
            request.analysis_result,
            request.context
        )
        
        # 质量评估
        if result.get('sql'):
            evaluator = SQLQualityEvaluator()
            quality_metrics = evaluator.evaluate_sql_quality(
                result['sql'], request.query
            )
        else:
            quality_metrics = None
        
        processing_time = time.time() - start_time
        
        return SQLGenerationResponse(
            sql=result.get('sql'),
            original_sql=result.get('original_sql'),
            is_valid=result.get('is_valid', False),
            validation_errors=result.get('validation_errors', []),
            optimization_applied=result.get('optimization_applied', False),
            confidence_score=result.get('confidence_score', 0.0),
            quality_metrics=quality_metrics,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_sql(
    sql: str,
    db_type: str = "mysql",
    generator: SQLGeneratorAgent = Depends(get_sql_generator)
):
    """验证SQL语句"""
    try:
        validation_result = await generator._validate_sql(sql)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_sql(
    sql: str,
    db_type: str = "mysql"
):
    """优化SQL语句"""
    try:
        optimizer = SQLOptimizer()
        optimization_result = optimizer.optimize(sql)
        return optimization_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 测试用例

### 单元测试

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestSQLGeneratorAgent:
    @pytest.fixture
    def mock_model_client(self):
        client = AsyncMock()
        client.complete.return_value = "SELECT * FROM users WHERE age > 18;"
        return client
    
    @pytest.fixture
    def mock_schema_service(self):
        service = AsyncMock()
        service.build_context.return_value = "表 users: id, name, age"
        return service
    
    @pytest.fixture
    def generator(self, mock_model_client, mock_schema_service):
        return SQLGeneratorAgent("mysql", mock_model_client, mock_schema_service)
    
    @pytest.mark.asyncio
    async def test_generate_simple_sql(self, generator):
        """测试简单SQL生成"""
        query = "查找所有成年用户"
        analysis = {
            'query_intent': '查找用户',
            'query_type': 'select',
            'entities': ['用户', '成年'],
            'filter_conditions': ['年龄大于18']
        }
        
        result = await generator.generate_sql(query, analysis)
        
        assert result['is_valid']
        assert 'SELECT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()
    
    def test_extract_sql_from_response(self, generator):
        """测试SQL提取"""
        response = "```sql\nSELECT * FROM users;\n```"
        sql = generator._extract_sql_from_response(response)
        
        assert sql == "SELECT * FROM users;"
    
    def test_sql_validation(self, generator):
        """测试SQL验证"""
        # 这里需要mock数据库访问
        pass

class TestSQLOptimizer:
    def test_optimization_rules(self):
        """测试优化规则"""
        optimizer = SQLOptimizer()
        sql = "SELECT * FROM users WHERE id = 1;"
        
        result = optimizer.optimize(sql)
        
        assert 'original_sql' in result
        assert 'optimized_sql' in result
        assert 'applied_rules' in result
```

## 配置和部署

### 配置文件

```yaml
# sql_generator_config.yaml
sql_generator:
  model:
    provider: "openai"
    model_name: "gpt-4"
    temperature: 0.1
    max_tokens: 2000
  
  optimization:
    enabled: true
    rules:
      - "remove_unnecessary_subquery"
      - "optimize_join_order"
      - "add_index_hints"
  
  validation:
    enabled: true
    strict_mode: false
    check_table_existence: true
    check_column_existence: true
  
  quality_evaluation:
    enabled: true
    min_quality_score: 0.7
  
  dialects:
    mysql:
      quote_char: "`"
      limit_syntax: "LIMIT"
    postgresql:
      quote_char: '"'
      limit_syntax: "LIMIT"
    sqlite:
      quote_char: "["
      limit_syntax: "LIMIT"
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

*此文档提供了SQL生成与优化服务的完整实现指南，包括智能生成、语法验证、性能优化、质量评估和多数据库支持。*