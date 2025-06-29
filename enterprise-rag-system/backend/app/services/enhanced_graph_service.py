"""
增强版Neo4j知识图谱服务
支持实体抽取、关系识别、图谱构建、路径搜索、可视化
"""

import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any

from loguru import logger

from app.services.neo4j_graph_service import Neo4jGraphService as Neo4jService
from app.core import GraphDatabaseException


@dataclass
class Entity:
    """实体类"""
    name: str
    type: str
    properties: Dict[str, Any]
    confidence: float = 0.0
    mentions: List[str] = None
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []


@dataclass
class Relationship:
    """关系类"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any]
    confidence: float = 0.0


@dataclass
class GraphPath:
    """图谱路径"""
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    length: int
    score: float
    description: str


class EntityExtractor:
    """实体抽取器"""
    
    def __init__(self):
        # 预定义实体类型和模式
        self.entity_patterns = {
            'PERSON': [
                r'(?:先生|女士|教授|博士|老师|同学)\s*([^\s，。！？；：]{2,4})',
                r'([^\s，。！？；：]{2,4})\s*(?:先生|女士|教授|博士|老师|同学)',
                r'(?:CEO|CTO|CFO|总裁|总经理|经理|主任|部长)\s*([^\s，。！？；：]{2,4})',
            ],
            'ORGANIZATION': [
                r'([^\s，。！？；：]{2,10}(?:公司|企业|集团|机构|组织|协会|学会|大学|学院|研究所|实验室))',
                r'([^\s，。！？；：]{2,10}(?:有限公司|股份有限公司|科技有限公司))',
            ],
            'LOCATION': [
                r'([^\s，。！？；：]{2,8}(?:省|市|县|区|镇|村|街道|路|街|巷|号))',
                r'([^\s，。！？；：]{2,8}(?:国|州|洲|岛|山|河|湖|海))',
            ],
            'PRODUCT': [
                r'([^\s，。！？；：]{2,10}(?:系统|平台|软件|应用|产品|服务|解决方案))',
                r'([^\s，。！？；：]{2,10}(?:版本|型号|规格))',
            ],
            'CONCEPT': [
                r'([^\s，。！？；：]{2,8}(?:技术|方法|理论|概念|原理|算法|模型))',
                r'([^\s，。！？；：]{2,8}(?:标准|规范|协议|框架))',
            ]
        }
        
        # 关系模式
        self.relation_patterns = {
            'BELONGS_TO': [
                r'(.+?)(?:属于|隶属于|归属于)(.+)',
                r'(.+?)(?:是|为)(.+?)(?:的|之)',
            ],
            'LOCATED_IN': [
                r'(.+?)(?:位于|在|处于)(.+)',
                r'(.+?)(?:的|之)(.+?)(?:地区|地方|位置)',
            ],
            'WORKS_FOR': [
                r'(.+?)(?:在|于)(.+?)(?:工作|任职|就职)',
                r'(.+?)(?:是|为)(.+?)(?:的|之)(?:员工|职员|成员)',
            ],
            'DEVELOPS': [
                r'(.+?)(?:开发|研发|制作|创建)(?:了)?(.+)',
                r'(.+?)(?:负责|主导)(.+?)(?:的|之)(?:开发|研发)',
            ],
            'USES': [
                r'(.+?)(?:使用|采用|应用|利用)(?:了)?(.+)',
                r'(.+?)(?:基于|依据)(.+?)(?:实现|构建)',
            ]
        }
    
    def extract_entities(self, text: str) -> List[Entity]:
        """从文本中抽取实体"""
        entities = []
        found_entities = set()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_name = match.group(1).strip()
                    
                    # 避免重复和过短的实体
                    if len(entity_name) >= 2 and entity_name not in found_entities:
                        found_entities.add(entity_name)
                        
                        entity = Entity(
                            name=entity_name,
                            type=entity_type,
                            properties={
                                'source_text': text,
                                'pattern_matched': pattern,
                                'position': match.start()
                            },
                            confidence=self._calculate_entity_confidence(entity_name, entity_type, text),
                            mentions=[entity_name]
                        )
                        entities.append(entity)
        
        return entities
    
    def extract_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """从文本中抽取关系"""
        relationships = []
        entity_names = {entity.name for entity in entities}
        
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    source = match.group(1).strip()
                    target = match.group(2).strip()
                    
                    # 检查是否为已识别的实体
                    if source in entity_names and target in entity_names:
                        relationship = Relationship(
                            source=source,
                            target=target,
                            type=relation_type,
                            properties={
                                'source_text': text,
                                'pattern_matched': pattern,
                                'position': match.start()
                            },
                            confidence=self._calculate_relation_confidence(source, target, relation_type, text)
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def _calculate_entity_confidence(self, entity_name: str, entity_type: str, text: str) -> float:
        """计算实体置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于实体长度
        if len(entity_name) >= 3:
            confidence += 0.1
        
        # 基于出现频率
        count = text.count(entity_name)
        if count > 1:
            confidence += min(count * 0.1, 0.3)
        
        # 基于上下文
        context_keywords = {
            'PERSON': ['先生', '女士', '教授', '博士'],
            'ORGANIZATION': ['公司', '企业', '机构', '大学'],
            'LOCATION': ['省', '市', '县', '区'],
            'PRODUCT': ['系统', '平台', '软件', '产品'],
            'CONCEPT': ['技术', '方法', '理论', '概念']
        }
        
        if entity_type in context_keywords:
            for keyword in context_keywords[entity_type]:
                if keyword in text:
                    confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _calculate_relation_confidence(self, source: str, target: str, relation_type: str, text: str) -> float:
        """计算关系置信度"""
        confidence = 0.6  # 基础置信度
        
        # 基于距离
        source_pos = text.find(source)
        target_pos = text.find(target)
        if source_pos != -1 and target_pos != -1:
            distance = abs(source_pos - target_pos)
            if distance < 50:
                confidence += 0.2
            elif distance < 100:
                confidence += 0.1
        
        return min(confidence, 1.0)


class EnhancedGraphService:
    """增强版知识图谱服务"""
    
    def __init__(self):
        self.base_service = Neo4jService()
        self.entity_extractor = EntityExtractor()
        
        # 图谱统计
        self.stats = {
            'total_entities': 0,
            'total_relationships': 0,
            'entity_types': defaultdict(int),
            'relationship_types': defaultdict(int)
        }
        
        logger.info("增强版知识图谱服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        await self.base_service.connect()
        
        # 创建索引
        await self._create_indexes()
        
        # 更新统计信息
        await self._update_stats()
    
    async def _create_indexes(self):
        """创建图数据库索引"""
        try:
            index_queries = [
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (n:Entity) ON (n.name)",
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (n:Entity) ON (n.type)",
                "CREATE INDEX entity_kb_idx IF NOT EXISTS FOR (n:Entity) ON (n.knowledge_base_id)",
                "CREATE INDEX document_idx IF NOT EXISTS FOR (n:Document) ON (n.document_id)",
                "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (n:Entity) REQUIRE (n.name, n.knowledge_base_id) IS UNIQUE"
            ]
            
            for query in index_queries:
                try:
                    await self.base_service.execute_query(query)
                except Exception as e:
                    logger.warning(f"创建索引失败: {query}, 错误: {e}")
            
            logger.info("图数据库索引创建完成")
            
        except Exception as e:
            logger.error(f"创建图数据库索引失败: {e}")
    
    async def build_knowledge_graph(
        self,
        document_id: int,
        content: str,
        knowledge_base_id: int,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """构建知识图谱"""
        try:
            start_time = time.time()
            
            # 1. 实体抽取
            entities = self.entity_extractor.extract_entities(content)
            logger.info(f"抽取到 {len(entities)} 个实体")
            
            # 2. 关系抽取
            relationships = self.entity_extractor.extract_relationships(content, entities)
            logger.info(f"抽取到 {len(relationships)} 个关系")
            
            # 3. 创建文档节点
            doc_node = await self.base_service.create_node(
                label="Document",
                properties={
                    "document_id": document_id,
                    "content": content[:1000],  # 限制长度
                    "metadata": metadata or {},
                    "created_at": time.time()
                },
                knowledge_base_id=knowledge_base_id
            )
            
            # 4. 创建实体节点
            entity_nodes = {}
            for entity in entities:
                # 检查实体是否已存在
                existing_entities = await self.base_service.find_nodes(
                    label="Entity",
                    properties={"name": entity.name},
                    knowledge_base_ids=[knowledge_base_id]
                )
                
                if existing_entities:
                    # 更新现有实体
                    entity_node = existing_entities[0]
                    entity_nodes[entity.name] = entity_node
                else:
                    # 创建新实体
                    entity_node = await self.base_service.create_node(
                        label="Entity",
                        properties={
                            "name": entity.name,
                            "type": entity.type,
                            "confidence": entity.confidence,
                            "mentions": entity.mentions,
                            "properties": entity.properties,
                            "created_at": time.time()
                        },
                        knowledge_base_id=knowledge_base_id
                    )
                    entity_nodes[entity.name] = entity_node
                
                # 创建文档-实体关系
                await self.base_service.create_relationship(
                    start_node_id=doc_node['_id'],
                    end_node_id=entity_node['_id'],
                    relationship_type="CONTAINS",
                    properties={
                        "confidence": entity.confidence,
                        "position": entity.properties.get('position', 0)
                    }
                )
            
            # 5. 创建实体间关系
            relationship_count = 0
            for relationship in relationships:
                if relationship.source in entity_nodes and relationship.target in entity_nodes:
                    await self.base_service.create_relationship(
                        start_node_id=entity_nodes[relationship.source]['_id'],
                        end_node_id=entity_nodes[relationship.target]['_id'],
                        relationship_type=relationship.type,
                        properties={
                            "confidence": relationship.confidence,
                            "source_text": relationship.properties.get('source_text', ''),
                            "created_at": time.time()
                        }
                    )
                    relationship_count += 1
            
            processing_time = time.time() - start_time
            
            # 更新统计
            await self._update_stats()
            
            result = {
                "document_node_id": doc_node['_id'],
                "entities_created": len(entity_nodes),
                "relationships_created": relationship_count,
                "processing_time": processing_time,
                "entities": [
                    {
                        "name": entity.name,
                        "type": entity.type,
                        "confidence": entity.confidence,
                        "node_id": entity_nodes[entity.name]['_id']
                    }
                    for entity in entities if entity.name in entity_nodes
                ]
            }
            
            logger.info(f"知识图谱构建完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {e}")
            raise GraphDatabaseException(f"构建知识图谱失败: {e}")
    
    async def find_paths(
        self,
        start_entity: str,
        end_entity: str = None,
        max_depth: int = 3,
        max_nodes: int = 100,
        knowledge_base_ids: List[int] = None
    ) -> List[GraphPath]:
        """查找图谱路径"""
        try:
            if end_entity:
                # 查找两个实体间的路径
                query = f"""
                MATCH path = (start:Entity {{name: $start_name}})-[*1..{max_depth}]-(end:Entity {{name: $end_name}})
                WHERE start.knowledge_base_id IN $kb_ids AND end.knowledge_base_id IN $kb_ids
                RETURN path, length(path) as path_length
                ORDER BY path_length
                LIMIT {max_nodes}
                """
                params = {
                    "start_name": start_entity,
                    "end_name": end_entity,
                    "kb_ids": knowledge_base_ids or [1]
                }
            else:
                # 查找从起始实体出发的路径
                query = f"""
                MATCH path = (start:Entity {{name: $start_name}})-[*1..{max_depth}]-(end:Entity)
                WHERE start.knowledge_base_id IN $kb_ids
                RETURN path, length(path) as path_length, end.name as end_name
                ORDER BY path_length
                LIMIT {max_nodes}
                """
                params = {
                    "start_name": start_entity,
                    "kb_ids": knowledge_base_ids or [1]
                }
            
            results = await self.base_service.execute_query(query, params)
            
            paths = []
            for result in results:
                path_data = result['path']
                path_length = result['path_length']
                
                # 解析路径
                nodes = []
                relationships = []
                
                # 这里需要根据Neo4j返回的路径数据结构进行解析
                # 简化实现
                path = GraphPath(
                    nodes=nodes,
                    relationships=relationships,
                    length=path_length,
                    score=1.0 / (path_length + 1),  # 简单评分
                    description=f"从 {start_entity} 到 {result.get('end_name', end_entity)} 的路径"
                )
                paths.append(path)
            
            return paths
            
        except Exception as e:
            logger.error(f"查找图谱路径失败: {e}")
            raise GraphDatabaseException(f"查找图谱路径失败: {e}")
    
    async def extract_entities(self, text: str) -> List[str]:
        """抽取实体（兼容性方法）"""
        entities = self.entity_extractor.extract_entities(text)
        return [entity.name for entity in entities]
    
    async def get_entity_neighbors(
        self,
        entity_name: str,
        max_depth: int = 2,
        knowledge_base_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """获取实体的邻居节点"""
        try:
            query = f"""
            MATCH (entity:Entity {{name: $entity_name}})-[r*1..{max_depth}]-(neighbor:Entity)
            WHERE entity.knowledge_base_id IN $kb_ids
            RETURN DISTINCT neighbor, r[0] as first_relation, length(r) as distance
            ORDER BY distance, neighbor.name
            LIMIT 50
            """
            
            params = {
                "entity_name": entity_name,
                "kb_ids": knowledge_base_ids or [1]
            }
            
            results = await self.base_service.execute_query(query, params)
            
            neighbors = []
            for result in results:
                neighbor = result['neighbor']
                relation = result.get('first_relation', {})
                distance = result['distance']
                
                neighbors.append({
                    "entity": neighbor,
                    "relationship": relation,
                    "distance": distance
                })
            
            return neighbors
            
        except Exception as e:
            logger.error(f"获取实体邻居失败: {e}")
            return []
    
    async def _update_stats(self):
        """更新统计信息"""
        try:
            stats = await self.base_service.get_graph_stats()
            
            self.stats['total_entities'] = 0
            self.stats['total_relationships'] = stats.get('relationship_count', 0)
            
            # 统计实体类型
            for label_info in stats.get('label_counts', []):
                labels = label_info.get('labels', [])
                count = label_info.get('count', 0)
                if 'Entity' in labels:
                    self.stats['total_entities'] += count
            
            # 统计关系类型
            for rel_info in stats.get('relationship_type_counts', []):
                rel_type = rel_info.get('type', '')
                count = rel_info.get('count', 0)
                self.stats['relationship_types'][rel_type] = count
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return dict(self.stats)


# 全局增强版图谱服务实例
enhanced_graph_service = EnhancedGraphService()
