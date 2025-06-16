# SQL执行与结果处理服务功能还原提示词

## 服务概述

SQL执行与结果处理服务负责安全地执行生成的SQL语句，处理查询结果，并将结果转换为用户友好的格式。该服务确保数据安全、性能优化和结果的准确展示。

## 核心功能

### 1. 安全SQL执行
- SQL注入防护和安全检查
- 查询权限验证和访问控制
- 查询超时和资源限制
- 只读查询强制执行

### 2. 结果数据处理
- 查询结果格式化和类型转换
- 大数据集分页和流式处理
- 数据脱敏和隐私保护
- 结果缓存和性能优化

### 3. 错误处理与恢复
- 数据库连接异常处理
- SQL执行错误分析和报告
- 自动重试和故障恢复
- 详细的错误日志记录

### 4. 结果可视化准备
- 数据类型分析和推荐图表类型
- 统计信息计算和摘要生成
- 数据质量检查和异常值检测
- 可视化数据结构优化

## 技术实现

### SQL执行器核心类

```python
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import time
from datetime import datetime, timedelta
import hashlib
import json
from dataclasses import dataclass

@dataclass
class ExecutionConfig:
    """执行配置"""
    max_execution_time: int = 30  # 最大执行时间（秒）
    max_rows: int = 10000  # 最大返回行数
    enable_cache: bool = True
    cache_ttl: int = 300  # 缓存过期时间（秒）
    enable_pagination: bool = True
    page_size: int = 100
    enable_data_masking: bool = True
    sensitive_columns: List[str] = None

class SQLExecutorAgent:
    """SQL执行智能体"""
    
    def __init__(self, db_access, config: ExecutionConfig = None):
        self.db_access = db_access
        self.config = config or ExecutionConfig()
        self.result_cache = {}
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'cache_hits': 0
        }
    
    async def execute_sql(self, 
                         sql: str, 
                         user_id: str = None,
                         session_id: str = None) -> Dict[str, Any]:
        """执行SQL查询"""
        execution_id = self._generate_execution_id(sql, user_id)
        
        try:
            # 安全检查
            security_check = await self._security_check(sql, user_id)
            if not security_check['is_safe']:
                return {
                    'success': False,
                    'error': f"安全检查失败: {security_check['reason']}",
                    'error_type': 'SECURITY_ERROR',
                    'execution_id': execution_id
                }
            
            # 检查缓存
            if self.config.enable_cache:
                cached_result = self._get_cached_result(sql)
                if cached_result:
                    self.execution_stats['cache_hits'] += 1
                    return {
                        **cached_result,
                        'from_cache': True,
                        'execution_id': execution_id
                    }
            
            # 执行SQL
            start_time = time.time()
            execution_result = await self._execute_with_timeout(sql)
            execution_time = time.time() - start_time
            
            # 处理结果
            processed_result = await self._process_result(
                execution_result, sql, execution_time
            )
            
            # 缓存结果
            if self.config.enable_cache and processed_result['success']:
                self._cache_result(sql, processed_result)
            
            # 更新统计
            self.execution_stats['total_executions'] += 1
            if processed_result['success']:
                self.execution_stats['successful_executions'] += 1
            else:
                self.execution_stats['failed_executions'] += 1
            
            processed_result['execution_id'] = execution_id
            return processed_result
            
        except Exception as e:
            logger.error(f"SQL执行异常 [{execution_id}]: {e}")
            self.execution_stats['total_executions'] += 1
            self.execution_stats['failed_executions'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'error_type': 'EXECUTION_ERROR',
                'execution_id': execution_id,
                'execution_time': 0
            }
    
    async def _security_check(self, sql: str, user_id: str = None) -> Dict[str, Any]:
        """SQL安全检查"""
        sql_upper = sql.upper().strip()
        
        # 检查是否为只读查询
        readonly_keywords = ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']
        if not any(sql_upper.startswith(keyword) for keyword in readonly_keywords):
            return {
                'is_safe': False,
                'reason': '只允许执行只读查询（SELECT、WITH、SHOW、DESCRIBE、EXPLAIN）'
            }
        
        # 检查危险关键字
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'MERGE', 'CALL', 'EXEC'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    'is_safe': False,
                    'reason': f'检测到危险关键字: {keyword}'
                }
        
        # 检查SQL注入模式
        injection_patterns = [
            r"';\s*--",  # 注释注入
            r"\bunion\s+select\b",  # UNION注入
            r"\bor\s+1\s*=\s*1\b",  # 布尔注入
            r"\band\s+1\s*=\s*1\b",
            r"\bxp_cmdshell\b",  # 系统命令执行
            r"\bsp_executesql\b"
        ]
        
        import re
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return {
                    'is_safe': False,
                    'reason': f'检测到可能的SQL注入模式: {pattern}'
                }
        
        # 检查用户权限（如果提供了user_id）
        if user_id:
            permission_check = await self._check_user_permissions(user_id, sql)
            if not permission_check['has_permission']:
                return {
                    'is_safe': False,
                    'reason': f'用户权限不足: {permission_check["reason"]}'
                }
        
        return {'is_safe': True, 'reason': '安全检查通过'}
    
    async def _check_user_permissions(self, user_id: str, sql: str) -> Dict[str, Any]:
        """检查用户权限"""
        # 简化的权限检查逻辑
        # 实际实现应该查询用户权限表
        
        # 提取查询涉及的表名
        import re
        table_matches = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        tables = [match.lower() for match in table_matches]
        
        # 检查敏感表访问权限
        sensitive_tables = ['user_credentials', 'payment_info', 'personal_data']
        for table in tables:
            if table in sensitive_tables:
                # 这里应该查询用户是否有访问该表的权限
                # 简化实现，假设普通用户不能访问敏感表
                if not await self._user_has_sensitive_access(user_id):
                    return {
                        'has_permission': False,
                        'reason': f'无权访问敏感表: {table}'
                    }
        
        return {'has_permission': True, 'reason': '权限检查通过'}
    
    async def _user_has_sensitive_access(self, user_id: str) -> bool:
        """检查用户是否有敏感数据访问权限"""
        # 简化实现，实际应该查询权限系统
        return False
    
    async def _execute_with_timeout(self, sql: str) -> Dict[str, Any]:
        """带超时的SQL执行"""
        try:
            # 使用asyncio.wait_for实现超时控制
            result = await asyncio.wait_for(
                self.db_access.execute_query(sql),
                timeout=self.config.max_execution_time
            )
            
            return {
                'success': True,
                'data': result,
                'row_count': len(result) if result else 0
            }
            
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': f'查询超时（超过{self.config.max_execution_time}秒）',
                'error_type': 'TIMEOUT_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'DATABASE_ERROR'
            }
    
    async def _process_result(self, 
                            execution_result: Dict[str, Any], 
                            sql: str, 
                            execution_time: float) -> Dict[str, Any]:
        """处理查询结果"""
        if not execution_result['success']:
            return {
                'success': False,
                'error': execution_result['error'],
                'error_type': execution_result.get('error_type', 'UNKNOWN_ERROR'),
                'execution_time': execution_time
            }
        
        raw_data = execution_result['data']
        row_count = execution_result['row_count']
        
        # 检查结果大小限制
        if row_count > self.config.max_rows:
            raw_data = raw_data[:self.config.max_rows]
            truncated = True
        else:
            truncated = False
        
        # 数据类型转换和格式化
        formatted_data = self._format_data(raw_data)
        
        # 数据脱敏
        if self.config.enable_data_masking:
            formatted_data = self._mask_sensitive_data(formatted_data)
        
        # 生成数据摘要
        data_summary = self._generate_data_summary(formatted_data)
        
        # 分析数据类型和推荐可视化
        visualization_suggestions = self._suggest_visualizations(formatted_data)
        
        return {
            'success': True,
            'data': formatted_data,
            'row_count': len(formatted_data),
            'total_rows': row_count,
            'truncated': truncated,
            'execution_time': execution_time,
            'data_summary': data_summary,
            'visualization_suggestions': visualization_suggestions,
            'sql': sql,
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_data(self, raw_data: List[Dict]) -> List[Dict]:
        """格式化数据"""
        if not raw_data:
            return []
        
        formatted_data = []
        for row in raw_data:
            formatted_row = {}
            for key, value in row.items():
                # 处理不同数据类型
                if value is None:
                    formatted_row[key] = None
                elif isinstance(value, datetime):
                    formatted_row[key] = value.isoformat()
                elif isinstance(value, (int, float)):
                    formatted_row[key] = value
                elif isinstance(value, bool):
                    formatted_row[key] = value
                else:
                    formatted_row[key] = str(value)
            
            formatted_data.append(formatted_row)
        
        return formatted_data
    
    def _mask_sensitive_data(self, data: List[Dict]) -> List[Dict]:
        """数据脱敏"""
        if not self.config.sensitive_columns:
            return data
        
        masked_data = []
        for row in data:
            masked_row = {}
            for key, value in row.items():
                if key.lower() in [col.lower() for col in self.config.sensitive_columns]:
                    # 脱敏处理
                    if isinstance(value, str) and len(value) > 4:
                        masked_row[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                    else:
                        masked_row[key] = '***'
                else:
                    masked_row[key] = value
            
            masked_data.append(masked_row)
        
        return masked_data
    
    def _generate_data_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """生成数据摘要"""
        if not data:
            return {
                'row_count': 0,
                'column_count': 0,
                'columns': [],
                'data_types': {},
                'statistics': {}
            }
        
        # 基本信息
        row_count = len(data)
        columns = list(data[0].keys()) if data else []
        column_count = len(columns)
        
        # 数据类型分析
        data_types = {}
        statistics = {}
        
        for column in columns:
            values = [row.get(column) for row in data if row.get(column) is not None]
            
            if not values:
                data_types[column] = 'null'
                continue
            
            # 推断数据类型
            sample_value = values[0]
            if isinstance(sample_value, (int, float)):
                data_types[column] = 'numeric'
                # 数值统计
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                if numeric_values:
                    statistics[column] = {
                        'min': min(numeric_values),
                        'max': max(numeric_values),
                        'avg': sum(numeric_values) / len(numeric_values),
                        'count': len(numeric_values)
                    }
            elif isinstance(sample_value, bool):
                data_types[column] = 'boolean'
                # 布尔统计
                true_count = sum(1 for v in values if v is True)
                statistics[column] = {
                    'true_count': true_count,
                    'false_count': len(values) - true_count,
                    'total_count': len(values)
                }
            elif isinstance(sample_value, str):
                # 检查是否为日期
                if self._is_date_string(sample_value):
                    data_types[column] = 'date'
                else:
                    data_types[column] = 'text'
                
                # 文本统计
                unique_values = len(set(values))
                statistics[column] = {
                    'unique_count': unique_values,
                    'total_count': len(values),
                    'avg_length': sum(len(str(v)) for v in values) / len(values)
                }
            else:
                data_types[column] = 'unknown'
        
        return {
            'row_count': row_count,
            'column_count': column_count,
            'columns': columns,
            'data_types': data_types,
            'statistics': statistics
        }
    
    def _is_date_string(self, value: str) -> bool:
        """检查字符串是否为日期格式"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
        ]
        
        import re
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        return False
    
    def _suggest_visualizations(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """推荐可视化方案"""
        if not data:
            return []
        
        suggestions = []
        columns = list(data[0].keys())
        
        # 分析列的数据类型
        numeric_columns = []
        text_columns = []
        date_columns = []
        
        for column in columns:
            sample_values = [row.get(column) for row in data[:10] if row.get(column) is not None]
            if not sample_values:
                continue
            
            sample_value = sample_values[0]
            if isinstance(sample_value, (int, float)):
                numeric_columns.append(column)
            elif isinstance(sample_value, str) and self._is_date_string(sample_value):
                date_columns.append(column)
            else:
                text_columns.append(column)
        
        # 基于数据特征推荐图表
        if len(numeric_columns) >= 2:
            suggestions.append({
                'type': 'scatter',
                'title': '散点图',
                'description': '适合显示两个数值变量之间的关系',
                'x_axis': numeric_columns[0],
                'y_axis': numeric_columns[1],
                'confidence': 0.8
            })
        
        if len(numeric_columns) >= 1 and len(text_columns) >= 1:
            suggestions.append({
                'type': 'bar',
                'title': '柱状图',
                'description': '适合显示分类数据的数值比较',
                'x_axis': text_columns[0],
                'y_axis': numeric_columns[0],
                'confidence': 0.9
            })
        
        if len(date_columns) >= 1 and len(numeric_columns) >= 1:
            suggestions.append({
                'type': 'line',
                'title': '折线图',
                'description': '适合显示时间序列数据的趋势',
                'x_axis': date_columns[0],
                'y_axis': numeric_columns[0],
                'confidence': 0.85
            })
        
        if len(text_columns) >= 1:
            # 检查是否适合饼图（分类数据且类别不太多）
            category_column = text_columns[0]
            unique_values = len(set(row.get(category_column) for row in data))
            
            if unique_values <= 10:
                suggestions.append({
                    'type': 'pie',
                    'title': '饼图',
                    'description': '适合显示分类数据的占比',
                    'category': category_column,
                    'confidence': 0.7
                })
        
        # 表格总是一个选项
        suggestions.append({
            'type': 'table',
            'title': '数据表格',
            'description': '以表格形式显示详细数据',
            'confidence': 1.0
        })
        
        # 按置信度排序
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions
    
    def _generate_execution_id(self, sql: str, user_id: str = None) -> str:
        """生成执行ID"""
        content = f"{sql}_{user_id}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_cached_result(self, sql: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        cache_key = hashlib.md5(sql.encode()).hexdigest()
        
        if cache_key in self.result_cache:
            cached_item = self.result_cache[cache_key]
            
            # 检查是否过期
            if datetime.now() - cached_item['timestamp'] < timedelta(seconds=self.config.cache_ttl):
                return cached_item['result']
            else:
                # 清理过期缓存
                del self.result_cache[cache_key]
        
        return None
    
    def _cache_result(self, sql: str, result: Dict[str, Any]):
        """缓存结果"""
        cache_key = hashlib.md5(sql.encode()).hexdigest()
        
        # 限制缓存大小
        if len(self.result_cache) >= 100:
            # 删除最旧的缓存项
            oldest_key = min(self.result_cache.keys(), 
                            key=lambda k: self.result_cache[k]['timestamp'])
            del self.result_cache[oldest_key]
        
        self.result_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now()
        }
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        total = self.execution_stats['total_executions']
        success_rate = (self.execution_stats['successful_executions'] / total * 100) if total > 0 else 0
        cache_hit_rate = (self.execution_stats['cache_hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.execution_stats,
            'success_rate': round(success_rate, 2),
            'cache_hit_rate': round(cache_hit_rate, 2)
        }
```

### 分页查询处理

```python
class PaginatedQueryExecutor:
    """分页查询执行器"""
    
    def __init__(self, sql_executor: SQLExecutorAgent):
        self.sql_executor = sql_executor
    
    async def execute_paginated_query(self, 
                                     sql: str, 
                                     page: int = 1, 
                                     page_size: int = 100,
                                     user_id: str = None) -> Dict[str, Any]:
        """执行分页查询"""
        try:
            # 首先获取总行数
            count_sql = self._build_count_sql(sql)
            count_result = await self.sql_executor.execute_sql(count_sql, user_id)
            
            if not count_result['success']:
                return count_result
            
            total_rows = count_result['data'][0]['total_count'] if count_result['data'] else 0
            total_pages = (total_rows + page_size - 1) // page_size
            
            # 构建分页SQL
            paginated_sql = self._build_paginated_sql(sql, page, page_size)
            
            # 执行分页查询
            result = await self.sql_executor.execute_sql(paginated_sql, user_id)
            
            if result['success']:
                result.update({
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_rows': total_rows,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"分页查询执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PAGINATION_ERROR'
            }
    
    def _build_count_sql(self, sql: str) -> str:
        """构建计数SQL"""
        # 简化实现，实际需要更复杂的SQL解析
        return f"SELECT COUNT(*) as total_count FROM ({sql}) as count_query"
    
    def _build_paginated_sql(self, sql: str, page: int, page_size: int) -> str:
        """构建分页SQL"""
        offset = (page - 1) * page_size
        
        # 检查SQL是否已经有LIMIT子句
        if 'LIMIT' in sql.upper():
            # 如果已有LIMIT，需要替换
            import re
            sql = re.sub(r'\s+LIMIT\s+\d+(?:\s+OFFSET\s+\d+)?\s*;?\s*$', '', sql, flags=re.IGNORECASE)
        
        # 添加分页子句
        return f"{sql} LIMIT {page_size} OFFSET {offset}"
```

### 流式查询处理

```python
class StreamingQueryExecutor:
    """流式查询执行器"""
    
    def __init__(self, sql_executor: SQLExecutorAgent):
        self.sql_executor = sql_executor
    
    async def execute_streaming_query(self, 
                                     sql: str, 
                                     chunk_size: int = 1000,
                                     user_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """执行流式查询"""
        try:
            # 安全检查
            security_check = await self.sql_executor._security_check(sql, user_id)
            if not security_check['is_safe']:
                yield {
                    'type': 'error',
                    'error': f"安全检查失败: {security_check['reason']}",
                    'error_type': 'SECURITY_ERROR'
                }
                return
            
            # 发送开始信号
            yield {
                'type': 'start',
                'message': '开始执行查询',
                'timestamp': datetime.now().isoformat()
            }
            
            # 流式执行查询
            async for chunk in self._stream_query_results(sql, chunk_size):
                yield {
                    'type': 'data',
                    'data': chunk['data'],
                    'chunk_index': chunk['chunk_index'],
                    'chunk_size': len(chunk['data']),
                    'timestamp': datetime.now().isoformat()
                }
            
            # 发送完成信号
            yield {
                'type': 'complete',
                'message': '查询执行完成',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                'type': 'error',
                'error': str(e),
                'error_type': 'STREAMING_ERROR',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _stream_query_results(self, sql: str, chunk_size: int) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取查询结果"""
        # 这里需要根据具体数据库实现流式查询
        # 简化实现，实际应该使用数据库的游标功能
        
        page = 1
        chunk_index = 0
        
        while True:
            # 分页获取数据
            paginated_sql = f"{sql} LIMIT {chunk_size} OFFSET {(page - 1) * chunk_size}"
            
            try:
                result = await self.sql_executor.db_access.execute_query(paginated_sql)
                
                if not result or len(result) == 0:
                    break
                
                yield {
                    'data': result,
                    'chunk_index': chunk_index
                }
                
                chunk_index += 1
                page += 1
                
                # 如果返回的数据少于chunk_size，说明已经是最后一批
                if len(result) < chunk_size:
                    break
                    
            except Exception as e:
                logger.error(f"流式查询块 {chunk_index} 失败: {e}")
                break
```

### 结果导出服务

```python
import csv
import json
import io
from typing import List, Dict, Any

class ResultExporter:
    """结果导出服务"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'excel', 'txt']
    
    async def export_results(self, 
                           data: List[Dict[str, Any]], 
                           format: str = 'csv',
                           filename: str = None) -> Dict[str, Any]:
        """导出查询结果"""
        if format not in self.supported_formats:
            return {
                'success': False,
                'error': f'不支持的导出格式: {format}',
                'supported_formats': self.supported_formats
            }
        
        try:
            if format == 'csv':
                content = self._export_to_csv(data)
                content_type = 'text/csv'
            elif format == 'json':
                content = self._export_to_json(data)
                content_type = 'application/json'
            elif format == 'excel':
                content = self._export_to_excel(data)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif format == 'txt':
                content = self._export_to_txt(data)
                content_type = 'text/plain'
            
            return {
                'success': True,
                'content': content,
                'content_type': content_type,
                'filename': filename or f'query_result.{format}',
                'size': len(content) if isinstance(content, (str, bytes)) else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'导出失败: {str(e)}'
            }
    
    def _export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """导出为CSV格式"""
        if not data:
            return ''
        
        output = io.StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            # 处理None值和特殊字符
            cleaned_row = {}
            for key, value in row.items():
                if value is None:
                    cleaned_row[key] = ''
                else:
                    cleaned_row[key] = str(value)
            writer.writerow(cleaned_row)
        
        return output.getvalue()
    
    def _export_to_json(self, data: List[Dict[str, Any]]) -> str:
        """导出为JSON格式"""
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    def _export_to_excel(self, data: List[Dict[str, Any]]) -> bytes:
        """导出为Excel格式"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            # 使用BytesIO创建Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Query Results')
            
            return output.getvalue()
            
        except ImportError:
            raise Exception("需要安装pandas和openpyxl库来支持Excel导出")
    
    def _export_to_txt(self, data: List[Dict[str, Any]]) -> str:
        """导出为文本格式"""
        if not data:
            return ''
        
        lines = []
        fieldnames = list(data[0].keys())
        
        # 表头
        lines.append('\t'.join(fieldnames))
        lines.append('-' * 50)
        
        # 数据行
        for row in data:
            values = [str(row.get(field, '')) for field in fieldnames]
            lines.append('\t'.join(values))
        
        return '\n'.join(lines)
```

## 错误处理和监控

### 错误分类和处理

```python
from enum import Enum

class ErrorType(Enum):
    SECURITY_ERROR = "SECURITY_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.error_patterns = {
            'connection': ['connection', 'connect', 'timeout', 'network'],
            'syntax': ['syntax', 'parse', 'invalid', 'malformed'],
            'permission': ['permission', 'access', 'denied', 'unauthorized'],
            'resource': ['memory', 'disk', 'resource', 'limit']
        }
    
    def classify_error(self, error_message: str) -> ErrorType:
        """分类错误类型"""
        error_lower = error_message.lower()
        
        for category, keywords in self.error_patterns.items():
            if any(keyword in error_lower for keyword in keywords):
                if category == 'connection':
                    return ErrorType.DATABASE_ERROR
                elif category == 'syntax':
                    return ErrorType.SYNTAX_ERROR
                elif category == 'permission':
                    return ErrorType.PERMISSION_ERROR
                elif category == 'resource':
                    return ErrorType.RESOURCE_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    def get_user_friendly_message(self, error_type: ErrorType, original_error: str) -> str:
        """获取用户友好的错误消息"""
        messages = {
            ErrorType.SECURITY_ERROR: "查询包含不安全的内容，请检查您的SQL语句",
            ErrorType.TIMEOUT_ERROR: "查询执行时间过长，请尝试优化您的查询或减少数据范围",
            ErrorType.DATABASE_ERROR: "数据库连接或执行出现问题，请稍后重试",
            ErrorType.PERMISSION_ERROR: "您没有权限执行此查询，请联系管理员",
            ErrorType.SYNTAX_ERROR: "SQL语法错误，请检查您的查询语句",
            ErrorType.RESOURCE_ERROR: "系统资源不足，请稍后重试或减少查询复杂度",
            ErrorType.UNKNOWN_ERROR: "执行过程中出现未知错误，请联系技术支持"
        }
        
        return messages.get(error_type, original_error)
    
    def should_retry(self, error_type: ErrorType) -> bool:
        """判断是否应该重试"""
        retry_types = {ErrorType.DATABASE_ERROR, ErrorType.TIMEOUT_ERROR, ErrorType.RESOURCE_ERROR}
        return error_type in retry_types
```

### 性能监控

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# 监控指标
sql_executions = Counter('sql_executions_total', 'Total SQL executions', ['status', 'error_type'])
sql_execution_duration = Histogram('sql_execution_duration_seconds', 'SQL execution duration')
sql_result_size = Histogram('sql_result_size_bytes', 'SQL result size in bytes')
cache_operations = Counter('cache_operations_total', 'Cache operations', ['operation', 'result'])
active_connections = Gauge('active_database_connections', 'Active database connections')

class MonitoredSQLExecutor(SQLExecutorAgent):
    async def execute_sql(self, sql: str, user_id: str = None, session_id: str = None):
        start_time = time.time()
        
        try:
            result = await super().execute_sql(sql, user_id, session_id)
            
            # 记录执行状态
            status = 'success' if result['success'] else 'failure'
            error_type = result.get('error_type', 'none')
            sql_executions.labels(status=status, error_type=error_type).inc()
            
            # 记录结果大小
            if result['success'] and result.get('data'):
                result_size = len(json.dumps(result['data']).encode('utf-8'))
                sql_result_size.observe(result_size)
            
            return result
            
        finally:
            # 记录执行时间
            sql_execution_duration.observe(time.time() - start_time)
```

## API接口

### REST API

```python
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

class SQLExecutionRequest(BaseModel):
    sql: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    enable_cache: Optional[bool] = True
    max_rows: Optional[int] = 10000

class PaginatedExecutionRequest(BaseModel):
    sql: str
    page: int = 1
    page_size: int = 100
    user_id: Optional[str] = None

class ExportRequest(BaseModel):
    sql: str
    format: str = 'csv'
    filename: Optional[str] = None
    user_id: Optional[str] = None

@router.post("/execute")
async def execute_sql(
    request: SQLExecutionRequest,
    executor: SQLExecutorAgent = Depends(get_sql_executor)
):
    """执行SQL查询"""
    try:
        result = await executor.execute_sql(
            request.sql,
            request.user_id,
            request.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/paginated")
async def execute_paginated_sql(
    request: PaginatedExecutionRequest,
    paginated_executor: PaginatedQueryExecutor = Depends(get_paginated_executor)
):
    """执行分页SQL查询"""
    try:
        result = await paginated_executor.execute_paginated_query(
            request.sql,
            request.page,
            request.page_size,
            request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/stream")
async def execute_streaming_sql(
    request: SQLExecutionRequest,
    streaming_executor: StreamingQueryExecutor = Depends(get_streaming_executor)
):
    """执行流式SQL查询"""
    async def generate_stream():
        async for chunk in streaming_executor.execute_streaming_query(
            request.sql, user_id=request.user_id
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.post("/export")
async def export_results(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    executor: SQLExecutorAgent = Depends(get_sql_executor),
    exporter: ResultExporter = Depends(get_result_exporter)
):
    """导出查询结果"""
    try:
        # 执行查询
        result = await executor.execute_sql(request.sql, request.user_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # 导出结果
        export_result = await exporter.export_results(
            result['data'],
            request.format,
            request.filename
        )
        
        if not export_result['success']:
            raise HTTPException(status_code=500, detail=export_result['error'])
        
        # 返回文件
        return StreamingResponse(
            io.BytesIO(export_result['content'].encode() if isinstance(export_result['content'], str) else export_result['content']),
            media_type=export_result['content_type'],
            headers={"Content-Disposition": f"attachment; filename={export_result['filename']}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_execution_stats(
    executor: SQLExecutorAgent = Depends(get_sql_executor)
):
    """获取执行统计信息"""
    return await executor.get_execution_stats()
```

## 测试用例

### 单元测试

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestSQLExecutorAgent:
    @pytest.fixture
    def mock_db_access(self):
        db_access = AsyncMock()
        db_access.execute_query.return_value = [
            {'id': 1, 'name': 'Alice', 'age': 25},
            {'id': 2, 'name': 'Bob', 'age': 30}
        ]
        return db_access
    
    @pytest.fixture
    def executor(self, mock_db_access):
        config = ExecutionConfig(max_execution_time=10, max_rows=1000)
        return SQLExecutorAgent(mock_db_access, config)
    
    @pytest.mark.asyncio
    async def test_execute_valid_sql(self, executor):
        """测试执行有效SQL"""
        sql = "SELECT * FROM users WHERE age > 18"
        result = await executor.execute_sql(sql)
        
        assert result['success']
        assert len(result['data']) == 2
        assert 'data_summary' in result
        assert 'visualization_suggestions' in result
    
    @pytest.mark.asyncio
    async def test_security_check_dangerous_sql(self, executor):
        """测试危险SQL的安全检查"""
        sql = "DROP TABLE users"
        result = await executor.execute_sql(sql)
        
        assert not result['success']
        assert result['error_type'] == 'SECURITY_ERROR'
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, executor):
        """测试缓存功能"""
        sql = "SELECT * FROM users"
        
        # 第一次执行
        result1 = await executor.execute_sql(sql)
        assert result1['success']
        assert not result1.get('from_cache', False)
        
        # 第二次执行应该从缓存获取
        result2 = await executor.execute_sql(sql)
        assert result2['success']
        assert result2.get('from_cache', False)  # 在测试中可能不会命中缓存
    
    def test_data_masking(self, executor):
        """测试数据脱敏"""
        executor.config.sensitive_columns = ['email', 'phone']
        
        data = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
        ]
        
        masked_data = executor._mask_sensitive_data(data)
        
        assert masked_data[0]['email'] != 'alice@example.com'
        assert '*' in masked_data[0]['email']
        assert masked_data[0]['name'] == 'Alice'  # 非敏感字段不变
    
    def test_visualization_suggestions(self, executor):
        """测试可视化建议"""
        data = [
            {'category': 'A', 'value': 100, 'date': '2023-01-01'},
            {'category': 'B', 'value': 200, 'date': '2023-01-02'}
        ]
        
        suggestions = executor._suggest_visualizations(data)
        
        assert len(suggestions) > 0
        assert any(s['type'] == 'bar' for s in suggestions)
        assert any(s['type'] == 'table' for s in suggestions)

class TestResultExporter:
    @pytest.fixture
    def exporter(self):
        return ResultExporter()
    
    @pytest.fixture
    def sample_data(self):
        return [
            {'id': 1, 'name': 'Alice', 'age': 25},
            {'id': 2, 'name': 'Bob', 'age': 30}
        ]
    
    @pytest.mark.asyncio
    async def test_csv_export(self, exporter, sample_data):
        """测试CSV导出"""
        result = await exporter.export_results(sample_data, 'csv')
        
        assert result['success']
        assert 'id,name,age' in result['content']
        assert 'Alice' in result['content']
    
    @pytest.mark.asyncio
    async def test_json_export(self, exporter, sample_data):
        """测试JSON导出"""
        result = await exporter.export_results(sample_data, 'json')
        
        assert result['success']
        assert result['content_type'] == 'application/json'
        
        # 验证JSON格式
        import json
        parsed_data = json.loads(result['content'])
        assert len(parsed_data) == 2
        assert parsed_data[0]['name'] == 'Alice'
```

---

*此文档提供了SQL执行与结果处理服务的完整实现指南，包括安全执行、结果处理、分页查询、流式处理、数据导出和性能监控。*