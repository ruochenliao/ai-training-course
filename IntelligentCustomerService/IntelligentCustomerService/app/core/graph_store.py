"""
Neo4j图数据库存储管理器
提供知识图谱的构建、查询和管理功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class GraphStoreException(Exception):
    """图数据库异常"""
    pass


class Neo4jGraphStore:
    """
    Neo4j图数据库存储管理器
    
    主要功能：
    - 知识图谱构建和管理
    - 实体和关系的CRUD操作
    - 图算法查询和分析
    - 知识推理和路径查找
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "neo4j_password",
        database: str = "neo4j"
    ):
        """
        初始化Neo4j图存储
        
        Args:
            uri: Neo4j连接URI
            username: 用户名
            password: 密码
            database: 数据库名
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._connected = False
        
        logger.info(f"初始化Neo4j图存储: {uri}")
    
    async def connect(self):
        """连接到Neo4j数据库"""
        try:
            if self._connected and self.driver:
                return
            
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # 验证连接
            await self.driver.verify_connectivity()
            
            # 创建约束和索引
            await self._create_constraints_and_indexes()
            
            self._connected = True
            logger.info("✅ Neo4j连接成功")
            
        except AuthError as e:
            logger.error(f"❌ Neo4j认证失败: {str(e)}")
            raise GraphStoreException(f"Neo4j认证失败: {str(e)}")
        except ServiceUnavailable as e:
            logger.error(f"❌ Neo4j服务不可用: {str(e)}")
            raise GraphStoreException(f"Neo4j服务不可用: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {str(e)}")
            raise GraphStoreException(f"Neo4j连接失败: {str(e)}")
    
    async def disconnect(self):
        """断开连接"""
        if self.driver:
            await self.driver.close()
            self._connected = False
            logger.info("Neo4j连接已断开")
    
    async def _create_constraints_and_indexes(self):
        """创建约束和索引"""
        try:
            async with self.driver.session(database=self.database) as session:
                # 创建实体约束
                constraints = [
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                    "CREATE CONSTRAINT knowledge_base_id IF NOT EXISTS FOR (kb:KnowledgeBase) REQUIRE kb.id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        await session.run(constraint)
                    except Exception as e:
                        # 约束可能已存在，忽略错误
                        logger.debug(f"约束创建跳过: {str(e)}")
                
                # 创建索引
                indexes = [
                    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                    "CREATE INDEX entity_knowledge_base IF NOT EXISTS FOR (e:Entity) ON (e.knowledge_base_id)",
                    "CREATE INDEX document_title IF NOT EXISTS FOR (d:Document) ON (d.title)",
                    "CREATE INDEX relation_type IF NOT EXISTS FOR ()-[r]-() ON (r.type)"
                ]
                
                for index in indexes:
                    try:
                        await session.run(index)
                    except Exception as e:
                        # 索引可能已存在，忽略错误
                        logger.debug(f"索引创建跳过: {str(e)}")
                
                logger.info("✅ Neo4j约束和索引创建完成")
                
        except Exception as e:
            logger.error(f"❌ 创建约束和索引失败: {str(e)}")
            # 不抛出异常，允许继续使用
    
    async def create_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None,
        knowledge_base_id: Optional[str] = None
    ) -> bool:
        """
        创建实体节点
        
        Args:
            entity_id: 实体ID
            name: 实体名称
            entity_type: 实体类型
            properties: 实体属性
            knowledge_base_id: 知识库ID
            
        Returns:
            创建是否成功
        """
        try:
            await self._ensure_connected()
            
            properties = properties or {}
            properties.update({
                "id": entity_id,
                "name": name,
                "type": entity_type,
                "created_at": datetime.now().isoformat(),
                "knowledge_base_id": knowledge_base_id
            })
            
            query = """
            MERGE (e:Entity {id: $entity_id})
            SET e += $properties
            RETURN e
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {
                    "entity_id": entity_id,
                    "properties": properties
                })
                
                record = await result.single()
                if record:
                    logger.debug(f"实体创建成功: {entity_id}")
                    return True
                else:
                    logger.warning(f"实体创建失败: {entity_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"创建实体失败: {str(e)}")
            raise GraphStoreException(f"创建实体失败: {str(e)}")
    
    async def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        创建关系
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            relationship_type: 关系类型
            properties: 关系属性
            
        Returns:
            创建是否成功
        """
        try:
            await self._ensure_connected()
            
            properties = properties or {}
            properties.update({
                "type": relationship_type,
                "created_at": datetime.now().isoformat()
            })
            
            query = f"""
            MATCH (source:Entity {{id: $source_id}})
            MATCH (target:Entity {{id: $target_id}})
            MERGE (source)-[r:{relationship_type}]->(target)
            SET r += $properties
            RETURN r
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {
                    "source_id": source_entity_id,
                    "target_id": target_entity_id,
                    "properties": properties
                })
                
                record = await result.single()
                if record:
                    logger.debug(f"关系创建成功: {source_entity_id} -> {target_entity_id}")
                    return True
                else:
                    logger.warning(f"关系创建失败: {source_entity_id} -> {target_entity_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"创建关系失败: {str(e)}")
            raise GraphStoreException(f"创建关系失败: {str(e)}")
    
    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查找实体
        
        Args:
            entity_type: 实体类型过滤
            name_pattern: 名称模式匹配
            knowledge_base_id: 知识库ID过滤
            limit: 结果限制
            
        Returns:
            实体列表
        """
        try:
            await self._ensure_connected()
            
            # 构建查询条件
            where_conditions = []
            params = {"limit": limit}
            
            if entity_type:
                where_conditions.append("e.type = $entity_type")
                params["entity_type"] = entity_type
            
            if name_pattern:
                where_conditions.append("e.name CONTAINS $name_pattern")
                params["name_pattern"] = name_pattern
            
            if knowledge_base_id:
                where_conditions.append("e.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "true"
            
            query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN e
            LIMIT $limit
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, params)
                
                entities = []
                async for record in result:
                    entity_data = dict(record["e"])
                    entities.append(entity_data)
                
                logger.debug(f"找到 {len(entities)} 个实体")
                return entities
                
        except Exception as e:
            logger.error(f"查找实体失败: {str(e)}")
            raise GraphStoreException(f"查找实体失败: {str(e)}")
    
    async def find_related_entities(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查找相关实体
        
        Args:
            entity_id: 中心实体ID
            relationship_types: 关系类型过滤
            max_depth: 最大深度
            limit: 结果限制
            
        Returns:
            相关实体列表
        """
        try:
            await self._ensure_connected()
            
            # 构建关系类型过滤
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""
            MATCH (start:Entity {{id: $entity_id}})
            MATCH (start)-[r{rel_filter}*1..{max_depth}]-(related:Entity)
            WHERE related.id <> $entity_id
            RETURN DISTINCT related, length(r) as distance
            ORDER BY distance, related.name
            LIMIT $limit
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {
                    "entity_id": entity_id,
                    "limit": limit
                })
                
                related_entities = []
                async for record in result:
                    entity_data = dict(record["related"])
                    entity_data["distance"] = record["distance"]
                    related_entities.append(entity_data)
                
                logger.debug(f"找到 {len(related_entities)} 个相关实体")
                return related_entities
                
        except Exception as e:
            logger.error(f"查找相关实体失败: {str(e)}")
            raise GraphStoreException(f"查找相关实体失败: {str(e)}")
    
    async def find_shortest_path(
        self,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        查找两个实体间的最短路径

        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            max_depth: 最大搜索深度

        Returns:
            路径信息
        """
        try:
            await self._ensure_connected()

            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            MATCH path = shortestPath((source)-[*1..%d]-(target))
            RETURN path, length(path) as path_length
            """ % max_depth

            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {
                    "source_id": source_entity_id,
                    "target_id": target_entity_id
                })

                record = await result.single()
                if record:
                    path = record["path"]
                    path_length = record["path_length"]

                    # 提取路径中的节点和关系
                    nodes = []
                    relationships = []

                    for node in path.nodes:
                        nodes.append(dict(node))

                    for rel in path.relationships:
                        relationships.append({
                            "type": rel.type,
                            "properties": dict(rel)
                        })

                    return {
                        "path_length": path_length,
                        "nodes": nodes,
                        "relationships": relationships
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"查找最短路径失败: {str(e)}")
            raise GraphStoreException(f"查找最短路径失败: {str(e)}")

    async def execute_cypher(
        self,
        query: str,
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行自定义Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果
        """
        try:
            await self._ensure_connected()

            parameters = parameters or {}

            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, parameters)

                records = []
                async for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # 处理Neo4j节点和关系对象
                        if hasattr(value, '__dict__'):
                            record_dict[key] = dict(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)

                logger.debug(f"Cypher查询返回 {len(records)} 条记录")
                return records

        except Exception as e:
            logger.error(f"执行Cypher查询失败: {str(e)}")
            raise GraphStoreException(f"执行Cypher查询失败: {str(e)}")

    async def get_graph_statistics(
        self,
        knowledge_base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取图谱统计信息

        Args:
            knowledge_base_id: 知识库ID过滤

        Returns:
            统计信息
        """
        try:
            await self._ensure_connected()

            # 构建过滤条件
            where_clause = ""
            params = {}

            if knowledge_base_id:
                where_clause = "WHERE e.knowledge_base_id = $knowledge_base_id"
                params["knowledge_base_id"] = knowledge_base_id

            query = f"""
            MATCH (e:Entity) {where_clause}
            OPTIONAL MATCH (e)-[r]-()
            RETURN
                count(DISTINCT e) as entity_count,
                count(DISTINCT r) as relationship_count,
                collect(DISTINCT e.type) as entity_types,
                collect(DISTINCT type(r)) as relationship_types
            """

            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, params)
                record = await result.single()

                if record:
                    return {
                        "entity_count": record["entity_count"],
                        "relationship_count": record["relationship_count"],
                        "entity_types": [t for t in record["entity_types"] if t],
                        "relationship_types": [t for t in record["relationship_types"] if t],
                        "knowledge_base_id": knowledge_base_id
                    }
                else:
                    return {
                        "entity_count": 0,
                        "relationship_count": 0,
                        "entity_types": [],
                        "relationship_types": [],
                        "knowledge_base_id": knowledge_base_id
                    }

        except Exception as e:
            logger.error(f"获取图谱统计失败: {str(e)}")
            raise GraphStoreException(f"获取图谱统计失败: {str(e)}")

    async def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体及其关系

        Args:
            entity_id: 实体ID

        Returns:
            删除是否成功
        """
        try:
            await self._ensure_connected()

            query = """
            MATCH (e:Entity {id: $entity_id})
            DETACH DELETE e
            RETURN count(e) as deleted_count
            """

            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {"entity_id": entity_id})
                record = await result.single()

                deleted_count = record["deleted_count"] if record else 0
                success = deleted_count > 0

                if success:
                    logger.debug(f"实体删除成功: {entity_id}")
                else:
                    logger.warning(f"实体删除失败或不存在: {entity_id}")

                return success

        except Exception as e:
            logger.error(f"删除实体失败: {str(e)}")
            raise GraphStoreException(f"删除实体失败: {str(e)}")

    async def _ensure_connected(self):
        """确保连接已建立"""
        if not self._connected:
            await self.connect()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            await self._ensure_connected()

            start_time = datetime.now()

            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                test_value = record["test"] if record else None

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            return {
                "status": "healthy",
                "response_time": response_time,
                "database": self.database,
                "test_result": test_value,
                "connected": self._connected
            }

        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": self._connected
            }


# 全局图存储实例
graph_store: Optional[Neo4jGraphStore] = None


def get_graph_store() -> Neo4jGraphStore:
    """获取图存储实例"""
    global graph_store
    
    if graph_store is None:
        # 从环境变量或配置文件获取连接信息
        import os
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j_password")
        database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        graph_store = Neo4jGraphStore(
            uri=uri,
            username=username,
            password=password,
            database=database
        )
    
    return graph_store


async def initialize_graph_store():
    """初始化图存储"""
    store = get_graph_store()
    await store.connect()
    return store
