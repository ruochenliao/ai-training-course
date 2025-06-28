"""
知识图谱API端点
"""

from typing import Any, List, Optional

from app.core.security import get_current_user
from app.models.knowledge import KnowledgeBase
from app.models.user import User
from app.services.neo4j_graph_service import neo4j_graph_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

router = APIRouter()


class GraphNode(BaseModel):
    """图节点"""
    id: str
    label: str
    type: str
    properties: dict = {}


class GraphEdge(BaseModel):
    """图边"""
    id: str
    source: str
    target: str
    type: str
    properties: dict = {}


class GraphVisualizationResponse(BaseModel):
    """图谱可视化响应"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    knowledge_base_id: Optional[int] = None


class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    name: str
    type: str
    properties: dict = {}
    relations_count: int = 0


class RelationResponse(BaseModel):
    """关系响应"""
    id: str
    source_entity: str
    target_entity: str
    relation_type: str
    properties: dict = {}


@router.get("/visualize", response_model=GraphVisualizationResponse, summary="获取知识图谱可视化数据")
async def get_knowledge_graph(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    depth: int = Query(2, ge=1, le=5, description="图谱深度"),
    limit: int = Query(100, ge=1, le=1000, description="节点数量限制"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取知识图谱可视化数据
    """
    try:
        # 检查知识库权限
        if knowledge_base_id:
            knowledge_base = await KnowledgeBase.get_or_none(
                id=knowledge_base_id,
                is_deleted=False
            )
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 检查权限
            if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
                if knowledge_base.visibility != "public":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此知识库"
                    )

        # 获取图谱数据
        graph_data = await neo4j_graph_service.get_graph_visualization(
            knowledge_base_id=knowledge_base_id,
            entity_type=entity_type,
            depth=depth,
            limit=limit
        )

        # 转换为响应格式
        nodes = []
        for node in graph_data.get("nodes", []):
            nodes.append(GraphNode(
                id=node["id"],
                label=node["label"],
                type=node["type"],
                properties=node.get("properties", {})
            ))

        edges = []
        for edge in graph_data.get("edges", []):
            edges.append(GraphEdge(
                id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                type=edge["type"],
                properties=edge.get("properties", {})
            ))

        return GraphVisualizationResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            knowledge_base_id=knowledge_base_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识图谱失败: {str(e)}"
        )


@router.get("/entities", summary="获取实体列表")
async def get_graph_entities(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取实体列表
    """
    try:
        # 检查知识库权限
        if knowledge_base_id:
            knowledge_base = await KnowledgeBase.get_or_none(
                id=knowledge_base_id,
                is_deleted=False
            )
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 检查权限
            if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
                if knowledge_base.visibility != "public":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此知识库"
                    )

        # 获取实体列表
        entities_data = await neo4j_graph_service.get_entities(
            knowledge_base_id=knowledge_base_id,
            entity_type=entity_type,
            search=search,
            page=page,
            size=size
        )

        # 转换为响应格式
        entities = []
        for entity in entities_data.get("entities", []):
            entities.append(EntityResponse(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                properties=entity.get("properties", {}),
                relations_count=entity.get("relations_count", 0)
            ))

        return {
            "entities": entities,
            "total": entities_data.get("total", 0),
            "page": page,
            "size": size,
            "pages": (entities_data.get("total", 0) + size - 1) // size
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实体列表失败: {str(e)}"
        )


@router.get("/relations", summary="获取关系列表")
async def get_graph_relations(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    relation_type: Optional[str] = Query(None, description="关系类型"),
    source_entity: Optional[str] = Query(None, description="源实体"),
    target_entity: Optional[str] = Query(None, description="目标实体"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取关系列表
    """
    try:
        # 检查知识库权限
        if knowledge_base_id:
            knowledge_base = await KnowledgeBase.get_or_none(
                id=knowledge_base_id,
                is_deleted=False
            )
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 检查权限
            if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
                if knowledge_base.visibility != "public":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此知识库"
                    )

        # 获取关系列表
        relations_data = await neo4j_graph_service.get_relations(
            knowledge_base_id=knowledge_base_id,
            relation_type=relation_type,
            source_entity=source_entity,
            target_entity=target_entity,
            page=page,
            size=size
        )

        # 转换为响应格式
        relations = []
        for relation in relations_data.get("relations", []):
            relations.append(RelationResponse(
                id=relation["id"],
                source_entity=relation["source_entity"],
                target_entity=relation["target_entity"],
                relation_type=relation["relation_type"],
                properties=relation.get("properties", {})
            ))

        return {
            "relations": relations,
            "total": relations_data.get("total", 0),
            "page": page,
            "size": size,
            "pages": (relations_data.get("total", 0) + size - 1) // size
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取关系列表失败: {str(e)}"
        )


@router.get("/stats", summary="获取图谱统计信息")
async def get_graph_stats(
    knowledge_base_id: Optional[int] = Query(None, description="知识库ID"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取图谱统计信息
    """
    try:
        # 检查知识库权限
        if knowledge_base_id:
            knowledge_base = await KnowledgeBase.get_or_none(
                id=knowledge_base_id,
                is_deleted=False
            )
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="知识库不存在"
                )
            
            # 检查权限
            if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
                if knowledge_base.visibility != "public":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问此知识库"
                    )

        # 获取统计信息
        stats = await neo4j_graph_service.get_graph_stats(
            knowledge_base_id=knowledge_base_id
        )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图谱统计信息失败: {str(e)}"
        )
