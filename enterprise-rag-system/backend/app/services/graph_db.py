"""
Neo4j图数据库服务
"""

from typing import List, Dict, Any, Optional

from app.core.config import settings
from loguru import logger
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.exceptions import GraphDatabaseException


class Neo4jService:
    """Neo4j图数据库服务类"""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self.driver: Optional[AsyncDriver] = None
    
    async def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                database=self.database
            )
            
            # 验证连接
            await self.driver.verify_connectivity()
            
            logger.info(f"成功连接到Neo4j: {self.uri}")
            
            # 创建约束和索引
            await self._create_constraints_and_indexes()
            
        except Exception as e:
            logger.error(f"连接Neo4j失败: {e}")
            raise GraphDatabaseException(f"连接Neo4j失败: {e}")
    
    async def close(self):
        """关闭Neo4j连接"""
        try:
            if self.driver:
                await self.driver.close()
                logger.info("已关闭Neo4j连接")
        except Exception as e:
            logger.error(f"关闭Neo4j连接失败: {e}")
    
    def _ensure_connected(self):
        """确保已连接"""
        if not self.driver:
            raise GraphDatabaseException("未连接到Neo4j，请先调用connect()")
    
    async def _create_constraints_and_indexes(self):
        """创建约束和索引"""
        try:
            async with self.driver.session() as session:
                # 创建实体节点约束
                await session.run("""
                    CREATE CONSTRAINT entity_id IF NOT EXISTS 
                    FOR (e:Entity) REQUIRE e.id IS UNIQUE
                """)
                
                # 创建文档节点约束
                await session.run("""
                    CREATE CONSTRAINT document_id IF NOT EXISTS 
                    FOR (d:Document) REQUIRE d.id IS UNIQUE
                """)
                
                # 创建知识库节点约束
                await session.run("""
                    CREATE CONSTRAINT kb_id IF NOT EXISTS 
                    FOR (k:KnowledgeBase) REQUIRE k.id IS UNIQUE
                """)
                
                # 创建索引
                await session.run("""
                    CREATE INDEX entity_name_idx IF NOT EXISTS 
                    FOR (e:Entity) ON (e.name)
                """)
                
                await session.run("""
                    CREATE INDEX entity_type_idx IF NOT EXISTS 
                    FOR (e:Entity) ON (e.type)
                """)
                
                logger.info("Neo4j约束和索引创建完成")
                
        except Exception as e:
            logger.error(f"创建约束和索引失败: {e}")
            # 不抛出异常，因为约束可能已存在
    
    async def create_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None,
        knowledge_base_id: int = None
    ) -> bool:
        """创建实体节点"""
        try:
            self._ensure_connected()
            
            properties = properties or {}
            
            async with self.driver.session() as session:
                query = """
                MERGE (e:Entity {id: $entity_id})
                SET e.name = $name,
                    e.type = $entity_type,
                    e.knowledge_base_id = $knowledge_base_id,
                    e.created_at = datetime(),
                    e.updated_at = datetime()
                """
                
                # 添加自定义属性
                for key, value in properties.items():
                    if key not in ['id', 'name', 'type', 'knowledge_base_id']:
                        query += f", e.{key} = ${key}"
                
                params = {
                    "entity_id": entity_id,
                    "name": name,
                    "entity_type": entity_type,
                    "knowledge_base_id": knowledge_base_id,
                    **properties
                }
                
                await session.run(query, params)
                
                logger.debug(f"创建实体: {name} ({entity_type})")
                return True
                
        except Exception as e:
            logger.error(f"创建实体失败: {e}")
            raise GraphDatabaseException(f"创建实体失败: {e}")

    async def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None,
        knowledge_base_id: int = None
    ) -> bool:
        """创建实体关系"""
        try:
            if not self.driver:
                await self.connect()

            properties = properties or {}

            async with self.driver.session() as session:
                query = """
                MATCH (source:Entity {id: $source_id})
                MATCH (target:Entity {id: $target_id})
                MERGE (source)-[r:%s]->(target)
                SET r.created_at = datetime(),
                    r.updated_at = datetime()
                """ % relationship_type

                if knowledge_base_id:
                    query += ", r.knowledge_base_id = $knowledge_base_id"

                # 添加自定义属性
                for key, value in properties.items():
                    if key not in ['created_at', 'updated_at', 'knowledge_base_id']:
                        query += f", r.{key} = ${key}"

                params = {
                    "source_id": source_entity_id,
                    "target_id": target_entity_id,
                    "knowledge_base_id": knowledge_base_id,
                    **properties
                }

                await session.run(query, params)

                logger.debug(f"创建关系: {source_entity_id} -[{relationship_type}]-> {target_entity_id}")
                return True

        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise GraphDatabaseException(f"创建关系失败: {e}")

    async def find_entities(
        self,
        entity_type: str = None,
        name_pattern: str = None,
        knowledge_base_id: int = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找实体"""
        try:
            if not self.driver:
                await self.connect()

            conditions = []
            params = {"limit": limit}

            if entity_type:
                conditions.append("e.type = $entity_type")
                params["entity_type"] = entity_type

            if name_pattern:
                conditions.append("e.name CONTAINS $name_pattern")
                params["name_pattern"] = name_pattern

            if knowledge_base_id:
                conditions.append("e.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id

            where_clause = " AND ".join(conditions) if conditions else "true"

            query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN e
            LIMIT $limit
            """

            async with self.driver.session() as session:
                result = await session.run(query, params)
                entities = []

                async for record in result:
                    entity_data = dict(record["e"])
                    entities.append(entity_data)

                logger.debug(f"找到 {len(entities)} 个实体")
                return entities

        except Exception as e:
            logger.error(f"查找实体失败: {e}")
            raise GraphDatabaseException(f"查找实体失败: {e}")

    async def find_relationships(
        self,
        source_entity_id: str = None,
        target_entity_id: str = None,
        relationship_type: str = None,
        knowledge_base_id: int = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找关系"""
        try:
            if not self.driver:
                await self.connect()

            conditions = []
            params = {"limit": limit}

            match_clause = "MATCH (source:Entity)-[r]->(target:Entity)"

            if source_entity_id:
                conditions.append("source.id = $source_id")
                params["source_id"] = source_entity_id

            if target_entity_id:
                conditions.append("target.id = $target_id")
                params["target_id"] = target_entity_id

            if relationship_type:
                match_clause = f"MATCH (source:Entity)-[r:{relationship_type}]->(target:Entity)"

            if knowledge_base_id:
                conditions.append("r.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id

            where_clause = " AND ".join(conditions) if conditions else "true"

            query = f"""
            {match_clause}
            WHERE {where_clause}
            RETURN source, r, target
            LIMIT $limit
            """

            async with self.driver.session() as session:
                result = await session.run(query, params)
                relationships = []

                async for record in result:
                    rel_data = {
                        "source": dict(record["source"]),
                        "relationship": dict(record["r"]),
                        "target": dict(record["target"]),
                        "type": record["r"].type
                    }
                    relationships.append(rel_data)

                logger.debug(f"找到 {len(relationships)} 个关系")
                return relationships

        except Exception as e:
            logger.error(f"查找关系失败: {e}")
            raise GraphDatabaseException(f"查找关系失败: {e}")

    async def get_entity_neighbors(
        self,
        entity_id: str,
        relationship_types: List[str] = None,
        direction: str = "both",  # "in", "out", "both"
        max_depth: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取实体的邻居节点"""
        try:
            if not self.driver:
                await self.connect()

            # 构建关系模式
            if relationship_types:
                rel_pattern = "|".join(relationship_types)
                rel_pattern = f":{rel_pattern}"
            else:
                rel_pattern = ""

            # 构建方向模式
            if direction == "out":
                pattern = f"(entity)-[r{rel_pattern}*1..{max_depth}]->(neighbor)"
            elif direction == "in":
                pattern = f"(entity)<-[r{rel_pattern}*1..{max_depth}]-(neighbor)"
            else:  # both
                pattern = f"(entity)-[r{rel_pattern}*1..{max_depth}]-(neighbor)"

            query = f"""
            MATCH (entity:Entity {{id: $entity_id}})
            MATCH {pattern}
            RETURN DISTINCT neighbor, r
            LIMIT $limit
            """

            params = {
                "entity_id": entity_id,
                "limit": limit
            }

            async with self.driver.session() as session:
                result = await session.run(query, params)
                neighbors = []

                async for record in result:
                    neighbor_data = {
                        "entity": dict(record["neighbor"]),
                        "relationships": [dict(rel) for rel in record["r"]]
                    }
                    neighbors.append(neighbor_data)

                return {
                    "entity_id": entity_id,
                    "neighbors": neighbors,
                    "count": len(neighbors)
                }

        except Exception as e:
            logger.error(f"获取邻居节点失败: {e}")
            raise GraphDatabaseException(f"获取邻居节点失败: {e}")

    async def find_shortest_path(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_types: List[str] = None,
        max_length: int = 5
    ) -> Dict[str, Any]:
        """查找两个实体之间的最短路径"""
        try:
            if not self.driver:
                await self.connect()

            # 构建关系模式
            if relationship_types:
                rel_pattern = "|".join(relationship_types)
                rel_pattern = f":{rel_pattern}"
            else:
                rel_pattern = ""

            query = f"""
            MATCH (source:Entity {{id: $source_id}})
            MATCH (target:Entity {{id: $target_id}})
            MATCH path = shortestPath((source)-[r{rel_pattern}*1..{max_length}]-(target))
            RETURN path, length(path) as path_length
            """

            params = {
                "source_id": source_entity_id,
                "target_id": target_entity_id
            }

            async with self.driver.session() as session:
                result = await session.run(query, params)
                record = await result.single()

                if record:
                    path = record["path"]
                    path_length = record["path_length"]

                    # 解析路径
                    nodes = []
                    relationships = []

                    for i, node in enumerate(path.nodes):
                        nodes.append(dict(node))

                    for rel in path.relationships:
                        relationships.append({
                            "type": rel.type,
                            "properties": dict(rel)
                        })

                    return {
                        "source_id": source_entity_id,
                        "target_id": target_entity_id,
                        "path_found": True,
                        "path_length": path_length,
                        "nodes": nodes,
                        "relationships": relationships
                    }
                else:
                    return {
                        "source_id": source_entity_id,
                        "target_id": target_entity_id,
                        "path_found": False,
                        "path_length": -1,
                        "nodes": [],
                        "relationships": []
                    }

        except Exception as e:
            logger.error(f"查找最短路径失败: {e}")
            raise GraphDatabaseException(f"查找最短路径失败: {e}")

    async def get_subgraph(
        self,
        entity_ids: List[str],
        include_relationships: bool = True,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """获取指定实体的子图"""
        try:
            if not self.driver:
                await self.connect()

            if include_relationships:
                query = f"""
                MATCH (entity:Entity)
                WHERE entity.id IN $entity_ids
                OPTIONAL MATCH (entity)-[r*1..{max_depth}]-(connected)
                RETURN DISTINCT entity, r, connected
                """
            else:
                query = """
                MATCH (entity:Entity)
                WHERE entity.id IN $entity_ids
                RETURN entity
                """

            params = {"entity_ids": entity_ids}

            async with self.driver.session() as session:
                result = await session.run(query, params)

                nodes = {}
                relationships = []

                async for record in result:
                    # 添加主要实体
                    entity = dict(record["entity"])
                    nodes[entity["id"]] = entity

                    if include_relationships and record["connected"]:
                        # 添加连接的实体
                        connected = dict(record["connected"])
                        nodes[connected["id"]] = connected

                        # 添加关系
                        if record["r"]:
                            for rel in record["r"]:
                                rel_data = {
                                    "type": rel.type,
                                    "properties": dict(rel),
                                    "start_node": rel.start_node.element_id,
                                    "end_node": rel.end_node.element_id
                                }
                                relationships.append(rel_data)

                return {
                    "nodes": list(nodes.values()),
                    "relationships": relationships,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships)
                }

        except Exception as e:
            logger.error(f"获取子图失败: {e}")
            raise GraphDatabaseException(f"获取子图失败: {e}")

    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体及其所有关系"""
        try:
            if not self.driver:
                await self.connect()

            async with self.driver.session() as session:
                query = """
                MATCH (entity:Entity {id: $entity_id})
                DETACH DELETE entity
                """

                result = await session.run(query, {"entity_id": entity_id})
                summary = await result.consume()

                deleted_count = summary.counters.nodes_deleted
                logger.info(f"删除实体: {entity_id}, 删除节点数: {deleted_count}")

                return deleted_count > 0

        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            raise GraphDatabaseException(f"删除实体失败: {e}")

    async def delete_knowledge_base_data(self, knowledge_base_id: int) -> Dict[str, int]:
        """删除知识库的所有图数据"""
        try:
            if not self.driver:
                await self.connect()

            async with self.driver.session() as session:
                # 删除实体和关系
                query = """
                MATCH (entity:Entity {knowledge_base_id: $knowledge_base_id})
                DETACH DELETE entity
                """

                result = await session.run(query, {"knowledge_base_id": knowledge_base_id})
                summary = await result.consume()

                deleted_nodes = summary.counters.nodes_deleted
                deleted_relationships = summary.counters.relationships_deleted

                logger.info(f"删除知识库 {knowledge_base_id} 的图数据: 节点 {deleted_nodes}, 关系 {deleted_relationships}")

                return {
                    "deleted_nodes": deleted_nodes,
                    "deleted_relationships": deleted_relationships
                }

        except Exception as e:
            logger.error(f"删除知识库图数据失败: {e}")
            raise GraphDatabaseException(f"删除知识库图数据失败: {e}")
    
    async def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """创建关系"""
        try:
            self._ensure_connected()
            
            properties = properties or {}
            
            async with self.driver.session() as session:
                query = """
                MATCH (source:Entity {id: $source_id})
                MATCH (target:Entity {id: $target_id})
                MERGE (source)-[r:%s]->(target)
                SET r.created_at = datetime(),
                    r.updated_at = datetime()
                """ % relationship_type
                
                # 添加自定义属性
                for key, value in properties.items():
                    query += f", r.{key} = ${key}"
                
                params = {
                    "source_id": source_entity_id,
                    "target_id": target_entity_id,
                    **properties
                }
                
                await session.run(query, params)
                
                logger.debug(f"创建关系: {source_entity_id} -[{relationship_type}]-> {target_entity_id}")
                return True
                
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise GraphDatabaseException(f"创建关系失败: {e}")
    
    async def find_entities(
        self,
        name: str = None,
        entity_type: str = None,
        knowledge_base_id: int = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找实体"""
        try:
            self._ensure_connected()
            
            # 构建查询条件
            conditions = []
            params = {"limit": limit}
            
            if name:
                conditions.append("e.name CONTAINS $name")
                params["name"] = name
            
            if entity_type:
                conditions.append("e.type = $entity_type")
                params["entity_type"] = entity_type
            
            if knowledge_base_id is not None:
                conditions.append("e.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN e
            LIMIT $limit
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, params)
                records = await result.data()
                
                entities = []
                for record in records:
                    entity_data = dict(record["e"])
                    entities.append(entity_data)
                
                logger.debug(f"找到 {len(entities)} 个实体")
                return entities
                
        except Exception as e:
            logger.error(f"查找实体失败: {e}")
            raise GraphDatabaseException(f"查找实体失败: {e}")
    
    async def find_relationships(
        self,
        source_entity_id: str = None,
        target_entity_id: str = None,
        relationship_type: str = None,
        knowledge_base_id: int = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找关系"""
        try:
            self._ensure_connected()
            
            # 构建查询
            match_clause = "MATCH (source:Entity)-[r]->(target:Entity)"
            conditions = []
            params = {"limit": limit}
            
            if source_entity_id:
                conditions.append("source.id = $source_id")
                params["source_id"] = source_entity_id
            
            if target_entity_id:
                conditions.append("target.id = $target_id")
                params["target_id"] = target_entity_id
            
            if relationship_type:
                match_clause = f"MATCH (source:Entity)-[r:{relationship_type}]->(target:Entity)"
            
            if knowledge_base_id is not None:
                conditions.append("source.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            query = f"""
            {match_clause}
            WHERE {where_clause}
            RETURN source, r, target, type(r) as relationship_type
            LIMIT $limit
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, params)
                records = await result.data()
                
                relationships = []
                for record in records:
                    rel_data = {
                        "source": dict(record["source"]),
                        "target": dict(record["target"]),
                        "relationship": dict(record["r"]),
                        "relationship_type": record["relationship_type"]
                    }
                    relationships.append(rel_data)
                
                logger.debug(f"找到 {len(relationships)} 个关系")
                return relationships
                
        except Exception as e:
            logger.error(f"查找关系失败: {e}")
            raise GraphDatabaseException(f"查找关系失败: {e}")
    
    async def get_entity_neighbors(
        self,
        entity_id: str,
        max_depth: int = 2,
        relationship_types: List[str] = None
    ) -> Dict[str, Any]:
        """获取实体的邻居节点"""
        try:
            self._ensure_connected()
            
            # 构建关系类型过滤
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""
            MATCH path = (start:Entity {{id: $entity_id}})-[r{rel_filter}*1..{max_depth}]-(neighbor:Entity)
            RETURN start, relationships(path) as rels, neighbor, length(path) as depth
            ORDER BY depth
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, {"entity_id": entity_id})
                records = await result.data()
                
                # 组织结果
                start_entity = None
                neighbors = []
                relationships = []
                
                for record in records:
                    if start_entity is None:
                        start_entity = dict(record["start"])
                    
                    neighbor = dict(record["neighbor"])
                    depth = record["depth"]
                    
                    neighbor["depth"] = depth
                    neighbors.append(neighbor)
                    
                    # 处理路径上的关系
                    for rel in record["rels"]:
                        rel_data = {
                            "type": rel.type,
                            "properties": dict(rel),
                            "start_node": rel.start_node.element_id,
                            "end_node": rel.end_node.element_id
                        }
                        relationships.append(rel_data)
                
                result_data = {
                    "entity": start_entity,
                    "neighbors": neighbors,
                    "relationships": relationships,
                    "total_neighbors": len(neighbors)
                }
                
                logger.debug(f"实体 {entity_id} 有 {len(neighbors)} 个邻居")
                return result_data
                
        except Exception as e:
            logger.error(f"获取实体邻居失败: {e}")
            raise GraphDatabaseException(f"获取实体邻居失败: {e}")
    
    async def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行自定义Cypher查询"""
        try:
            self._ensure_connected()
            
            parameters = parameters or {}
            
            async with self.driver.session() as session:
                result = await session.run(query, parameters)
                records = await result.data()
                
                logger.debug(f"Cypher查询返回 {len(records)} 条记录")
                return records
                
        except Exception as e:
            logger.error(f"执行Cypher查询失败: {e}")
            raise GraphDatabaseException(f"执行Cypher查询失败: {e}")
    
    async def delete_entities(
        self,
        entity_ids: List[str] = None,
        knowledge_base_id: int = None
    ) -> int:
        """删除实体"""
        try:
            self._ensure_connected()
            
            conditions = []
            params = {}
            
            if entity_ids:
                conditions.append("e.id IN $entity_ids")
                params["entity_ids"] = entity_ids
            
            if knowledge_base_id is not None:
                conditions.append("e.knowledge_base_id = $knowledge_base_id")
                params["knowledge_base_id"] = knowledge_base_id
            
            if not conditions:
                raise ValueError("必须指定删除条件")
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            DETACH DELETE e
            RETURN count(e) as deleted_count
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, params)
                record = await result.single()
                deleted_count = record["deleted_count"]
                
                logger.info(f"删除了 {deleted_count} 个实体")
                return deleted_count
                
        except Exception as e:
            logger.error(f"删除实体失败: {e}")
            raise GraphDatabaseException(f"删除实体失败: {e}")
    
    async def get_graph_stats(self, knowledge_base_id: int = None) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            self._ensure_connected()
            
            # 构建过滤条件
            where_clause = ""
            params = {}
            
            if knowledge_base_id is not None:
                where_clause = "WHERE e.knowledge_base_id = $knowledge_base_id"
                params["knowledge_base_id"] = knowledge_base_id
            
            query = f"""
            MATCH (e:Entity) {where_clause}
            OPTIONAL MATCH (e)-[r]->()
            RETURN 
                count(DISTINCT e) as entity_count,
                count(DISTINCT r) as relationship_count,
                collect(DISTINCT e.type) as entity_types,
                collect(DISTINCT type(r)) as relationship_types
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, params)
                record = await result.single()
                
                stats = {
                    "entity_count": record["entity_count"],
                    "relationship_count": record["relationship_count"],
                    "entity_types": [t for t in record["entity_types"] if t],
                    "relationship_types": [t for t in record["relationship_types"] if t]
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"获取图谱统计信息失败: {e}")
            raise GraphDatabaseException(f"获取图谱统计信息失败: {e}")


# 全局Neo4j服务实例
neo4j_service = Neo4jService()
graph_service = neo4j_service  # 别名，保持向后兼容
