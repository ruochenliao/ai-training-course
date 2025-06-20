"""
知识图谱服务
负责实体抽取、关系构建和图谱查询
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from ..core.graph_store import get_graph_store, GraphStoreException
from ..core.model_manager import model_manager, ModelType

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    知识图谱服务
    
    主要功能：
    - 从文本中抽取实体和关系
    - 构建和维护知识图谱
    - 基于图谱的智能查询
    - 知识推理和发现
    """
    
    def __init__(self):
        """初始化知识图谱服务"""
        self.graph_store = get_graph_store()
        self.entity_types = [
            "人物", "组织", "地点", "产品", "技术", "概念", 
            "时间", "数量", "事件", "文档", "其他"
        ]
        self.relation_types = [
            "属于", "包含", "相关", "依赖", "产生", "使用",
            "位于", "发生在", "参与", "拥有", "创建", "修改"
        ]
        
        logger.info("知识图谱服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        try:
            await self.graph_store.connect()
            logger.info("✅ 知识图谱服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 知识图谱服务初始化失败: {str(e)}")
            raise
    
    async def extract_entities_and_relations(
        self,
        text: str,
        knowledge_base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文本中抽取实体和关系
        
        Args:
            text: 输入文本
            knowledge_base_id: 知识库ID
            
        Returns:
            抽取结果
        """
        try:
            # 使用LLM进行实体和关系抽取
            llm_service = model_manager.get_default_model(ModelType.LLM)
            
            if llm_service:
                # 构建提示词
                prompt = self._build_extraction_prompt(text)
                
                # 调用LLM
                response = await llm_service.chat_completion(
                    messages=[
                        {"role": "system", "content": "你是一个专业的知识图谱构建专家，擅长从文本中抽取实体和关系。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                
                # 解析LLM响应
                extraction_result = self._parse_extraction_response(response)
            else:
                # 降级到规则基础的抽取
                extraction_result = await self._rule_based_extraction(text)
            
            # 标准化结果
            entities = extraction_result.get("entities", [])
            relations = extraction_result.get("relations", [])
            
            # 为实体生成ID
            for entity in entities:
                if "id" not in entity:
                    entity["id"] = self._generate_entity_id(entity["name"], entity["type"])
                entity["knowledge_base_id"] = knowledge_base_id
            
            return {
                "entities": entities,
                "relations": relations,
                "text": text,
                "knowledge_base_id": knowledge_base_id
            }
            
        except Exception as e:
            logger.error(f"实体关系抽取失败: {str(e)}")
            return {
                "entities": [],
                "relations": [],
                "text": text,
                "knowledge_base_id": knowledge_base_id,
                "error": str(e)
            }
    
    def _build_extraction_prompt(self, text: str) -> str:
        """构建实体关系抽取提示词"""
        entity_types_str = "、".join(self.entity_types)
        relation_types_str = "、".join(self.relation_types)
        
        prompt = f"""
请从以下文本中抽取实体和关系，并以JSON格式返回结果。

实体类型包括：{entity_types_str}
关系类型包括：{relation_types_str}

文本内容：
{text}

请按以下JSON格式返回结果：
{{
    "entities": [
        {{
            "name": "实体名称",
            "type": "实体类型",
            "description": "实体描述",
            "properties": {{}}
        }}
    ],
    "relations": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型",
            "description": "关系描述",
            "properties": {{}}
        }}
    ]
}}

注意：
1. 只抽取明确存在的实体和关系
2. 实体名称要准确，避免重复
3. 关系要有明确的方向性
4. 描述要简洁准确
"""
        return prompt
    
    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """解析LLM抽取响应"""
        try:
            # 尝试直接解析JSON
            if response.strip().startswith("{"):
                return json.loads(response)
            
            # 查找JSON块
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # 如果无法解析，返回空结果
            logger.warning("无法解析LLM抽取响应")
            return {"entities": [], "relations": []}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return {"entities": [], "relations": []}
    
    async def _rule_based_extraction(self, text: str) -> Dict[str, Any]:
        """基于规则的实体关系抽取（降级方案）"""
        entities = []
        relations = []
        
        # 简单的实体识别规则
        # 这里可以添加更复杂的规则或使用NLP库
        
        # 识别可能的实体（简单示例）
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 1 and word.isalpha():
                # 简单的实体识别逻辑
                entity = {
                    "name": word,
                    "type": "概念",
                    "description": f"从文本中识别的概念: {word}",
                    "properties": {"position": i}
                }
                entities.append(entity)
        
        # 去重
        seen_names = set()
        unique_entities = []
        for entity in entities:
            if entity["name"] not in seen_names:
                seen_names.add(entity["name"])
                unique_entities.append(entity)
        
        return {
            "entities": unique_entities[:10],  # 限制数量
            "relations": relations
        }
    
    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """生成实体ID"""
        # 使用名称和类型的哈希值作为ID
        import hashlib
        content = f"{name}_{entity_type}".lower()
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def build_knowledge_graph(
        self,
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            extraction_result: 实体关系抽取结果
            
        Returns:
            构建结果
        """
        try:
            entities = extraction_result.get("entities", [])
            relations = extraction_result.get("relations", [])
            knowledge_base_id = extraction_result.get("knowledge_base_id")
            
            created_entities = 0
            created_relations = 0
            errors = []
            
            # 创建实体
            for entity in entities:
                try:
                    success = await self.graph_store.create_entity(
                        entity_id=entity["id"],
                        name=entity["name"],
                        entity_type=entity["type"],
                        properties={
                            "description": entity.get("description", ""),
                            **entity.get("properties", {})
                        },
                        knowledge_base_id=knowledge_base_id
                    )
                    if success:
                        created_entities += 1
                except Exception as e:
                    errors.append(f"创建实体失败 {entity['name']}: {str(e)}")
            
            # 创建关系
            for relation in relations:
                try:
                    # 查找源实体和目标实体ID
                    source_entity = next(
                        (e for e in entities if e["name"] == relation["source"]), 
                        None
                    )
                    target_entity = next(
                        (e for e in entities if e["name"] == relation["target"]), 
                        None
                    )
                    
                    if source_entity and target_entity:
                        success = await self.graph_store.create_relationship(
                            source_entity_id=source_entity["id"],
                            target_entity_id=target_entity["id"],
                            relationship_type=relation["type"],
                            properties={
                                "description": relation.get("description", ""),
                                **relation.get("properties", {})
                            }
                        )
                        if success:
                            created_relations += 1
                    else:
                        errors.append(f"关系实体未找到: {relation['source']} -> {relation['target']}")
                        
                except Exception as e:
                    errors.append(f"创建关系失败 {relation['source']} -> {relation['target']}: {str(e)}")
            
            result = {
                "success": True,
                "created_entities": created_entities,
                "created_relations": created_relations,
                "total_entities": len(entities),
                "total_relations": len(relations),
                "errors": errors,
                "knowledge_base_id": knowledge_base_id
            }
            
            logger.info(f"知识图谱构建完成: 实体 {created_entities}/{len(entities)}, 关系 {created_relations}/{len(relations)}")
            return result
            
        except Exception as e:
            logger.error(f"知识图谱构建失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "created_entities": 0,
                "created_relations": 0
            }
    
    async def query_knowledge_graph(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询知识图谱
        
        Args:
            query: 查询文本
            knowledge_base_id: 知识库ID
            max_results: 最大结果数
            
        Returns:
            查询结果
        """
        try:
            # 从查询中提取关键词
            keywords = self._extract_keywords(query)
            
            results = []
            
            # 查找匹配的实体
            for keyword in keywords:
                entities = await self.graph_store.find_entities(
                    name_pattern=keyword,
                    knowledge_base_id=knowledge_base_id,
                    limit=max_results
                )
                
                for entity in entities:
                    # 查找相关实体
                    related_entities = await self.graph_store.find_related_entities(
                        entity_id=entity["id"],
                        max_depth=2,
                        limit=5
                    )
                    
                    result = {
                        "entity": entity,
                        "related_entities": related_entities,
                        "relevance_score": self._calculate_relevance(query, entity)
                    }
                    results.append(result)
            
            # 按相关性排序
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"知识图谱查询失败: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'\w+', text.lower())
        # 过滤停用词
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "如果", "因为", "所以"}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords[:5]  # 限制关键词数量
    
    def _calculate_relevance(self, query: str, entity: Dict[str, Any]) -> float:
        """计算相关性分数"""
        query_lower = query.lower()
        entity_name = entity.get("name", "").lower()
        entity_desc = entity.get("description", "").lower()
        
        score = 0.0
        
        # 名称匹配
        if entity_name in query_lower:
            score += 1.0
        elif any(word in entity_name for word in query_lower.split()):
            score += 0.5
        
        # 描述匹配
        if any(word in entity_desc for word in query_lower.split()):
            score += 0.3
        
        return score
    
    async def get_statistics(self, knowledge_base_id: Optional[str] = None) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        try:
            stats = await self.graph_store.get_graph_statistics(knowledge_base_id)
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {
                "entity_count": 0,
                "relationship_count": 0,
                "entity_types": [],
                "relationship_types": [],
                "error": str(e)
            }


# 全局知识图谱服务实例
knowledge_graph_service = KnowledgeGraphService()
