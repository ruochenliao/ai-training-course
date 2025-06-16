# SQL解释与文档生成服务功能还原提示词

## 服务概述

SQL解释与文档生成服务负责将生成的SQL语句转换为易于理解的自然语言解释，生成详细的查询文档，并提供SQL优化建议。该服务帮助用户理解查询逻辑，学习SQL知识，并改进查询性能。

## 核心功能

### 1. SQL语句解释
- 自然语言描述SQL查询逻辑
- 分析查询的业务含义和目的
- 解释复杂的JOIN关系和子查询
- 说明WHERE条件和过滤逻辑

### 2. 查询文档生成
- 生成结构化的查询文档
- 包含查询目的、涉及表、字段说明
- 提供查询示例和使用场景
- 生成技术文档和业务文档

### 3. SQL优化建议
- 分析查询性能瓶颈
- 提供索引优化建议
- 建议查询重写方案
- 识别潜在的性能问题

### 4. 学习辅助功能
- 提供SQL语法教学解释
- 生成相关的学习资源链接
- 推荐类似查询的最佳实践
- 提供交互式学习建议

## 技术实现

### SQL解释器核心类

```python
from typing import Dict, List, Optional, Any
import re
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"

class JoinType(Enum):
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"
    CROSS = "CROSS JOIN"

@dataclass
class SQLComponent:
    """SQL组件"""
    type: str
    content: str
    explanation: str
    business_meaning: str = ""

@dataclass
class QueryAnalysis:
    """查询分析结果"""
    query_type: QueryType
    tables: List[str]
    columns: List[str]
    joins: List[Dict[str, Any]]
    conditions: List[str]
    aggregations: List[str]
    ordering: List[str]
    grouping: List[str]
    complexity_score: float
    estimated_performance: str

class SQLExplainerAgent:
    """SQL解释智能体"""
    
    def __init__(self, llm_client, schema_info: Dict[str, Any] = None):
        self.llm_client = llm_client
        self.schema_info = schema_info or {}
        self.explanation_templates = self._load_explanation_templates()
        self.optimization_rules = self._load_optimization_rules()
    
    async def explain_sql(self, 
                         sql: str, 
                         context: Dict[str, Any] = None,
                         detail_level: str = "medium") -> Dict[str, Any]:
        """解释SQL查询"""
        try:
            # 分析SQL结构
            analysis = self._analyze_sql_structure(sql)
            
            # 生成基础解释
            basic_explanation = await self._generate_basic_explanation(sql, analysis)
            
            # 生成详细解释
            detailed_explanation = await self._generate_detailed_explanation(
                sql, analysis, detail_level
            )
            
            # 生成业务含义解释
            business_explanation = await self._generate_business_explanation(
                sql, analysis, context
            )
            
            # 生成优化建议
            optimization_suggestions = await self._generate_optimization_suggestions(
                sql, analysis
            )
            
            # 生成学习要点
            learning_points = self._generate_learning_points(sql, analysis)
            
            return {
                'success': True,
                'sql': sql,
                'analysis': analysis.__dict__,
                'explanations': {
                    'basic': basic_explanation,
                    'detailed': detailed_explanation,
                    'business': business_explanation
                },
                'optimization_suggestions': optimization_suggestions,
                'learning_points': learning_points,
                'complexity_assessment': self._assess_complexity(analysis),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SQL解释失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'sql': sql
            }
    
    def _analyze_sql_structure(self, sql: str) -> QueryAnalysis:
        """分析SQL结构"""
        sql_upper = sql.upper()
        
        # 确定查询类型
        query_type = self._determine_query_type(sql_upper)
        
        # 提取表名
        tables = self._extract_tables(sql)
        
        # 提取列名
        columns = self._extract_columns(sql)
        
        # 分析JOIN
        joins = self._analyze_joins(sql)
        
        # 提取WHERE条件
        conditions = self._extract_conditions(sql)
        
        # 提取聚合函数
        aggregations = self._extract_aggregations(sql)
        
        # 提取ORDER BY
        ordering = self._extract_ordering(sql)
        
        # 提取GROUP BY
        grouping = self._extract_grouping(sql)
        
        # 计算复杂度分数
        complexity_score = self._calculate_complexity_score(
            tables, joins, conditions, aggregations
        )
        
        # 估算性能
        estimated_performance = self._estimate_performance(complexity_score, tables, joins)
        
        return QueryAnalysis(
            query_type=query_type,
            tables=tables,
            columns=columns,
            joins=joins,
            conditions=conditions,
            aggregations=aggregations,
            ordering=ordering,
            grouping=grouping,
            complexity_score=complexity_score,
            estimated_performance=estimated_performance
        )
    
    def _determine_query_type(self, sql_upper: str) -> QueryType:
        """确定查询类型"""
        if sql_upper.strip().startswith('SELECT'):
            return QueryType.SELECT
        elif sql_upper.strip().startswith('INSERT'):
            return QueryType.INSERT
        elif sql_upper.strip().startswith('UPDATE'):
            return QueryType.UPDATE
        elif sql_upper.strip().startswith('DELETE'):
            return QueryType.DELETE
        elif sql_upper.strip().startswith('CREATE'):
            return QueryType.CREATE
        elif sql_upper.strip().startswith('ALTER'):
            return QueryType.ALTER
        elif sql_upper.strip().startswith('DROP'):
            return QueryType.DROP
        else:
            return QueryType.SELECT  # 默认
    
    def _extract_tables(self, sql: str) -> List[str]:
        """提取表名"""
        tables = []
        
        # FROM子句中的表
        from_pattern = r'FROM\s+([\w\.]+)(?:\s+(?:AS\s+)?([\w]+))?'
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        for match in from_matches:
            table_name = match[0]
            alias = match[1] if match[1] else None
            tables.append({
                'name': table_name,
                'alias': alias,
                'type': 'main'
            })
        
        # JOIN子句中的表
        join_pattern = r'(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+([\w\.]+)(?:\s+(?:AS\s+)?([\w]+))?'
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        for match in join_matches:
            table_name = match[0]
            alias = match[1] if match[1] else None
            tables.append({
                'name': table_name,
                'alias': alias,
                'type': 'joined'
            })
        
        return [t['name'] for t in tables]
    
    def _extract_columns(self, sql: str) -> List[str]:
        """提取列名"""
        columns = []
        
        # 简化的列提取（实际需要更复杂的SQL解析）
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            select_clause = select_match.group(1)
            
            # 处理SELECT *
            if '*' in select_clause:
                columns.append('*')
            else:
                # 分割列名（简化处理）
                column_parts = select_clause.split(',')
                for part in column_parts:
                    part = part.strip()
                    # 提取列名（去除函数和别名）
                    column_match = re.search(r'([\w\.]+)', part)
                    if column_match:
                        columns.append(column_match.group(1))
        
        return columns
    
    def _analyze_joins(self, sql: str) -> List[Dict[str, Any]]:
        """分析JOIN关系"""
        joins = []
        
        join_pattern = r'((?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN)\s+([\w\.]+)(?:\s+(?:AS\s+)?([\w]+))?\s+ON\s+([^\n]+?)(?=\s+(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN|\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|$)'
        
        matches = re.findall(join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            join_type = match[0].strip().upper()
            table = match[1]
            alias = match[2] if match[2] else None
            condition = match[3].strip()
            
            joins.append({
                'type': join_type,
                'table': table,
                'alias': alias,
                'condition': condition,
                'explanation': self._explain_join_condition(condition)
            })
        
        return joins
    
    def _explain_join_condition(self, condition: str) -> str:
        """解释JOIN条件"""
        # 简化的JOIN条件解释
        if '=' in condition:
            parts = condition.split('=')
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                return f"将{left}与{right}进行匹配连接"
        
        return f"根据条件 '{condition}' 进行连接"
    
    def _extract_conditions(self, sql: str) -> List[str]:
        """提取WHERE条件"""
        conditions = []
        
        where_pattern = r'WHERE\s+(.*?)(?=\s+GROUP|\s+ORDER|\s+LIMIT|$)'
        where_match = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1).strip()
            
            # 分割AND/OR条件
            condition_parts = re.split(r'\s+(?:AND|OR)\s+', where_clause, flags=re.IGNORECASE)
            
            for condition in condition_parts:
                condition = condition.strip()
                if condition:
                    conditions.append({
                        'condition': condition,
                        'explanation': self._explain_condition(condition)
                    })
        
        return conditions
    
    def _explain_condition(self, condition: str) -> str:
        """解释WHERE条件"""
        condition = condition.strip()
        
        # 等值条件
        if '=' in condition and 'LIKE' not in condition.upper():
            parts = condition.split('=')
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip()
                return f"{field} 等于 {value}"
        
        # LIKE条件
        elif 'LIKE' in condition.upper():
            return f"模糊匹配条件: {condition}"
        
        # 范围条件
        elif 'BETWEEN' in condition.upper():
            return f"范围条件: {condition}"
        
        # IN条件
        elif 'IN' in condition.upper():
            return f"包含条件: {condition}"
        
        # 比较条件
        elif any(op in condition for op in ['>', '<', '>=', '<=', '!=', '<>']):
            return f"比较条件: {condition}"
        
        return f"条件: {condition}"
    
    def _extract_aggregations(self, sql: str) -> List[str]:
        """提取聚合函数"""
        aggregations = []
        
        agg_pattern = r'(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\s*\([^)]+\)'
        matches = re.findall(agg_pattern, sql, re.IGNORECASE)
        
        for match in matches:
            aggregations.append(match.upper())
        
        return aggregations
    
    def _extract_ordering(self, sql: str) -> List[str]:
        """提取ORDER BY"""
        ordering = []
        
        order_pattern = r'ORDER\s+BY\s+(.*?)(?=\s+LIMIT|$)'
        order_match = re.search(order_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if order_match:
            order_clause = order_match.group(1).strip()
            order_parts = order_clause.split(',')
            
            for part in order_parts:
                part = part.strip()
                if part:
                    ordering.append(part)
        
        return ordering
    
    def _extract_grouping(self, sql: str) -> List[str]:
        """提取GROUP BY"""
        grouping = []
        
        group_pattern = r'GROUP\s+BY\s+(.*?)(?=\s+HAVING|\s+ORDER|\s+LIMIT|$)'
        group_match = re.search(group_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if group_match:
            group_clause = group_match.group(1).strip()
            group_parts = group_clause.split(',')
            
            for part in group_parts:
                part = part.strip()
                if part:
                    grouping.append(part)
        
        return grouping
    
    def _calculate_complexity_score(self, 
                                   tables: List[str], 
                                   joins: List[Dict], 
                                   conditions: List[str], 
                                   aggregations: List[str]) -> float:
        """计算复杂度分数"""
        score = 0.0
        
        # 表数量影响
        score += len(tables) * 0.5
        
        # JOIN数量影响
        score += len(joins) * 1.0
        
        # 条件数量影响
        score += len(conditions) * 0.3
        
        # 聚合函数影响
        score += len(aggregations) * 0.8
        
        # 子查询影响（简化检测）
        # 实际实现需要更复杂的子查询检测
        
        return min(score, 10.0)  # 限制在0-10范围内
    
    def _estimate_performance(self, complexity_score: float, tables: List[str], joins: List[Dict]) -> str:
        """估算性能"""
        if complexity_score <= 2.0:
            return "优秀"
        elif complexity_score <= 4.0:
            return "良好"
        elif complexity_score <= 6.0:
            return "一般"
        elif complexity_score <= 8.0:
            return "较差"
        else:
            return "很差"
    
    async def _generate_basic_explanation(self, sql: str, analysis: QueryAnalysis) -> str:
        """生成基础解释"""
        prompt = f"""
请用简洁的中文解释以下SQL查询的作用：

SQL查询：
{sql}

查询分析：
- 查询类型：{analysis.query_type.value}
- 涉及表：{', '.join(analysis.tables)}
- 查询列：{', '.join(analysis.columns)}
- JOIN数量：{len(analysis.joins)}
- 条件数量：{len(analysis.conditions)}

请用1-2句话简洁地说明这个查询的主要目的。
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"生成基础解释失败: {e}")
            return self._generate_fallback_explanation(analysis)
    
    async def _generate_detailed_explanation(self, 
                                           sql: str, 
                                           analysis: QueryAnalysis, 
                                           detail_level: str) -> Dict[str, Any]:
        """生成详细解释"""
        explanation = {
            'query_overview': '',
            'table_analysis': [],
            'join_analysis': [],
            'condition_analysis': [],
            'result_description': '',
            'execution_flow': []
        }
        
        # 查询概述
        explanation['query_overview'] = await self._generate_query_overview(sql, analysis)
        
        # 表分析
        explanation['table_analysis'] = self._analyze_table_usage(analysis)
        
        # JOIN分析
        if analysis.joins:
            explanation['join_analysis'] = self._analyze_join_logic(analysis.joins)
        
        # 条件分析
        if analysis.conditions:
            explanation['condition_analysis'] = self._analyze_condition_logic(analysis.conditions)
        
        # 结果描述
        explanation['result_description'] = self._describe_expected_results(analysis)
        
        # 执行流程
        explanation['execution_flow'] = self._describe_execution_flow(analysis)
        
        return explanation
    
    async def _generate_business_explanation(self, 
                                           sql: str, 
                                           analysis: QueryAnalysis, 
                                           context: Dict[str, Any] = None) -> str:
        """生成业务含义解释"""
        if not context:
            context = {}
        
        prompt = f"""
请从业务角度解释以下SQL查询的含义和用途：

SQL查询：
{sql}

业务上下文：
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无特定业务上下文'}

请说明：
1. 这个查询解决什么业务问题
2. 查询结果对业务决策有什么帮助
3. 可能的使用场景

请用通俗易懂的语言解释，避免技术术语。
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"生成业务解释失败: {e}")
            return "无法生成业务解释，请联系技术支持。"
    
    async def _generate_optimization_suggestions(self, 
                                               sql: str, 
                                               analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        # 基于规则的优化建议
        rule_suggestions = self._apply_optimization_rules(sql, analysis)
        suggestions.extend(rule_suggestions)
        
        # 基于LLM的优化建议
        llm_suggestions = await self._generate_llm_optimization_suggestions(sql, analysis)
        suggestions.extend(llm_suggestions)
        
        # 去重和排序
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        
        return sorted(unique_suggestions, key=lambda x: x.get('priority', 5))
    
    def _apply_optimization_rules(self, sql: str, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """应用优化规则"""
        suggestions = []
        
        # 规则1：检查是否使用SELECT *
        if '*' in analysis.columns:
            suggestions.append({
                'type': 'column_selection',
                'title': '避免使用SELECT *',
                'description': '明确指定需要的列名，可以减少数据传输量和提高查询性能',
                'priority': 2,
                'impact': 'medium',
                'example': '将 SELECT * 改为 SELECT column1, column2, column3'
            })
        
        # 规则2：检查JOIN数量
        if len(analysis.joins) > 3:
            suggestions.append({
                'type': 'join_optimization',
                'title': '考虑减少JOIN数量',
                'description': f'当前查询包含{len(analysis.joins)}个JOIN，可能影响性能',
                'priority': 3,
                'impact': 'high',
                'example': '考虑使用子查询或临时表来减少JOIN复杂度'
            })
        
        # 规则3：检查WHERE条件
        if len(analysis.conditions) == 0 and len(analysis.tables) > 1:
            suggestions.append({
                'type': 'filtering',
                'title': '添加WHERE条件',
                'description': '多表查询建议添加适当的WHERE条件来限制结果集',
                'priority': 1,
                'impact': 'high',
                'example': '添加WHERE子句来过滤不需要的数据'
            })
        
        # 规则4：检查ORDER BY
        if analysis.ordering and not analysis.grouping:
            suggestions.append({
                'type': 'indexing',
                'title': '考虑为ORDER BY字段添加索引',
                'description': f'为排序字段 {analysis.ordering} 添加索引可以提高排序性能',
                'priority': 4,
                'impact': 'medium',
                'example': f'CREATE INDEX idx_sort ON table_name ({analysis.ordering[0]})'
            })
        
        # 规则5：检查聚合查询
        if analysis.aggregations and not analysis.grouping:
            suggestions.append({
                'type': 'aggregation',
                'title': '检查聚合查询逻辑',
                'description': '使用聚合函数时考虑是否需要GROUP BY子句',
                'priority': 2,
                'impact': 'medium',
                'example': '确认聚合函数的使用是否符合预期'
            })
        
        return suggestions
    
    async def _generate_llm_optimization_suggestions(self, 
                                                   sql: str, 
                                                   analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """使用LLM生成优化建议"""
        prompt = f"""
请分析以下SQL查询并提供性能优化建议：

SQL查询：
{sql}

查询特征：
- 复杂度分数：{analysis.complexity_score}
- 表数量：{len(analysis.tables)}
- JOIN数量：{len(analysis.joins)}
- 条件数量：{len(analysis.conditions)}
- 聚合函数：{len(analysis.aggregations)}

请提供具体的优化建议，包括：
1. 索引优化建议
2. 查询重写建议
3. 性能改进方案

请以JSON格式返回建议，每个建议包含type、title、description、priority、impact、example字段。
"""
        
        try:
            response = await self.llm_client.generate_response(prompt)
            # 解析LLM返回的JSON格式建议
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else []
        except Exception as e:
            logger.error(f"LLM优化建议生成失败: {e}")
            return []
    
    def _generate_learning_points(self, sql: str, analysis: QueryAnalysis) -> List[Dict[str, Any]]:
        """生成学习要点"""
        learning_points = []
        
        # 基于查询特征生成学习要点
        if analysis.joins:
            learning_points.append({
                'topic': 'SQL JOIN',
                'title': '表连接操作',
                'description': '学习不同类型的JOIN操作及其使用场景',
                'difficulty': 'intermediate',
                'resources': [
                    'https://www.w3schools.com/sql/sql_join.asp',
                    'SQL JOIN详解教程'
                ]
            })
        
        if analysis.aggregations:
            learning_points.append({
                'topic': 'SQL Aggregation',
                'title': '聚合函数',
                'description': '掌握COUNT、SUM、AVG等聚合函数的使用',
                'difficulty': 'beginner',
                'resources': [
                    'https://www.w3schools.com/sql/sql_count_avg_sum.asp',
                    'SQL聚合函数教程'
                ]
            })
        
        if analysis.grouping:
            learning_points.append({
                'topic': 'SQL GROUP BY',
                'title': '分组查询',
                'description': '理解GROUP BY子句和HAVING条件的使用',
                'difficulty': 'intermediate',
                'resources': [
                    'https://www.w3schools.com/sql/sql_groupby.asp',
                    'SQL分组查询详解'
                ]
            })
        
        if analysis.complexity_score > 5.0:
            learning_points.append({
                'topic': 'Query Optimization',
                'title': '查询优化',
                'description': '学习复杂查询的优化技巧和最佳实践',
                'difficulty': 'advanced',
                'resources': [
                    'SQL查询优化指南',
                    '数据库性能调优'
                ]
            })
        
        return learning_points
    
    def _assess_complexity(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """评估查询复杂度"""
        score = analysis.complexity_score
        
        if score <= 2.0:
            level = "简单"
            description = "这是一个简单的查询，易于理解和执行"
        elif score <= 4.0:
            level = "中等"
            description = "这是一个中等复杂度的查询，包含一些高级特性"
        elif score <= 6.0:
            level = "复杂"
            description = "这是一个复杂的查询，需要仔细优化以确保性能"
        else:
            level = "非常复杂"
            description = "这是一个非常复杂的查询，建议分解为多个简单查询"
        
        return {
            'score': score,
            'level': level,
            'description': description,
            'factors': {
                'table_count': len(analysis.tables),
                'join_count': len(analysis.joins),
                'condition_count': len(analysis.conditions),
                'aggregation_count': len(analysis.aggregations)
            }
        }
    
    def _generate_fallback_explanation(self, analysis: QueryAnalysis) -> str:
        """生成备用解释"""
        if analysis.query_type == QueryType.SELECT:
            return f"这是一个查询语句，从 {', '.join(analysis.tables)} 表中检索数据。"
        else:
            return f"这是一个 {analysis.query_type.value} 操作。"
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """加载解释模板"""
        return {
            'select': "从{tables}中查询{columns}数据",
            'join': "将{table1}和{table2}通过{condition}连接",
            'where': "筛选满足{condition}的记录",
            'group': "按{columns}分组统计",
            'order': "按{columns}排序"
        }
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """加载优化规则"""
        return [
            {
                'name': 'avoid_select_star',
                'pattern': r'SELECT\s+\*',
                'suggestion': '明确指定需要的列名'
            },
            {
                'name': 'add_where_clause',
                'pattern': r'FROM\s+\w+\s+JOIN',
                'suggestion': '添加WHERE条件限制结果集'
            }
        ]
```

### 文档生成器

```python
class DocumentationGenerator:
    """文档生成器"""
    
    def __init__(self, sql_explainer: SQLExplainerAgent):
        self.sql_explainer = sql_explainer
        self.templates = self._load_document_templates()
    
    async def generate_query_documentation(self, 
                                         sql: str, 
                                         context: Dict[str, Any] = None,
                                         doc_type: str = "technical") -> Dict[str, Any]:
        """生成查询文档"""
        try:
            # 获取SQL解释
            explanation_result = await self.sql_explainer.explain_sql(sql, context)
            
            if not explanation_result['success']:
                return explanation_result
            
            # 根据文档类型生成不同格式的文档
            if doc_type == "technical":
                document = await self._generate_technical_documentation(sql, explanation_result)
            elif doc_type == "business":
                document = await self._generate_business_documentation(sql, explanation_result)
            elif doc_type == "tutorial":
                document = await self._generate_tutorial_documentation(sql, explanation_result)
            else:
                document = await self._generate_general_documentation(sql, explanation_result)
            
            return {
                'success': True,
                'document': document,
                'doc_type': doc_type,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"文档生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_technical_documentation(self, 
                                              sql: str, 
                                              explanation: Dict[str, Any]) -> str:
        """生成技术文档"""
        analysis = explanation['analysis']
        explanations = explanation['explanations']
        optimization = explanation['optimization_suggestions']
        
        doc = f"""
# SQL查询技术文档

## 查询概述
{explanations['basic']}

## SQL语句
```sql
{sql}
```

## 查询分析

### 基本信息
- **查询类型**: {analysis['query_type']}
- **涉及表**: {', '.join(analysis['tables'])}
- **查询列**: {', '.join(analysis['columns'])}
- **复杂度评分**: {analysis['complexity_score']:.1f}/10
- **预估性能**: {analysis['estimated_performance']}

### 表连接分析
"""
        
        if analysis['joins']:
            doc += "\n"
            for i, join in enumerate(analysis['joins'], 1):
                doc += f"""
#### JOIN {i}
- **类型**: {join['type']}
- **表**: {join['table']}
- **条件**: {join['condition']}
- **说明**: {join['explanation']}

"""
        else:
            doc += "无表连接操作\n\n"
        
        doc += "### 筛选条件\n"
        if analysis['conditions']:
            for i, condition in enumerate(analysis['conditions'], 1):
                doc += f"- **条件 {i}**: {condition['condition']} - {condition['explanation']}\n"
        else:
            doc += "无筛选条件\n"
        
        doc += "\n### 聚合和分组\n"
        if analysis['aggregations']:
            doc += f"- **聚合函数**: {', '.join(analysis['aggregations'])}\n"
        if analysis['grouping']:
            doc += f"- **分组字段**: {', '.join(analysis['grouping'])}\n"
        if not analysis['aggregations'] and not analysis['grouping']:
            doc += "无聚合和分组操作\n"
        
        doc += "\n### 排序\n"
        if analysis['ordering']:
            doc += f"- **排序字段**: {', '.join(analysis['ordering'])}\n"
        else:
            doc += "无排序操作\n"
        
        doc += "\n## 优化建议\n"
        if optimization:
            for i, suggestion in enumerate(optimization, 1):
                doc += f"""
### {i}. {suggestion['title']}
- **类型**: {suggestion['type']}
- **优先级**: {suggestion['priority']}
- **影响**: {suggestion['impact']}
- **描述**: {suggestion['description']}
- **示例**: {suggestion.get('example', '无')}

"""
        else:
            doc += "暂无优化建议\n"
        
        doc += "\n## 学习要点\n"
        learning_points = explanation.get('learning_points', [])
        if learning_points:
            for point in learning_points:
                doc += f"""
### {point['title']}
- **主题**: {point['topic']}
- **难度**: {point['difficulty']}
- **描述**: {point['description']}
- **资源**: {', '.join(point['resources'])}

"""
        else:
            doc += "无特殊学习要点\n"
        
        return doc
    
    async def _generate_business_documentation(self, 
                                             sql: str, 
                                             explanation: Dict[str, Any]) -> str:
        """生成业务文档"""
        explanations = explanation['explanations']
        analysis = explanation['analysis']
        
        doc = f"""
# 查询业务文档

## 业务目的
{explanations['business']}

## 查询说明
{explanations['basic']}

## 数据来源
本查询从以下数据表获取信息：
"""
        
        for table in analysis['tables']:
            # 这里可以添加表的业务含义说明
            doc += f"- **{table}**: {self._get_table_business_description(table)}\n"
        
        doc += "\n## 查询结果\n"
        doc += self._describe_business_results(analysis)
        
        doc += "\n## 使用场景\n"
        doc += self._generate_use_cases(analysis)
        
        return doc
    
    async def _generate_tutorial_documentation(self, 
                                             sql: str, 
                                             explanation: Dict[str, Any]) -> str:
        """生成教程文档"""
        analysis = explanation['analysis']
        explanations = explanation['explanations']
        learning_points = explanation.get('learning_points', [])
        
        doc = f"""
# SQL查询教程

## 学习目标
通过这个查询示例，您将学习：
"""
        
        for point in learning_points:
            doc += f"- {point['description']}\n"
        
        doc += f"""

## 查询解析

### 第一步：理解查询目的
{explanations['basic']}

### 第二步：分析查询结构
```sql
{sql}
```

这个查询包含以下组件：
"""
        
        if analysis['tables']:
            doc += f"- **数据表**: {', '.join(analysis['tables'])}\n"
        
        if analysis['joins']:
            doc += f"- **表连接**: {len(analysis['joins'])}个JOIN操作\n"
        
        if analysis['conditions']:
            doc += f"- **筛选条件**: {len(analysis['conditions'])}个WHERE条件\n"
        
        if analysis['aggregations']:
            doc += f"- **聚合函数**: {', '.join(analysis['aggregations'])}\n"
        
        doc += "\n### 第三步：逐步解释\n"
        doc += self._generate_step_by_step_explanation(sql, analysis)
        
        doc += "\n## 练习建议\n"
        doc += self._generate_practice_suggestions(analysis)
        
        return doc
    
    def _get_table_business_description(self, table_name: str) -> str:
        """获取表的业务描述"""
        # 这里可以从schema信息或配置中获取表的业务含义
        descriptions = {
            'users': '用户信息表，包含用户基本资料',
            'orders': '订单信息表，记录所有交易订单',
            'products': '产品信息表，包含商品详情',
            'customers': '客户信息表，存储客户数据'
        }
        
        return descriptions.get(table_name.lower(), f'{table_name}数据表')
    
    def _describe_business_results(self, analysis: Dict[str, Any]) -> str:
        """描述业务结果"""
        if analysis['aggregations']:
            return "查询将返回统计汇总数据，用于业务分析和决策支持。"
        elif len(analysis['tables']) > 1:
            return "查询将返回多表关联的详细数据，提供完整的业务视图。"
        else:
            return "查询将返回符合条件的详细记录，用于具体业务操作。"
    
    def _generate_use_cases(self, analysis: Dict[str, Any]) -> str:
        """生成使用场景"""
        use_cases = []
        
        if analysis['aggregations']:
            use_cases.append("- 业务报表生成")
            use_cases.append("- 数据分析和统计")
            use_cases.append("- KPI指标计算")
        
        if len(analysis['tables']) > 1:
            use_cases.append("- 跨部门数据整合")
            use_cases.append("- 业务流程分析")
        
        if analysis['conditions']:
            use_cases.append("- 精准数据筛选")
            use_cases.append("- 条件查询和检索")
        
        if not use_cases:
            use_cases.append("- 基础数据查询")
            use_cases.append("- 数据浏览和检索")
        
        return "\n".join(use_cases)
    
    def _generate_step_by_step_explanation(self, sql: str, analysis: Dict[str, Any]) -> str:
        """生成逐步解释"""
        steps = []
        step_num = 1
        
        # FROM子句
        if analysis['tables']:
            steps.append(f"**步骤 {step_num}**: 从 {analysis['tables'][0]} 表开始查询")
            step_num += 1
        
        # JOIN子句
        for join in analysis['joins']:
            steps.append(f"**步骤 {step_num}**: 通过 {join['type']} 连接 {join['table']} 表")
            step_num += 1
        
        # WHERE子句
        if analysis['conditions']:
            steps.append(f"**步骤 {step_num}**: 应用筛选条件过滤数据")
            step_num += 1
        
        # GROUP BY子句
        if analysis['grouping']:
            steps.append(f"**步骤 {step_num}**: 按 {', '.join(analysis['grouping'])} 分组")
            step_num += 1
        
        # ORDER BY子句
        if analysis['ordering']:
            steps.append(f"**步骤 {step_num}**: 按 {', '.join(analysis['ordering'])} 排序")
            step_num += 1
        
        # SELECT子句
        steps.append(f"**步骤 {step_num}**: 选择并返回指定的列")
        
        return "\n".join(steps)
    
    def _generate_practice_suggestions(self, analysis: Dict[str, Any]) -> str:
        """生成练习建议"""
        suggestions = []
        
        if analysis['joins']:
            suggestions.append("- 尝试修改JOIN类型，观察结果差异")
            suggestions.append("- 练习编写不同的JOIN条件")
        
        if analysis['conditions']:
            suggestions.append("- 修改WHERE条件，观察筛选效果")
            suggestions.append("- 尝试添加更多筛选条件")
        
        if analysis['aggregations']:
            suggestions.append("- 尝试使用不同的聚合函数")
            suggestions.append("- 练习GROUP BY和HAVING的组合使用")
        
        suggestions.append("- 分析查询的执行计划")
        suggestions.append("- 尝试优化查询性能")
        
        return "\n".join(suggestions)
    
    def _load_document_templates(self) -> Dict[str, str]:
        """加载文档模板"""
        return {
            'technical': 'technical_template.md',
            'business': 'business_template.md',
            'tutorial': 'tutorial_template.md'
        }
```

## API接口

### REST API

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class SQLExplanationRequest(BaseModel):
    sql: str
    context: Optional[Dict[str, Any]] = None
    detail_level: str = "medium"  # basic, medium, detailed

class DocumentGenerationRequest(BaseModel):
    sql: str
    context: Optional[Dict[str, Any]] = None
    doc_type: str = "technical"  # technical, business, tutorial

@router.post("/explain")
async def explain_sql(
    request: SQLExplanationRequest,
    explainer: SQLExplainerAgent = Depends(get_sql_explainer)
):
    """解释SQL查询"""
    try:
        result = await explainer.explain_sql(
            request.sql,
            request.context,
            request.detail_level
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-documentation")
async def generate_documentation(
    request: DocumentGenerationRequest,
    doc_generator: DocumentationGenerator = Depends(get_doc_generator)
):
    """生成查询文档"""
    try:
        result = await doc_generator.generate_query_documentation(
            request.sql,
            request.context,
            request.doc_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-complexity")
async def analyze_complexity(
    request: SQLExplanationRequest,
    explainer: SQLExplainerAgent = Depends(get_sql_explainer)
):
    """分析查询复杂度"""
    try:
        explanation = await explainer.explain_sql(request.sql, request.context)
        if explanation['success']:
            return {
                'success': True,
                'complexity_assessment': explanation['complexity_assessment'],
                'optimization_suggestions': explanation['optimization_suggestions']
            }
        else:
            return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 测试用例

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestSQLExplainerAgent:
    @pytest.fixture
    def mock_llm_client(self):
        client = AsyncMock()
        client.generate_response.return_value = "这是一个查询用户信息的SQL语句。"
        return client
    
    @pytest.fixture
    def explainer(self, mock_llm_client):
        return SQLExplainerAgent(mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_explain_simple_select(self, explainer):
        """测试简单SELECT查询解释"""
        sql = "SELECT name, age FROM users WHERE age > 18"
        result = await explainer.explain_sql(sql)
        
        assert result['success']
        assert 'explanations' in result
        assert 'optimization_suggestions' in result
        assert 'learning_points' in result
    
    @pytest.mark.asyncio
    async def test_explain_join_query(self, explainer):
        """测试JOIN查询解释"""
        sql = """
        SELECT u.name, o.total 
        FROM users u 
        INNER JOIN orders o ON u.id = o.user_id 
        WHERE o.status = 'completed'
        """
        result = await explainer.explain_sql(sql)
        
        assert result['success']
        analysis = result['analysis']
        assert len(analysis['tables']) == 2
        assert len(analysis['joins']) == 1
        assert analysis['joins'][0]['type'] == 'INNER JOIN'
    
    def test_analyze_sql_structure(self, explainer):
        """测试SQL结构分析"""
        sql = "SELECT COUNT(*) FROM users GROUP BY department ORDER BY COUNT(*) DESC"
        analysis = explainer._analyze_sql_structure(sql)
        
        assert analysis.query_type == QueryType.SELECT
        assert 'users' in analysis.tables
        assert len(analysis.aggregations) > 0
        assert len(analysis.grouping) > 0
        assert len(analysis.ordering) > 0
    
    def test_extract_tables(self, explainer):
        """测试表名提取"""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        tables = explainer._extract_tables(sql)
        
        assert 'users' in tables
        assert 'orders' in tables
    
    def test_analyze_joins(self, explainer):
        """测试JOIN分析"""
        sql = "SELECT * FROM users u LEFT JOIN orders o ON u.id = o.user_id"
        joins = explainer._analyze_joins(sql)
        
        assert len(joins) == 1
        assert joins[0]['type'] == 'LEFT JOIN'
        assert joins[0]['table'] == 'orders'
    
    def test_calculate_complexity_score(self, explainer):
        """测试复杂度计算"""
        tables = ['users', 'orders', 'products']
        joins = [{'type': 'INNER JOIN'}, {'type': 'LEFT JOIN'}]
        conditions = ['age > 18', 'status = "active"']
        aggregations = ['COUNT(*)']
        
        score = explainer._calculate_complexity_score(tables, joins, conditions, aggregations)
        
        assert score > 0
        assert score <= 10.0

class TestDocumentationGenerator:
    @pytest.fixture
    def mock_explainer(self):
        explainer = AsyncMock()
        explainer.explain_sql.return_value = {
            'success': True,
            'analysis': {
                'query_type': 'SELECT',
                'tables': ['users'],
                'columns': ['name', 'age'],
                'joins': [],
                'conditions': [{'condition': 'age > 18', 'explanation': '年龄大于18'}],
                'aggregations': [],
                'ordering': [],
                'grouping': [],
                'complexity_score': 2.0,
                'estimated_performance': '良好'
            },
            'explanations': {
                'basic': '查询成年用户信息',
                'business': '获取所有成年用户的姓名和年龄信息'
            },
            'optimization_suggestions': [],
            'learning_points': []
        }
        return explainer
    
    @pytest.fixture
    def doc_generator(self, mock_explainer):
        return DocumentationGenerator(mock_explainer)
    
    @pytest.mark.asyncio
    async def test_generate_technical_documentation(self, doc_generator):
        """测试技术文档生成"""
        sql = "SELECT name, age FROM users WHERE age > 18"
        result = await doc_generator.generate_query_documentation(sql, doc_type="technical")
        
        assert result['success']
        assert 'document' in result
        assert '# SQL查询技术文档' in result['document']
        assert 'SQL语句' in result['document']
    
    @pytest.mark.asyncio
    async def test_generate_business_documentation(self, doc_generator):
        """测试业务文档生成"""
        sql = "SELECT name, age FROM users WHERE age > 18"
        result = await doc_generator.generate_query_documentation(sql, doc_type="business")
        
        assert result['success']
        assert 'document' in result
        assert '# 查询业务文档' in result['document']
        assert '业务目的' in result['document']
```

---

*此文档提供了SQL解释与文档生成服务的完整实现指南，包括SQL结构分析、自然语言解释、优化建议生成和多类型文档生成功能。*