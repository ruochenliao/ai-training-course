"""
知识图谱API端点
提供知识图谱的构建、查询和管理功能
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.knowledge_graph_service import knowledge_graph_service
from app.core.graph_store import get_graph_store
from app.models.user import User

logger = logging.getLogger(__name__)

knowledge_graph_router = APIRouter(tags=["知识图谱"])


class EntityCreateRequest(BaseModel):
    """创建实体请求"""
    name: str = Field(..., description="实体名称")
    entity_type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(None, description="实体描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实体属性")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")


class RelationshipCreateRequest(BaseModel):
    """创建关系请求"""
    source_entity_id: str = Field(..., description="源实体ID")
    target_entity_id: str = Field(..., description="目标实体ID")
    relationship_type: str = Field(..., description="关系类型")
    description: Optional[str] = Field(None, description="关系描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")


class TextExtractionRequest(BaseModel):
    """文本抽取请求"""
    text: str = Field(..., description="输入文本")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")
    auto_build: bool = Field(True, description="是否自动构建图谱")


class GraphQueryRequest(BaseModel):
    """图谱查询请求"""
    query: str = Field(..., description="查询文本")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")
    max_results: int = Field(10, description="最大结果数")


@knowledge_graph_router.post("/extract", summary="从文本抽取实体和关系")
async def extract_entities_and_relations(
    request: TextExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    从文本中抽取实体和关系
    """
    try:
        # 执行抽取
        extraction_result = await knowledge_graph_service.extract_entities_and_relations(
            text=request.text,
            knowledge_base_id=request.knowledge_base_id
        )
        
        # 如果启用自动构建，在后台构建图谱
        if request.auto_build and extraction_result.get("entities"):
            background_tasks.add_task(
                knowledge_graph_service.build_knowledge_graph,
                extraction_result
            )
        
        return {
            "success": True,
            "extraction_result": extraction_result,
            "auto_build": request.auto_build,
            "message": "实体关系抽取完成" + ("，正在后台构建图谱" if request.auto_build else "")
        }
        
    except Exception as e:
        logger.error(f"实体关系抽取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"抽取失败: {str(e)}")


@knowledge_graph_router.post("/build", summary="构建知识图谱")
async def build_knowledge_graph(
    extraction_result: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    基于抽取结果构建知识图谱
    """
    try:
        build_result = await knowledge_graph_service.build_knowledge_graph(extraction_result)
        
        return {
            "success": True,
            "build_result": build_result,
            "message": "知识图谱构建完成"
        }
        
    except Exception as e:
        logger.error(f"知识图谱构建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@knowledge_graph_router.post("/entities", summary="创建实体")
async def create_entity(
    request: EntityCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建新实体
    """
    try:
        graph_store = get_graph_store()
        
        # 生成实体ID
        entity_id = f"entity_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        success = await graph_store.create_entity(
            entity_id=entity_id,
            name=request.name,
            entity_type=request.entity_type,
            properties={
                "description": request.description or "",
                "created_by": current_user.id,
                **request.properties
            },
            knowledge_base_id=request.knowledge_base_id
        )
        
        if success:
            return {
                "success": True,
                "entity_id": entity_id,
                "message": "实体创建成功"
            }
        else:
            raise HTTPException(status_code=400, detail="实体创建失败")
            
    except Exception as e:
        logger.error(f"创建实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@knowledge_graph_router.post("/relationships", summary="创建关系")
async def create_relationship(
    request: RelationshipCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建实体间关系
    """
    try:
        graph_store = get_graph_store()
        
        success = await graph_store.create_relationship(
            source_entity_id=request.source_entity_id,
            target_entity_id=request.target_entity_id,
            relationship_type=request.relationship_type,
            properties={
                "description": request.description or "",
                "created_by": current_user.id,
                **request.properties
            }
        )
        
        if success:
            return {
                "success": True,
                "message": "关系创建成功"
            }
        else:
            raise HTTPException(status_code=400, detail="关系创建失败")
            
    except Exception as e:
        logger.error(f"创建关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@knowledge_graph_router.get("/entities", summary="查询实体")
async def find_entities(
    entity_type: Optional[str] = Query(None, description="实体类型"),
    name_pattern: Optional[str] = Query(None, description="名称模式"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID"),
    limit: int = Query(100, description="结果限制"),
    current_user: User = Depends(get_current_user)
):
    """
    查询实体列表
    """
    try:
        graph_store = get_graph_store()
        
        entities = await graph_store.find_entities(
            entity_type=entity_type,
            name_pattern=name_pattern,
            knowledge_base_id=knowledge_base_id,
            limit=limit
        )
        
        return {
            "success": True,
            "entities": entities,
            "total": len(entities),
            "message": f"找到 {len(entities)} 个实体"
        }
        
    except Exception as e:
        logger.error(f"查询实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@knowledge_graph_router.get("/entities/{entity_id}/related", summary="查询相关实体")
async def find_related_entities(
    entity_id: str,
    max_depth: int = Query(2, description="最大深度"),
    limit: int = Query(50, description="结果限制"),
    current_user: User = Depends(get_current_user)
):
    """
    查询实体的相关实体
    """
    try:
        graph_store = get_graph_store()
        
        related_entities = await graph_store.find_related_entities(
            entity_id=entity_id,
            max_depth=max_depth,
            limit=limit
        )
        
        return {
            "success": True,
            "entity_id": entity_id,
            "related_entities": related_entities,
            "total": len(related_entities),
            "message": f"找到 {len(related_entities)} 个相关实体"
        }
        
    except Exception as e:
        logger.error(f"查询相关实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@knowledge_graph_router.get("/entities/{source_id}/path/{target_id}", summary="查找实体间路径")
async def find_entity_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(5, description="最大搜索深度"),
    current_user: User = Depends(get_current_user)
):
    """
    查找两个实体间的最短路径
    """
    try:
        graph_store = get_graph_store()
        
        path = await graph_store.find_shortest_path(
            source_entity_id=source_id,
            target_entity_id=target_id,
            max_depth=max_depth
        )
        
        if path:
            return {
                "success": True,
                "source_id": source_id,
                "target_id": target_id,
                "path": path,
                "message": f"找到长度为 {path['path_length']} 的路径"
            }
        else:
            return {
                "success": False,
                "source_id": source_id,
                "target_id": target_id,
                "path": None,
                "message": "未找到连接路径"
            }
        
    except Exception as e:
        logger.error(f"查找路径失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查找失败: {str(e)}")


@knowledge_graph_router.post("/query", summary="智能图谱查询")
async def query_knowledge_graph(
    request: GraphQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    基于自然语言查询知识图谱
    """
    try:
        results = await knowledge_graph_service.query_knowledge_graph(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "total": len(results),
            "message": f"查询完成，返回 {len(results)} 个结果"
        }
        
    except Exception as e:
        logger.error(f"图谱查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@knowledge_graph_router.get("/statistics", summary="获取图谱统计")
async def get_graph_statistics(
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID"),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识图谱统计信息
    """
    try:
        stats = await knowledge_graph_service.get_statistics(knowledge_base_id)
        
        return {
            "success": True,
            "statistics": stats,
            "message": "统计信息获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@knowledge_graph_router.delete("/entities/{entity_id}", summary="删除实体")
async def delete_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除实体及其关系
    """
    try:
        graph_store = get_graph_store()
        
        success = await graph_store.delete_entity(entity_id)
        
        if success:
            return {
                "success": True,
                "entity_id": entity_id,
                "message": "实体删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="实体不存在或删除失败")
            
    except Exception as e:
        logger.error(f"删除实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@knowledge_graph_router.get("/health", summary="图数据库健康检查")
async def graph_health_check():
    """
    检查图数据库健康状态
    """
    try:
        graph_store = get_graph_store()
        health = await graph_store.health_check()
        
        return {
            "success": health["status"] == "healthy",
            "health": health,
            "message": "健康检查完成"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "success": False,
            "health": {"status": "unhealthy", "error": str(e)},
            "message": "健康检查失败"
        }
