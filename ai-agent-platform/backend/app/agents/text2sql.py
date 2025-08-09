"""
# Copyright (c) 2025 左岚. All rights reserved.

Text2SQL智能体

将自然语言查询转换为SQL语句，并执行数据分析。
"""

# # Standard library imports
from datetime import datetime
from enum import Enum
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

# # Local folder imports
from .base import AgentConfig, AgentMessage, BaseAgent
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    JOIN = "join"
    COMPLEX = "complex"


class DatabaseSchema:
    """数据库模式"""
    
    def __init__(self, name: str, tables: Dict[str, Dict[str, Any]]):
        self.name = name
        self.tables = tables
        self.relationships = {}
    
    def add_relationship(self, table1: str, column1: str, table2: str, column2: str):
        """添加表关系"""
        if table1 not in self.relationships:
            self.relationships[table1] = []
        self.relationships[table1].append({
            "table": table2,
            "local_column": column1,
            "foreign_column": column2
        })
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表信息"""
        return self.tables.get(table_name)
    
    def get_schema_description(self) -> str:
        """获取模式描述"""
        description = f"数据库: {self.name}\n\n"
        
        for table_name, table_info in self.tables.items():
            description += f"表: {table_name}\n"
            description += f"描述: {table_info.get('description', '无描述')}\n"
            description += "字段:\n"
            
            for column_name, column_info in table_info.get('columns', {}).items():
                description += f"  - {column_name}: {column_info.get('type', 'unknown')} - {column_info.get('description', '无描述')}\n"
            
            if table_name in self.relationships:
                description += "关系:\n"
                for rel in self.relationships[table_name]:
                    description += f"  - {table_name}.{rel['local_column']} -> {rel['table']}.{rel['foreign_column']}\n"
            
            description += "\n"
        
        return description


class SQLQuery:
    """SQL查询结果"""
    
    def __init__(self, natural_query: str, sql: str, query_type: QueryType,
                 explanation: str = "", confidence: float = 0.0):
        self.natural_query = natural_query
        self.sql = sql
        self.query_type = query_type
        self.explanation = explanation
        self.confidence = confidence
        self.created_at = datetime.now()
        self.execution_result = None
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "natural_query": self.natural_query,
            "sql": self.sql,
            "query_type": self.query_type.value,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "execution_result": self.execution_result,
            "error_message": self.error_message
        }


class Text2SQLAgent(BaseAgent):
    """Text2SQL智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Text2SQLAgent",
                description="将自然语言查询转换为SQL语句并执行数据分析",
                model="gpt-4o",
                temperature=0.3,
                system_prompt=self._get_system_prompt()
            )
        
        super().__init__(config)
        
        # 数据库模式
        self.schemas: Dict[str, DatabaseSchema] = {}
        self.current_schema = None
        
        # 查询历史
        self.query_history: List[SQLQuery] = []
        
        # SQL安全检查
        self.forbidden_keywords = [
            "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"
        ]
        
        # 初始化示例模式
        self._initialize_sample_schema()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的SQL专家，能够将自然语言查询转换为准确的SQL语句。

核心能力：
1. 理解自然语言查询意图
2. 生成正确的SQL语句
3. 解释SQL逻辑
4. 优化查询性能
5. 处理复杂的多表关联

SQL生成原则：
1. 准确性：确保SQL语法正确，逻辑准确
2. 安全性：只生成SELECT查询，避免修改数据
3. 性能：考虑查询效率，适当使用索引
4. 可读性：生成清晰、易懂的SQL代码
5. 完整性：包含必要的WHERE条件和排序

返回格式：
{
    "sql": "SELECT语句",
    "query_type": "查询类型",
    "explanation": "SQL解释",
    "confidence": 0.95,
    "tables_used": ["表名1", "表名2"],
    "potential_issues": ["可能的问题"]
}

注意事项：
- 只生成SELECT查询
- 仔细检查表名和字段名
- 考虑数据类型匹配
- 处理NULL值情况
- 适当使用聚合函数和分组"""
    
    def _initialize_sample_schema(self):
        """初始化示例数据库模式"""
        # 示例：电商数据库
        ecommerce_tables = {
            "users": {
                "description": "用户表",
                "columns": {
                    "id": {"type": "INT", "description": "用户ID"},
                    "username": {"type": "VARCHAR(50)", "description": "用户名"},
                    "email": {"type": "VARCHAR(100)", "description": "邮箱"},
                    "created_at": {"type": "DATETIME", "description": "注册时间"},
                    "status": {"type": "VARCHAR(20)", "description": "用户状态"}
                }
            },
            "products": {
                "description": "产品表",
                "columns": {
                    "id": {"type": "INT", "description": "产品ID"},
                    "name": {"type": "VARCHAR(200)", "description": "产品名称"},
                    "price": {"type": "DECIMAL(10,2)", "description": "价格"},
                    "category_id": {"type": "INT", "description": "分类ID"},
                    "stock": {"type": "INT", "description": "库存数量"},
                    "created_at": {"type": "DATETIME", "description": "创建时间"}
                }
            },
            "orders": {
                "description": "订单表",
                "columns": {
                    "id": {"type": "INT", "description": "订单ID"},
                    "user_id": {"type": "INT", "description": "用户ID"},
                    "total_amount": {"type": "DECIMAL(10,2)", "description": "订单总额"},
                    "status": {"type": "VARCHAR(20)", "description": "订单状态"},
                    "created_at": {"type": "DATETIME", "description": "下单时间"}
                }
            },
            "order_items": {
                "description": "订单项表",
                "columns": {
                    "id": {"type": "INT", "description": "订单项ID"},
                    "order_id": {"type": "INT", "description": "订单ID"},
                    "product_id": {"type": "INT", "description": "产品ID"},
                    "quantity": {"type": "INT", "description": "数量"},
                    "price": {"type": "DECIMAL(10,2)", "description": "单价"}
                }
            }
        }
        
        schema = DatabaseSchema("ecommerce", ecommerce_tables)
        
        # 添加关系
        schema.add_relationship("orders", "user_id", "users", "id")
        schema.add_relationship("order_items", "order_id", "orders", "id")
        schema.add_relationship("order_items", "product_id", "products", "id")
        schema.add_relationship("products", "category_id", "categories", "id")
        
        self.schemas["ecommerce"] = schema
        self.current_schema = "ecommerce"
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理Text2SQL请求"""
        try:
            # 解析查询
            natural_query = message.content
            schema_name = message.metadata.get("schema", self.current_schema)
            
            # 生成SQL
            sql_query = await self.generate_sql(natural_query, schema_name)
            
            # 构建响应
            response_content = json.dumps({
                "sql": sql_query.sql,
                "explanation": sql_query.explanation,
                "query_type": sql_query.query_type.value,
                "confidence": sql_query.confidence
            }, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"sql_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="sql_result",
                metadata={
                    "original_message_id": message.id,
                    "sql_query": sql_query.to_dict()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Text2SQL处理失败: {e}")
            error_response = AgentMessage(
                id=f"sql_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"SQL生成失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def generate_sql(self, natural_query: str, schema_name: str = None) -> SQLQuery:
        """生成SQL查询"""
        try:
            schema_name = schema_name or self.current_schema
            schema = self.schemas.get(schema_name)
            
            if not schema:
                raise ValueError(f"未找到数据库模式: {schema_name}")
            
            # 构建提示
            schema_description = schema.get_schema_description()
            
            prompt = f"""
数据库模式：
{schema_description}

自然语言查询：{natural_query}

请将自然语言查询转换为SQL语句。

要求：
1. 只生成SELECT查询
2. 确保表名和字段名正确
3. 考虑数据类型和NULL值
4. 适当使用JOIN、WHERE、GROUP BY、ORDER BY
5. 返回JSON格式结果

返回格式：
{{
    "sql": "SELECT语句",
    "query_type": "select|aggregate|join|complex",
    "explanation": "SQL解释说明",
    "confidence": 0.95,
    "tables_used": ["表名1", "表名2"],
    "potential_issues": ["可能的问题或注意事项"]
}}
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=1500
            )
            
            try:
                result = json.loads(response.content)
                
                # 验证SQL安全性
                sql = result.get("sql", "")
                if not self._is_safe_sql(sql):
                    raise ValueError("SQL包含不安全的操作")
                
                # 创建SQLQuery对象
                query_type = QueryType(result.get("query_type", "select"))
                
                sql_query = SQLQuery(
                    natural_query=natural_query,
                    sql=sql,
                    query_type=query_type,
                    explanation=result.get("explanation", ""),
                    confidence=result.get("confidence", 0.5)
                )
                
                # 添加到历史
                self.query_history.append(sql_query)
                
                return sql_query
                
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试提取SQL
                sql_match = re.search(r'SELECT.*?(?=;|$)', response.content, re.IGNORECASE | re.DOTALL)
                if sql_match:
                    sql = sql_match.group(0).strip()
                    if self._is_safe_sql(sql):
                        return SQLQuery(
                            natural_query=natural_query,
                            sql=sql,
                            query_type=QueryType.SELECT,
                            explanation="自动提取的SQL语句",
                            confidence=0.6
                        )
                
                raise ValueError("无法解析SQL生成结果")
                
        except Exception as e:
            logger.error(f"SQL生成失败: {e}")
            raise
    
    def _is_safe_sql(self, sql: str) -> bool:
        """检查SQL安全性"""
        sql_upper = sql.upper()
        
        # 检查禁用关键词
        for keyword in self.forbidden_keywords:
            if keyword in sql_upper:
                return False
        
        # 必须是SELECT语句
        if not sql_upper.strip().startswith("SELECT"):
            return False
        
        return True
    
    async def explain_sql(self, sql: str) -> str:
        """解释SQL语句"""
        try:
            prompt = f"""
请详细解释以下SQL语句的执行逻辑：

SQL语句：
{sql}

解释要求：
1. 说明查询的目的和功能
2. 解释每个子句的作用
3. 说明表之间的关联关系
4. 指出可能的性能考虑
5. 使用通俗易懂的语言

解释：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.5,
                max_tokens=1000
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"SQL解释失败: {e}")
            return "SQL解释生成失败"
    
    async def optimize_sql(self, sql: str) -> Dict[str, Any]:
        """优化SQL查询"""
        try:
            prompt = f"""
请分析并优化以下SQL查询：

原始SQL：
{sql}

优化要求：
1. 提高查询性能
2. 减少资源消耗
3. 保持结果正确性
4. 提供优化建议

返回JSON格式：
{{
    "optimized_sql": "优化后的SQL",
    "improvements": ["改进点1", "改进点2"],
    "performance_gain": "预期性能提升",
    "explanation": "优化说明"
}}
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=1200
            )
            
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {
                    "optimized_sql": sql,
                    "improvements": [],
                    "performance_gain": "无法分析",
                    "explanation": "优化分析失败"
                }
                
        except Exception as e:
            logger.error(f"SQL优化失败: {e}")
            return {
                "optimized_sql": sql,
                "improvements": [],
                "performance_gain": "优化失败",
                "explanation": str(e)
            }
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def add_schema(self, schema: DatabaseSchema):
        """添加数据库模式"""
        self.schemas[schema.name] = schema
        logger.info(f"添加数据库模式: {schema.name}")
    
    def set_current_schema(self, schema_name: str):
        """设置当前数据库模式"""
        if schema_name in self.schemas:
            self.current_schema = schema_name
            logger.info(f"切换到数据库模式: {schema_name}")
        else:
            raise ValueError(f"数据库模式不存在: {schema_name}")
    
    def get_query_history(self, limit: int = 10) -> List[SQLQuery]:
        """获取查询历史"""
        return self.query_history[-limit:]
    
    def get_schema_info(self, schema_name: str = None) -> Optional[str]:
        """获取数据库模式信息"""
        schema_name = schema_name or self.current_schema
        schema = self.schemas.get(schema_name)
        if schema:
            return schema.get_schema_description()
        return None
    
    def list_schemas(self) -> List[str]:
        """列出所有数据库模式"""
        return list(self.schemas.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_queries": len(self.query_history),
            "schemas_count": len(self.schemas),
            "current_schema": self.current_schema,
            "average_confidence": sum(q.confidence for q in self.query_history) / len(self.query_history) if self.query_history else 0
        }
