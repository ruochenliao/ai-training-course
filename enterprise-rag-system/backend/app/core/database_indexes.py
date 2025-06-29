"""
数据库索引优化脚本
"""

from typing import List, Dict, Any
from loguru import logger
from tortoise import Tortoise


class DatabaseIndexOptimizer:
    """数据库索引优化器"""
    
    def __init__(self):
        self.index_definitions = self._get_recommended_indexes()
    
    def _get_recommended_indexes(self) -> List[Dict[str, Any]]:
        """获取推荐的索引定义"""
        return [
            # 用户表索引
            {
                "table": "users",
                "name": "idx_users_email",
                "columns": ["email"],
                "unique": True,
                "reason": "用户邮箱唯一性和登录查询优化"
            },
            {
                "table": "users",
                "name": "idx_users_username",
                "columns": ["username"],
                "unique": True,
                "reason": "用户名唯一性和查询优化"
            },
            {
                "table": "users",
                "name": "idx_users_status_active",
                "columns": ["status", "is_active"],
                "reason": "用户状态过滤查询优化"
            },
            {
                "table": "users",
                "name": "idx_users_created_at",
                "columns": ["created_at"],
                "reason": "用户注册时间范围查询优化"
            },
            {
                "table": "users",
                "name": "idx_users_last_login",
                "columns": ["last_login"],
                "reason": "用户活跃度查询优化"
            },
            {
                "table": "users",
                "name": "idx_users_department",
                "columns": ["department_id"],
                "reason": "部门用户查询优化"
            },
            
            # 知识库表索引
            {
                "table": "knowledge_bases",
                "name": "idx_kb_owner_status",
                "columns": ["owner_id", "status"],
                "reason": "用户知识库查询优化"
            },
            {
                "table": "knowledge_bases",
                "name": "idx_kb_visibility_status",
                "columns": ["visibility", "status"],
                "reason": "公开知识库查询优化"
            },
            {
                "table": "knowledge_bases",
                "name": "idx_kb_type_status",
                "columns": ["knowledge_type", "status"],
                "reason": "知识库类型查询优化"
            },
            {
                "table": "knowledge_bases",
                "name": "idx_kb_created_at",
                "columns": ["created_at"],
                "reason": "知识库创建时间查询优化"
            },
            {
                "table": "knowledge_bases",
                "name": "idx_kb_is_deleted",
                "columns": ["is_deleted"],
                "reason": "软删除过滤优化"
            },
            {
                "table": "knowledge_bases",
                "name": "idx_kb_department",
                "columns": ["department_id"],
                "reason": "部门知识库查询优化"
            },
            
            # 文档表索引
            {
                "table": "documents",
                "name": "idx_doc_kb_status",
                "columns": ["knowledge_base_id", "status"],
                "reason": "知识库文档查询优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_owner_status",
                "columns": ["owner_id", "status"],
                "reason": "用户文档查询优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_file_type",
                "columns": ["file_type"],
                "reason": "文档类型过滤优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_processing_status",
                "columns": ["processing_status"],
                "reason": "文档处理状态查询优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_created_at",
                "columns": ["created_at"],
                "reason": "文档创建时间查询优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_is_deleted",
                "columns": ["is_deleted"],
                "reason": "软删除过滤优化"
            },
            {
                "table": "documents",
                "name": "idx_doc_file_size",
                "columns": ["file_size"],
                "reason": "文档大小范围查询优化"
            },
            
            # 对话表索引
            {
                "table": "conversations",
                "name": "idx_conv_user_created",
                "columns": ["user_id", "created_at"],
                "reason": "用户对话历史查询优化"
            },
            {
                "table": "conversations",
                "name": "idx_conv_kb_created",
                "columns": ["knowledge_base_id", "created_at"],
                "reason": "知识库对话查询优化"
            },
            {
                "table": "conversations",
                "name": "idx_conv_updated_at",
                "columns": ["updated_at"],
                "reason": "对话活跃度查询优化"
            },
            {
                "table": "conversations",
                "name": "idx_conv_status",
                "columns": ["status"],
                "reason": "对话状态过滤优化"
            },
            
            # 消息表索引
            {
                "table": "messages",
                "name": "idx_msg_conversation_created",
                "columns": ["conversation_id", "created_at"],
                "reason": "对话消息查询优化"
            },
            {
                "table": "messages",
                "name": "idx_msg_user_created",
                "columns": ["user_id", "created_at"],
                "reason": "用户消息历史查询优化"
            },
            {
                "table": "messages",
                "name": "idx_msg_type",
                "columns": ["message_type"],
                "reason": "消息类型过滤优化"
            },
            
            # RBAC相关表索引
            {
                "table": "user_roles",
                "name": "idx_ur_user_status",
                "columns": ["user_id", "status"],
                "reason": "用户角色查询优化"
            },
            {
                "table": "user_roles",
                "name": "idx_ur_role_status",
                "columns": ["role_id", "status"],
                "reason": "角色用户查询优化"
            },
            {
                "table": "user_roles",
                "name": "idx_ur_expires_at",
                "columns": ["expires_at"],
                "reason": "角色过期查询优化"
            },
            {
                "table": "role_permissions",
                "name": "idx_rp_role_status",
                "columns": ["role_id", "status"],
                "reason": "角色权限查询优化"
            },
            {
                "table": "role_permissions",
                "name": "idx_rp_permission_status",
                "columns": ["permission_id", "status"],
                "reason": "权限角色查询优化"
            },
            {
                "table": "user_permissions",
                "name": "idx_up_user_status",
                "columns": ["user_id", "status"],
                "reason": "用户直接权限查询优化"
            },
            {
                "table": "user_permissions",
                "name": "idx_up_permission_type",
                "columns": ["permission_type"],
                "reason": "权限类型过滤优化"
            },
            
            # 部门表索引
            {
                "table": "departments",
                "name": "idx_dept_parent_status",
                "columns": ["parent_id", "status"],
                "reason": "部门层级查询优化"
            },
            {
                "table": "departments",
                "name": "idx_dept_code",
                "columns": ["code"],
                "unique": True,
                "reason": "部门代码唯一性和查询优化"
            },
            
            # 文档块表索引（如果存在）
            {
                "table": "document_chunks",
                "name": "idx_chunk_doc_id",
                "columns": ["document_id"],
                "reason": "文档块查询优化"
            },
            {
                "table": "document_chunks",
                "name": "idx_chunk_vector_id",
                "columns": ["vector_id"],
                "reason": "向量检索优化"
            },
        ]
    
    async def check_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """检查表的现有索引"""
        try:
            conn = Tortoise.get_connection("default")
            
            # 查询表的索引信息
            sql = f"""
                SELECT 
                    INDEX_NAME,
                    COLUMN_NAME,
                    NON_UNIQUE,
                    SEQ_IN_INDEX,
                    CARDINALITY
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}'
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            
            result = await conn.execute_query(sql)
            
            # 解析索引信息
            indexes = {}
            if result[1]:
                for row in result[1]:
                    if len(row) >= 5:
                        index_name = row[0]
                        column_name = row[1]
                        non_unique = row[2]
                        seq_in_index = row[3]
                        cardinality = row[4]
                        
                        if index_name not in indexes:
                            indexes[index_name] = {
                                "name": index_name,
                                "columns": [],
                                "unique": non_unique == 0,
                                "cardinality": cardinality
                            }
                        
                        indexes[index_name]["columns"].append(column_name)
            
            return list(indexes.values())
            
        except Exception as e:
            logger.error(f"检查表 {table_name} 索引失败: {e}")
            return []
    
    async def create_index(self, index_def: Dict[str, Any]) -> bool:
        """创建索引"""
        try:
            conn = Tortoise.get_connection("default")
            
            # 构建CREATE INDEX语句
            unique_clause = "UNIQUE " if index_def.get("unique", False) else ""
            columns_clause = ", ".join(index_def["columns"])
            
            sql = f"""
                CREATE {unique_clause}INDEX {index_def['name']} 
                ON {index_def['table']} ({columns_clause})
            """
            
            await conn.execute_query(sql)
            logger.info(f"成功创建索引: {index_def['name']} on {index_def['table']}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {index_def['name']} - {e}")
            return False
    
    async def drop_index(self, table_name: str, index_name: str) -> bool:
        """删除索引"""
        try:
            conn = Tortoise.get_connection("default")
            
            sql = f"DROP INDEX {index_name} ON {table_name}"
            await conn.execute_query(sql)
            
            logger.info(f"成功删除索引: {index_name} on {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除索引失败: {index_name} - {e}")
            return False
    
    async def analyze_and_create_indexes(self, dry_run: bool = True) -> Dict[str, Any]:
        """分析并创建推荐的索引"""
        results = {
            "analyzed_tables": [],
            "recommended_indexes": [],
            "created_indexes": [],
            "skipped_indexes": [],
            "errors": []
        }
        
        # 按表分组索引定义
        indexes_by_table = {}
        for index_def in self.index_definitions:
            table = index_def["table"]
            if table not in indexes_by_table:
                indexes_by_table[table] = []
            indexes_by_table[table].append(index_def)
        
        # 分析每个表
        for table_name, table_indexes in indexes_by_table.items():
            try:
                # 检查现有索引
                existing_indexes = await self.check_existing_indexes(table_name)
                existing_index_names = {idx["name"] for idx in existing_indexes}
                
                results["analyzed_tables"].append({
                    "table": table_name,
                    "existing_indexes": len(existing_indexes),
                    "existing_index_names": list(existing_index_names)
                })
                
                # 检查推荐的索引
                for index_def in table_indexes:
                    if index_def["name"] not in existing_index_names:
                        results["recommended_indexes"].append(index_def)
                        
                        if not dry_run:
                            # 创建索引
                            success = await self.create_index(index_def)
                            if success:
                                results["created_indexes"].append(index_def["name"])
                            else:
                                results["errors"].append(f"创建索引失败: {index_def['name']}")
                        else:
                            logger.info(f"推荐创建索引: {index_def['name']} on {table_name} - {index_def['reason']}")
                    else:
                        results["skipped_indexes"].append({
                            "name": index_def["name"],
                            "reason": "索引已存在"
                        })
                        
            except Exception as e:
                error_msg = f"分析表 {table_name} 失败: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    async def get_index_usage_stats(self, table_name: str) -> List[Dict[str, Any]]:
        """获取索引使用统计"""
        try:
            conn = Tortoise.get_connection("default")
            
            # 查询索引使用统计（MySQL 5.7+）
            sql = f"""
                SELECT 
                    s.INDEX_NAME,
                    s.TABLE_NAME,
                    s.CARDINALITY,
                    IFNULL(u.COUNT_READ, 0) as READ_COUNT,
                    IFNULL(u.COUNT_WRITE, 0) as WRITE_COUNT,
                    IFNULL(u.SUM_TIMER_READ, 0) as READ_TIME,
                    IFNULL(u.SUM_TIMER_WRITE, 0) as WRITE_TIME
                FROM information_schema.STATISTICS s
                LEFT JOIN performance_schema.table_io_waits_summary_by_index_usage u
                    ON s.TABLE_SCHEMA = u.OBJECT_SCHEMA 
                    AND s.TABLE_NAME = u.OBJECT_NAME 
                    AND s.INDEX_NAME = u.INDEX_NAME
                WHERE s.TABLE_SCHEMA = DATABASE() 
                AND s.TABLE_NAME = '{table_name}'
                GROUP BY s.INDEX_NAME
                ORDER BY IFNULL(u.COUNT_READ, 0) DESC
            """
            
            result = await conn.execute_query(sql)
            
            stats = []
            if result[1]:
                for row in result[1]:
                    if len(row) >= 7:
                        stats.append({
                            "index_name": row[0],
                            "table_name": row[1],
                            "cardinality": row[2],
                            "read_count": row[3],
                            "write_count": row[4],
                            "read_time": row[5],
                            "write_time": row[6],
                            "usage_ratio": row[3] / (row[3] + row[4]) if (row[3] + row[4]) > 0 else 0
                        })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取索引使用统计失败: {e}")
            return []


# 全局索引优化器实例
index_optimizer = DatabaseIndexOptimizer()


def get_index_optimizer() -> DatabaseIndexOptimizer:
    """获取索引优化器实例"""
    return index_optimizer
