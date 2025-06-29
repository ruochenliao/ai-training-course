"""
图数据库服务（Neo4j）
"""

import asyncio
from typing import List, Dict, Any, Optional

from loguru import logger
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core import GraphDatabaseException
from app.core import settings


class Neo4jService:
    """Neo4j图数据库服务类"""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self.driver: Optional[AsyncDriver] = None
        self._connected = False
    
    async def connect(self):
        """连接到Neo4j"""
        try:
            if self._connected:
                return
            
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # 测试连接
            async with self.driver.session(database=self.database) as session:
                await session.run("RETURN 1")
            
            self._connected = True
            logger.info(f"成功连接到Neo4j: {self.uri}")
            
        except Exception as e:
            logger.error(f"连接Neo4j失败: {e}")
            raise GraphDatabaseException(f"连接Neo4j失败: {e}")
    
    async def disconnect(self):
        """断开Neo4j连接"""
        try:
            if self.driver and self._connected:
                await self.driver.close()
                self._connected = False
                logger.info("已断开Neo4j连接")
        except Exception as e:
            logger.error(f"断开Neo4j连接失败: {e}")
    
    async def execute_query(
        self, 
        query: str, 
        parameters: Dict[str, Any] = None,
        knowledge_base_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        try:
            if not self._connected:
                await self.connect()
            
            # 添加知识库过滤条件
            if knowledge_base_ids:
                if "WHERE" in query.upper():
                    query += f" AND n.knowledge_base_id IN {knowledge_base_ids}"
                else:
                    query += f" WHERE n.knowledge_base_id IN {knowledge_base_ids}"
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                
                # 处理结果
                processed_records = []
                for record in records:
                    processed_record = {}
                    for key, value in record.items():
                        if hasattr(value, '_properties'):
                            # Neo4j节点或关系对象
                            processed_record[key] = dict(value._properties)
                            processed_record[key]['_id'] = value.id
                            processed_record[key]['_labels'] = list(value.labels) if hasattr(value, 'labels') else []
                        else:
                            processed_record[key] = value
                    processed_records.append(processed_record)
                
                return processed_records
                
        except Exception as e:
            logger.error(f"执行Cypher查询失败: {e}")
            raise GraphDatabaseException(f"执行Cypher查询失败: {e}")
    
    async def create_node(
        self, 
        label: str, 
        properties: Dict[str, Any],
        knowledge_base_id: int
    ) -> Dict[str, Any]:
        """创建节点"""
        try:
            properties['knowledge_base_id'] = knowledge_base_id
            
            # 构建Cypher查询
            props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
            
            result = await self.execute_query(query, properties)
            return result[0]['n'] if result else {}
            
        except Exception as e:
            logger.error(f"创建节点失败: {e}")
            raise GraphDatabaseException(f"创建节点失败: {e}")
    
    async def create_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """创建关系"""
        try:
            props = properties or {}
            props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""
            
            query = f"""
            MATCH (a), (b)
            WHERE id(a) = $start_id AND id(b) = $end_id
            CREATE (a)-[r:{relationship_type} {{{props_str}}}]->(b)
            RETURN r
            """
            
            params = {
                "start_id": start_node_id,
                "end_id": end_node_id,
                **props
            }
            
            result = await self.execute_query(query, params)
            return result[0]['r'] if result else {}
            
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise GraphDatabaseException(f"创建关系失败: {e}")
    
    async def find_nodes(
        self,
        label: str = None,
        properties: Dict[str, Any] = None,
        knowledge_base_ids: List[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找节点"""
        try:
            # 构建查询
            match_clause = f"MATCH (n{':' + label if label else ''})"
            
            where_conditions = []
            params = {}
            
            if properties:
                for key, value in properties.items():
                    where_conditions.append(f"n.{key} = ${key}")
                    params[key] = value
            
            if knowledge_base_ids:
                where_conditions.append(f"n.knowledge_base_id IN $kb_ids")
                params['kb_ids'] = knowledge_base_ids
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f"{match_clause}{where_clause} RETURN n LIMIT {limit}"
            
            result = await self.execute_query(query, params)
            return [record['n'] for record in result]
            
        except Exception as e:
            logger.error(f"查找节点失败: {e}")
            raise GraphDatabaseException(f"查找节点失败: {e}")
    
    async def find_relationships(
        self,
        start_node_id: int = None,
        end_node_id: int = None,
        relationship_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找关系"""
        try:
            # 构建查询
            if start_node_id and end_node_id:
                match_clause = "MATCH (a)-[r]->(b)"
                where_clause = f" WHERE id(a) = {start_node_id} AND id(b) = {end_node_id}"
            elif start_node_id:
                match_clause = "MATCH (a)-[r]->()"
                where_clause = f" WHERE id(a) = {start_node_id}"
            elif end_node_id:
                match_clause = "MATCH ()-[r]->(b)"
                where_clause = f" WHERE id(b) = {end_node_id}"
            else:
                match_clause = "MATCH ()-[r]->()"
                where_clause = ""
            
            if relationship_type:
                match_clause = match_clause.replace("[r]", f"[r:{relationship_type}]")
            
            query = f"{match_clause}{where_clause} RETURN r LIMIT {limit}"
            
            result = await self.execute_query(query)
            return [record['r'] for record in result]
            
        except Exception as e:
            logger.error(f"查找关系失败: {e}")
            raise GraphDatabaseException(f"查找关系失败: {e}")
    
    async def get_node_neighbors(
        self,
        node_id: int,
        relationship_types: List[str] = None,
        direction: str = "both",  # incoming, outgoing, both
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取节点的邻居"""
        try:
            # 构建关系模式
            if direction == "outgoing":
                rel_pattern = "-[r]->"
            elif direction == "incoming":
                rel_pattern = "<-[r]-"
            else:  # both
                rel_pattern = "-[r]-"
            
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_pattern = rel_pattern.replace("[r]", f"[r:{rel_types}]")
            
            query = f"""
            MATCH (n){rel_pattern}(neighbor)
            WHERE id(n) = $node_id
            RETURN neighbor, r
            LIMIT {limit}
            """
            
            result = await self.execute_query(query, {"node_id": node_id})
            
            neighbors = []
            for record in result:
                neighbors.append({
                    "node": record['neighbor'],
                    "relationship": record['r']
                })
            
            return neighbors
            
        except Exception as e:
            logger.error(f"获取节点邻居失败: {e}")
            raise GraphDatabaseException(f"获取节点邻居失败: {e}")
    
    async def delete_node(self, node_id: int) -> bool:
        """删除节点"""
        try:
            query = """
            MATCH (n)
            WHERE id(n) = $node_id
            DETACH DELETE n
            """
            
            await self.execute_query(query, {"node_id": node_id})
            return True
            
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            raise GraphDatabaseException(f"删除节点失败: {e}")
    
    async def delete_relationship(self, relationship_id: int) -> bool:
        """删除关系"""
        try:
            query = """
            MATCH ()-[r]->()
            WHERE id(r) = $rel_id
            DELETE r
            """
            
            await self.execute_query(query, {"rel_id": relationship_id})
            return True
            
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            raise GraphDatabaseException(f"删除关系失败: {e}")
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """获取图数据库统计信息"""
        try:
            queries = {
                "node_count": "MATCH (n) RETURN count(n) as count",
                "relationship_count": "MATCH ()-[r]->() RETURN count(r) as count",
                "label_counts": "MATCH (n) RETURN labels(n) as labels, count(n) as count",
                "relationship_type_counts": "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count"
            }
            
            stats = {}
            
            for stat_name, query in queries.items():
                result = await self.execute_query(query)
                if stat_name in ["node_count", "relationship_count"]:
                    stats[stat_name] = result[0]['count'] if result else 0
                else:
                    stats[stat_name] = result
            
            return stats
            
        except Exception as e:
            logger.error(f"获取图数据库统计信息失败: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._connected:
                await self.connect()
            
            start_time = asyncio.get_event_loop().time()
            result = await self.execute_query("RETURN 1 as test")
            end_time = asyncio.get_event_loop().time()
            
            return {
                "status": "healthy",
                "response_time": end_time - start_time,
                "database": self.database,
                "test_result": result[0]['test'] if result else None
            }
            
        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局Neo4j服务实例
neo4j_service = Neo4jService()
