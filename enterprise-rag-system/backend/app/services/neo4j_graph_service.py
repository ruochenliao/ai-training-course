"""
Neo4j 5.x 知识图谱服务 - 企业级RAG系统
严格按照技术栈要求：Neo4j 5.x 存储知识图谱数据，支持 Cypher 查询
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from loguru import logger
from neo4j import AsyncGraphDatabase, AsyncDriver


class Neo4jGraphService:
    """Neo4j 知识图谱服务"""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.driver: Optional[AsyncDriver] = None
        self._connected = False
        
        # 图谱配置
        self.max_hops = 3  # 最大跳数
        self.batch_size = 1000  # 批处理大小
        
        # 节点和关系类型
        self.node_types = {
            "Document": "文档节点",
            "Chunk": "分块节点", 
            "Entity": "实体节点",
            "Concept": "概念节点",
            "Person": "人物节点",
            "Organization": "组织节点",
            "Location": "地点节点",
            "Event": "事件节点"
        }
        
        self.relation_types = {
            "CONTAINS": "包含关系",
            "MENTIONS": "提及关系",
            "RELATES_TO": "相关关系",
            "PART_OF": "部分关系",
            "LOCATED_IN": "位于关系",
            "WORKS_FOR": "工作关系",
            "PARTICIPATES_IN": "参与关系",
            "SIMILAR_TO": "相似关系"
        }
    
    async def connect(self):
        """连接到Neo4j数据库"""
        if self._connected and self.driver:
            return
        
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # 验证连接
            await self.driver.verify_connectivity()
            self._connected = True
            
            logger.info(f"Neo4j连接成功: {self.uri}")
            
            # 创建索引和约束
            await self._create_indexes_and_constraints()
            
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开Neo4j连接"""
        try:
            if self.driver:
                await self.driver.close()
                self._connected = False
                logger.info("Neo4j连接已断开")
        except Exception as e:
            logger.error(f"断开Neo4j连接失败: {e}")
    
    async def _create_indexes_and_constraints(self):
        """创建索引和约束"""
        try:
            async with self.driver.session() as session:
                # 创建唯一约束
                constraints = [
                    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        await session.run(constraint)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"创建约束失败: {constraint}, 错误: {e}")
                
                # 创建索引
                indexes = [
                    "CREATE INDEX document_kb_id IF NOT EXISTS FOR (d:Document) ON (d.knowledge_base_id)",
                    "CREATE INDEX chunk_document_id IF NOT EXISTS FOR (c:Chunk) ON (c.document_id)",
                    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)"
                ]
                
                for index in indexes:
                    try:
                        await session.run(index)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"创建索引失败: {index}, 错误: {e}")
                
                logger.info("Neo4j索引和约束创建完成")
                
        except Exception as e:
            logger.error(f"创建索引和约束失败: {e}")
    
    async def create_document_node(
        self, 
        document_id: int, 
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> bool:
        """创建文档节点"""
        try:
            await self.connect()
            
            query = """
            MERGE (d:Document {id: $document_id})
            SET d.knowledge_base_id = $knowledge_base_id,
                d.filename = $filename,
                d.file_type = $file_type,
                d.file_size = $file_size,
                d.total_chunks = $total_chunks,
                d.created_at = $created_at,
                d.updated_at = datetime()
            RETURN d
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "document_id": document_id,
                    "knowledge_base_id": knowledge_base_id,
                    "filename": metadata.get("filename", ""),
                    "file_type": metadata.get("file_type", ""),
                    "file_size": metadata.get("file_size", 0),
                    "total_chunks": metadata.get("total_chunks", 0),
                    "created_at": metadata.get("created_at", datetime.now().isoformat())
                })
                
                record = await result.single()
                if record:
                    logger.info(f"文档节点创建成功: {document_id}")
                    return True
                
        except Exception as e:
            logger.error(f"创建文档节点失败: {e}")
            return False
    
    async def create_chunk_node(
        self,
        chunk_id: str,
        document_id: int,
        chunk_index: int,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """创建分块节点"""
        try:
            await self.connect()
            
            query = """
            MERGE (c:Chunk {id: $chunk_id})
            SET c.document_id = $document_id,
                c.chunk_index = $chunk_index,
                c.content = $content,
                c.content_hash = $content_hash,
                c.chunk_type = $chunk_type,
                c.char_count = $char_count,
                c.created_at = $created_at,
                c.updated_at = datetime()
            WITH c
            MATCH (d:Document {id: $document_id})
            MERGE (d)-[:CONTAINS]->(c)
            RETURN c
            """
            
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "content": content[:1000],  # 限制内容长度
                    "content_hash": metadata.get("content_hash", ""),
                    "chunk_type": metadata.get("chunk_type", "text"),
                    "char_count": len(content),
                    "created_at": metadata.get("created_at", datetime.now().isoformat())
                })
                
                record = await result.single()
                if record:
                    logger.debug(f"分块节点创建成功: {chunk_id}")
                    return True
                
        except Exception as e:
            logger.error(f"创建分块节点失败: {e}")
            return False
    
    async def create_entity_nodes(
        self,
        chunk_id: str,
        entities: List[Dict[str, Any]]
    ) -> List[str]:
        """批量创建实体节点"""
        try:
            await self.connect()
            created_entities = []
            
            # 批量处理实体
            for i in range(0, len(entities), self.batch_size):
                batch_entities = entities[i:i + self.batch_size]
                
                async with self.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for entity in batch_entities:
                            entity_id = await self._create_single_entity(
                                tx, chunk_id, entity
                            )
                            if entity_id:
                                created_entities.append(entity_id)
            
            logger.info(f"批量创建实体节点完成: {len(created_entities)}")
            return created_entities
            
        except Exception as e:
            logger.error(f"批量创建实体节点失败: {e}")
            return []
    
    async def _create_single_entity(
        self,
        tx,
        chunk_id: str,
        entity: Dict[str, Any]
    ) -> Optional[str]:
        """创建单个实体节点"""
        try:
            entity_name = entity.get("name", "").strip()
            entity_type = entity.get("type", "Entity")
            entity_label = entity.get("label", entity_name)
            confidence = entity.get("confidence", 1.0)
            
            if not entity_name:
                return None
            
            # 创建实体节点
            query = f"""
            MERGE (e:{entity_type} {{name: $name}})
            SET e.label = $label,
                e.type = $type,
                e.confidence = $confidence,
                e.updated_at = datetime()
            WITH e
            MATCH (c:Chunk {{id: $chunk_id}})
            MERGE (c)-[:MENTIONS {{confidence: $confidence}}]->(e)
            RETURN e.name as entity_id
            """
            
            result = await tx.run(query, {
                "name": entity_name,
                "label": entity_label,
                "type": entity_type,
                "confidence": confidence,
                "chunk_id": chunk_id
            })
            
            record = await result.single()
            return record["entity_id"] if record else None
            
        except Exception as e:
            logger.error(f"创建单个实体节点失败: {e}")
            return None
    
    async def create_relations(
        self,
        relations: List[Dict[str, Any]]
    ) -> int:
        """批量创建关系"""
        try:
            await self.connect()
            created_count = 0
            
            # 批量处理关系
            for i in range(0, len(relations), self.batch_size):
                batch_relations = relations[i:i + self.batch_size]
                
                async with self.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for relation in batch_relations:
                            success = await self._create_single_relation(tx, relation)
                            if success:
                                created_count += 1
            
            logger.info(f"批量创建关系完成: {created_count}")
            return created_count
            
        except Exception as e:
            logger.error(f"批量创建关系失败: {e}")
            return 0
    
    async def _create_single_relation(
        self,
        tx,
        relation: Dict[str, Any]
    ) -> bool:
        """创建单个关系"""
        try:
            source = relation.get("source", "").strip()
            target = relation.get("target", "").strip()
            relation_type = relation.get("type", "RELATES_TO")
            confidence = relation.get("confidence", 1.0)
            properties = relation.get("properties", {})
            
            if not source or not target:
                return False
            
            # 创建关系
            query = f"""
            MATCH (s:Entity {{name: $source}})
            MATCH (t:Entity {{name: $target}})
            MERGE (s)-[r:{relation_type}]->(t)
            SET r.confidence = $confidence,
                r.properties = $properties,
                r.created_at = coalesce(r.created_at, datetime()),
                r.updated_at = datetime()
            RETURN r
            """
            
            result = await tx.run(query, {
                "source": source,
                "target": target,
                "confidence": confidence,
                "properties": properties
            })
            
            record = await result.single()
            return record is not None
            
        except Exception as e:
            logger.error(f"创建单个关系失败: {e}")
            return False
    
    async def search_entities(
        self,
        knowledge_base_id: int,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索实体"""
        try:
            await self.connect()
            
            # 构建查询条件
            type_filter = ""
            if entity_types:
                type_conditions = " OR ".join([f"e:{t}" for t in entity_types])
                type_filter = f"AND ({type_conditions})"
            
            cypher_query = f"""
            MATCH (d:Document {{knowledge_base_id: $kb_id}})-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE (e.name CONTAINS $query OR e.label CONTAINS $query) {type_filter}
            RETURN DISTINCT e.name as name, 
                   e.label as label, 
                   e.type as type,
                   e.confidence as confidence,
                   count(c) as mention_count
            ORDER BY mention_count DESC, e.confidence DESC
            LIMIT $limit
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher_query, {
                    "kb_id": knowledge_base_id,
                    "query": query,
                    "limit": limit
                })
                
                entities = []
                async for record in result:
                    entities.append({
                        "name": record["name"],
                        "label": record["label"],
                        "type": record["type"],
                        "confidence": record["confidence"],
                        "mention_count": record["mention_count"]
                    })
                
                logger.info(f"实体搜索完成，返回 {len(entities)} 个结果")
                return entities
                
        except Exception as e:
            logger.error(f"实体搜索失败: {e}")
            return []
    
    async def find_related_entities(
        self,
        entity_name: str,
        knowledge_base_id: int,
        max_hops: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """查找相关实体 (1-3跳关系推理)"""
        try:
            await self.connect()
            
            cypher_query = f"""
            MATCH (d:Document {{knowledge_base_id: $kb_id}})-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(start:Entity {{name: $entity_name}})
            MATCH path = (start)-[*1..{max_hops}]-(related:Entity)
            WHERE start <> related
            WITH related, length(path) as distance, count(path) as path_count
            RETURN DISTINCT related.name as name,
                   related.label as label,
                   related.type as type,
                   related.confidence as confidence,
                   distance,
                   path_count
            ORDER BY distance ASC, path_count DESC, related.confidence DESC
            LIMIT $limit
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher_query, {
                    "entity_name": entity_name,
                    "kb_id": knowledge_base_id,
                    "limit": limit
                })
                
                related_entities = []
                async for record in result:
                    related_entities.append({
                        "name": record["name"],
                        "label": record["label"],
                        "type": record["type"],
                        "confidence": record["confidence"],
                        "distance": record["distance"],
                        "path_count": record["path_count"]
                    })
                
                logger.info(f"相关实体查找完成，返回 {len(related_entities)} 个结果")
                return related_entities
                
        except Exception as e:
            logger.error(f"相关实体查找失败: {e}")
            return []
    
    async def get_entity_context(
        self,
        entity_name: str,
        knowledge_base_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取实体上下文信息"""
        try:
            await self.connect()
            
            cypher_query = """
            MATCH (d:Document {knowledge_base_id: $kb_id})-[:CONTAINS]->(c:Chunk)-[:MENTIONS]->(e:Entity {name: $entity_name})
            RETURN c.id as chunk_id,
                   c.content as content,
                   c.chunk_index as chunk_index,
                   d.id as document_id,
                   d.filename as filename
            ORDER BY c.chunk_index
            LIMIT $limit
            """
            
            async with self.driver.session() as session:
                result = await session.run(cypher_query, {
                    "entity_name": entity_name,
                    "kb_id": knowledge_base_id,
                    "limit": limit
                })
                
                contexts = []
                async for record in result:
                    contexts.append({
                        "chunk_id": record["chunk_id"],
                        "content": record["content"],
                        "chunk_index": record["chunk_index"],
                        "document_id": record["document_id"],
                        "filename": record["filename"]
                    })
                
                logger.info(f"实体上下文获取完成，返回 {len(contexts)} 个结果")
                return contexts
                
        except Exception as e:
            logger.error(f"获取实体上下文失败: {e}")
            return []
    
    async def delete_document_graph(self, document_id: int) -> bool:
        """删除文档相关的图谱数据"""
        try:
            await self.connect()
            
            cypher_query = """
            MATCH (d:Document {id: $document_id})-[:CONTAINS]->(c:Chunk)
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
            DETACH DELETE d, c
            WITH collect(DISTINCT e) as entities
            UNWIND entities as entity
            WITH entity
            WHERE NOT (entity)<-[:MENTIONS]-()
            DETACH DELETE entity
            """
            
            async with self.driver.session() as session:
                await session.run(cypher_query, {"document_id": document_id})
                
            logger.info(f"文档图谱数据删除完成: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档图谱数据失败: {e}")
            return False
    
    async def get_graph_stats(self, knowledge_base_id: int) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            await self.connect()
            
            stats_query = """
            MATCH (d:Document {knowledge_base_id: $kb_id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
            OPTIONAL MATCH (e1:Entity)-[r]-(e2:Entity)
            WHERE (e1)<-[:MENTIONS]-(:Chunk)<-[:CONTAINS]-(:Document {knowledge_base_id: $kb_id})
            AND (e2)<-[:MENTIONS]-(:Chunk)<-[:CONTAINS]-(:Document {knowledge_base_id: $kb_id})
            RETURN count(DISTINCT d) as document_count,
                   count(DISTINCT c) as chunk_count,
                   count(DISTINCT e) as entity_count,
                   count(DISTINCT r) as relation_count
            """
            
            async with self.driver.session() as session:
                result = await session.run(stats_query, {"kb_id": knowledge_base_id})
                record = await result.single()
                
                if record:
                    return {
                        "knowledge_base_id": knowledge_base_id,
                        "document_count": record["document_count"],
                        "chunk_count": record["chunk_count"],
                        "entity_count": record["entity_count"],
                        "relation_count": record["relation_count"]
                    }
                
        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            
        return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            await self.connect()
            
            # 测试查询
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if record and record["test"] == 1:
                    return {
                        "status": "healthy",
                        "uri": self.uri,
                        "connected": self._connected,
                        "max_hops": self.max_hops
                    }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "connected": False
            }


# 全局Neo4j服务实例
neo4j_service = Neo4jGraphService()


# 便捷函数
async def create_document_graph(
    document_id: int,
    knowledge_base_id: int,
    metadata: Dict[str, Any]
) -> bool:
    """创建文档图谱的便捷函数"""
    return await neo4j_service.create_document_node(
        document_id, knowledge_base_id, metadata
    )


async def add_chunk_to_graph(
    chunk_id: str,
    document_id: int,
    chunk_index: int,
    content: str,
    entities: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> bool:
    """将分块添加到图谱的便捷函数"""
    try:
        # 创建分块节点
        chunk_created = await neo4j_service.create_chunk_node(
            chunk_id, document_id, chunk_index, content, metadata
        )
        
        if not chunk_created:
            return False
        
        # 创建实体节点
        if entities:
            await neo4j_service.create_entity_nodes(chunk_id, entities)
        
        # 创建关系
        if relations:
            await neo4j_service.create_relations(relations)
        
        return True
        
    except Exception as e:
        logger.error(f"添加分块到图谱失败: {e}")
        return False


async def search_graph_entities(
    knowledge_base_id: int,
    query: str,
    entity_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """搜索图谱实体的便捷函数"""
    return await neo4j_service.search_entities(
        knowledge_base_id, query, entity_types
    )


async def find_entity_relations(
    entity_name: str,
    knowledge_base_id: int,
    max_hops: int = 2
) -> List[Dict[str, Any]]:
    """查找实体关系的便捷函数"""
    return await neo4j_service.find_related_entities(
        entity_name, knowledge_base_id, max_hops
    )
