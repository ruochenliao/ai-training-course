"""
实体关系抽取服务
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from app.core.config import settings
from app.services.llm_service import llm_service
from loguru import logger

from app.core.exceptions import ExternalServiceException


@dataclass
class Entity:
    """实体类"""
    name: str
    type: str
    description: str = ""
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class Relationship:
    """关系类"""
    source: str
    target: str
    type: str
    description: str = ""
    properties: Dict[str, Any] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class EntityExtractionService:
    """实体关系抽取服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.entity_types = [
            "人物", "组织", "地点", "时间", "事件", "概念", "产品", "技术", 
            "方法", "工具", "标准", "法规", "指标", "数据", "文档"
        ]
        
        self.relationship_types = [
            "属于", "包含", "使用", "依赖", "关联", "影响", "产生", "导致",
            "基于", "实现", "支持", "管理", "负责", "参与", "位于", "发生于"
        ]
        
        logger.info("实体关系抽取服务初始化完成")
    
    async def extract_entities_and_relationships(
        self,
        text: str,
        domain: str = "general",
        language: str = "zh"
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        从文本中抽取实体和关系
        
        Args:
            text: 输入文本
            domain: 领域类型
            language: 语言
            
        Returns:
            实体列表和关系列表的元组
        """
        try:
            # 分块处理长文本
            chunks = self._split_text(text, max_length=2000)
            
            all_entities = []
            all_relationships = []
            
            for chunk in chunks:
                entities, relationships = await self._extract_from_chunk(
                    chunk, domain, language
                )
                all_entities.extend(entities)
                all_relationships.extend(relationships)
            
            # 去重和合并
            entities = self._merge_entities(all_entities)
            relationships = self._merge_relationships(all_relationships)
            
            logger.info(f"抽取完成: {len(entities)} 个实体, {len(relationships)} 个关系")
            return entities, relationships
            
        except Exception as e:
            logger.error(f"实体关系抽取失败: {e}")
            raise ExternalServiceException(f"实体关系抽取失败: {e}")
    
    async def _extract_from_chunk(
        self,
        text: str,
        domain: str,
        language: str
    ) -> Tuple[List[Entity], List[Relationship]]:
        """从文本块中抽取实体和关系"""
        
        # 构建提示词
        prompt = self._build_extraction_prompt(text, domain, language)
        
        # 调用LLM
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )
        
        # 解析结果
        entities, relationships = self._parse_extraction_result(response["content"])
        
        return entities, relationships
    
    def _build_extraction_prompt(self, text: str, domain: str, language: str) -> str:
        """构建抽取提示词"""
        
        entity_types_str = "、".join(self.entity_types)
        relationship_types_str = "、".join(self.relationship_types)
        
        if language == "zh":
            prompt = f"""
请从以下文本中抽取实体和关系，并以JSON格式返回结果。

文本内容：
{text}

抽取要求：
1. 实体类型包括但不限于：{entity_types_str}
2. 关系类型包括但不限于：{relationship_types_str}
3. 领域：{domain}
4. 只抽取明确存在的实体和关系，避免推测
5. 实体名称要规范化，去除冗余词汇
6. 关系要有明确的方向性

返回格式：
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型",
      "description": "实体描述"
    }}
  ],
  "relationships": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称", 
      "type": "关系类型",
      "description": "关系描述",
      "confidence": 0.9
    }}
  ]
}}

请确保返回的是有效的JSON格式。
"""
        else:
            prompt = f"""
Please extract entities and relationships from the following text and return the results in JSON format.

Text content:
{text}

Extraction requirements:
1. Entity types include but are not limited to: {entity_types_str}
2. Relationship types include but are not limited to: {relationship_types_str}
3. Domain: {domain}
4. Only extract clearly existing entities and relationships, avoid speculation
5. Entity names should be normalized, removing redundant words
6. Relationships should have clear directionality

Return format:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "entity type",
      "description": "entity description"
    }}
  ],
  "relationships": [
    {{
      "source": "source entity name",
      "target": "target entity name",
      "type": "relationship type", 
      "description": "relationship description",
      "confidence": 0.9
    }}
  ]
}}

Please ensure the returned result is in valid JSON format.
"""
        
        return prompt
    
    def _parse_extraction_result(self, response: str) -> Tuple[List[Entity], List[Relationship]]:
        """解析抽取结果"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("未找到有效的JSON格式")
                return [], []
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # 解析实体
            entities = []
            for entity_data in data.get("entities", []):
                entity = Entity(
                    name=entity_data.get("name", "").strip(),
                    type=entity_data.get("type", "").strip(),
                    description=entity_data.get("description", "").strip()
                )
                if entity.name and entity.type:
                    entities.append(entity)
            
            # 解析关系
            relationships = []
            for rel_data in data.get("relationships", []):
                relationship = Relationship(
                    source=rel_data.get("source", "").strip(),
                    target=rel_data.get("target", "").strip(),
                    type=rel_data.get("type", "").strip(),
                    description=rel_data.get("description", "").strip(),
                    confidence=float(rel_data.get("confidence", 0.8))
                )
                if relationship.source and relationship.target and relationship.type:
                    relationships.append(relationship)
            
            return entities, relationships
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return [], []
        except Exception as e:
            logger.error(f"结果解析失败: {e}")
            return [], []
    
    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """分割长文本"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = re.split(r'[。！？\n]', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并重复实体"""
        entity_dict = {}
        
        for entity in entities:
            key = (entity.name.lower(), entity.type.lower())
            if key in entity_dict:
                # 合并描述
                existing = entity_dict[key]
                if entity.description and entity.description not in existing.description:
                    existing.description += f"; {entity.description}"
                # 合并属性
                existing.properties.update(entity.properties)
            else:
                entity_dict[key] = entity
        
        return list(entity_dict.values())
    
    def _merge_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """合并重复关系"""
        rel_dict = {}
        
        for rel in relationships:
            key = (rel.source.lower(), rel.target.lower(), rel.type.lower())
            if key in rel_dict:
                # 保留置信度更高的关系
                existing = rel_dict[key]
                if rel.confidence > existing.confidence:
                    rel_dict[key] = rel
            else:
                rel_dict[key] = rel
        
        return list(rel_dict.values())
    
    async def extract_entities_only(
        self,
        text: str,
        entity_types: List[str] = None,
        domain: str = "general"
    ) -> List[Entity]:
        """仅抽取实体"""
        entity_types = entity_types or self.entity_types
        
        prompt = f"""
请从以下文本中抽取实体，返回JSON格式：

文本：{text}

实体类型：{', '.join(entity_types)}
领域：{domain}

返回格式：
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型",
      "description": "实体描述"
    }}
  ]
}}
"""
        
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        
        entities, _ = self._parse_extraction_result(response["content"])
        return entities
    
    async def extract_relationships_only(
        self,
        text: str,
        entities: List[str],
        relationship_types: List[str] = None
    ) -> List[Relationship]:
        """仅抽取关系"""
        relationship_types = relationship_types or self.relationship_types
        
        entities_str = "、".join(entities)
        rel_types_str = "、".join(relationship_types)
        
        prompt = f"""
请从以下文本中抽取实体间的关系，返回JSON格式：

文本：{text}

已知实体：{entities_str}
关系类型：{rel_types_str}

返回格式：
{{
  "relationships": [
    {{
      "source": "源实体",
      "target": "目标实体",
      "type": "关系类型",
      "description": "关系描述",
      "confidence": 0.9
    }}
  ]
}}
"""
        
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        
        _, relationships = self._parse_extraction_result(response["content"])
        return relationships


# 全局实体抽取服务实例
entity_extraction_service = EntityExtractionService()
