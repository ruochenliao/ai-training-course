"""
知识库管理API
基于ChromaDB向量数据库的个人知识库和公共知识库管理接口
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from ....schemas.knowledge import (
    KnowledgeAddRequest,
    KnowledgeUpdateRequest,
    KnowledgeSearchRequest
)
from ....services.memory.factory import MemoryServiceFactory

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

# 全局记忆服务工厂
memory_factory = MemoryServiceFactory()


@router.post("/public/add", response_model=Dict[str, Any])
async def add_public_knowledge(
    request: KnowledgeAddRequest,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    添加公共知识
    
    向公共知识库添加新的知识内容，支持分类、标签和优先级设置。
    """
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="知识内容不能为空")
        
        logger.info(f"添加公共知识 - 分类: {request.category}, 标题: {request.title}")
        
        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()
        
        # 准备元数据
        metadata = {
            "category": request.category or "general",
            "title": request.title or request.content[:50] + "..." if len(request.content) > 50 else request.content,
            "tags": request.tags or [],
            "priority": request.priority or 1,
            "is_active": True,
            "source": request.source or "manual",
            "author": request.author or "system"
        }
        
        # 添加额外的元数据
        if request.metadata:
            metadata.update(request.metadata)
        
        # 添加知识
        knowledge_id = await public_memory.add_memory(
            content=request.content,
            metadata=metadata
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "公共知识添加成功",
                "data": {
                    "knowledge_id": knowledge_id,
                    "category": metadata["category"],
                    "title": metadata["title"],
                    "created_at": datetime.now().isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加公共知识错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="添加公共知识失败")


@router.post("/private/add", response_model=Dict[str, Any])
async def add_private_knowledge(
    request: KnowledgeAddRequest,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    添加个人知识
    
    向用户的个人知识库添加新的知识内容。
    """
    try:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        if not request.content:
            raise HTTPException(status_code=400, detail="知识内容不能为空")
        
        logger.info(f"添加个人知识 - 用户: {request.user_id}, 分类: {request.category}")
        
        # 获取私有记忆服务
        private_memory = memory_factory.get_private_memory_service(request.user_id)
        
        # 准备元数据
        metadata = {
            "content_type": "knowledge",
            "category": request.category or "general",
            "title": request.title or request.content[:50] + "..." if len(request.content) > 50 else request.content,
            "tags": request.tags or [],
            "priority": request.priority or 1,
            "source": request.source or "manual",
            "author": request.author or request.user_id
        }
        
        # 添加额外的元数据
        if request.metadata:
            metadata.update(request.metadata)
        
        # 添加知识
        knowledge_id = await private_memory.add_memory(
            content=request.content,
            metadata=metadata
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "个人知识添加成功",
                "data": {
                    "knowledge_id": knowledge_id,
                    "user_id": request.user_id,
                    "category": metadata["category"],
                    "title": metadata["title"],
                    "created_at": datetime.now().isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加个人知识错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="添加个人知识失败")


@router.post("/search", response_model=Dict[str, Any])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    搜索知识库
    
    使用语义搜索在个人知识库和公共知识库中查找相关内容。
    支持向量检索和重排模型优化。
    """
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="搜索查询不能为空")
        
        logger.info(f"搜索知识库 - 查询: {request.query}, 用户: {request.user_id}")
        
        # 准备搜索任务
        search_tasks = []
        
        # 搜索公共知识库
        if request.search_public:
            public_memory = memory_factory.get_public_memory_service()
            search_tasks.append(("public", public_memory.retrieve_memories(request.query, limit=request.limit or 5)))
        
        # 搜索个人知识库
        if request.search_private and request.user_id:
            private_memory = memory_factory.get_private_memory_service(request.user_id)
            search_tasks.append(("private", private_memory.retrieve_memories(request.query, limit=request.limit or 5)))
        
        # 并行执行搜索
        results = []
        if search_tasks:
            search_results = await asyncio.gather(
                *[task[1] for task in search_tasks],
                return_exceptions=True
            )
            
            # 处理搜索结果
            for i, (source_type, result) in enumerate(zip([task[0] for task in search_tasks], search_results)):
                if not isinstance(result, Exception):
                    for memory in result:
                        results.append({
                            "id": memory.id,
                            "content": memory.content,
                            "source": source_type,
                            "category": memory.metadata.get("category", ""),
                            "title": memory.metadata.get("title", ""),
                            "tags": memory.metadata.get("tags", []),
                            "priority": memory.metadata.get("priority", 1),
                            "relevance_score": memory.metadata.get("relevance_score", 0),
                            "similarity_score": memory.metadata.get("similarity_score", 0),
                            "created_at": memory.created_at.isoformat() if memory.created_at else None,
                            "metadata": memory.metadata
                        })
                else:
                    logger.warning(f"搜索{source_type}知识库失败: {result}")
        
        # 按相关性排序
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # 限制返回数量
        final_limit = request.limit or 10
        results = results[:final_limit]
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "知识搜索成功",
                "data": {
                    "query": request.query,
                    "total_count": len(results),
                    "search_public": request.search_public,
                    "search_private": request.search_private,
                    "results": results
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索知识库错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="搜索知识库失败")


@router.get("/public/categories", response_model=Dict[str, Any])
async def get_public_categories(
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    获取公共知识库分类列表
    
    返回公共知识库中所有可用的分类。
    """
    try:
        logger.info("获取公共知识库分类列表")
        
        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()
        
        # 获取所有分类
        categories = await public_memory.get_all_categories()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取分类列表成功",
                "data": {
                    "categories": categories,
                    "count": len(categories)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取公共知识库分类错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取分类列表失败")


@router.get("/public/stats", response_model=Dict[str, Any])
async def get_public_knowledge_stats(
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    获取公共知识库统计信息
    
    返回公共知识库的统计数据，包括总数、分类分布等。
    """
    try:
        logger.info("获取公共知识库统计信息")
        
        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()
        
        # 获取统计信息
        stats = await public_memory.get_knowledge_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取统计信息成功",
                "data": stats
            }
        )

    except Exception as e:
        logger.error(f"获取公共知识库统计错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get("/public/category/{category}", response_model=Dict[str, Any])
async def get_public_knowledge_by_category(
    category: str,
    limit: int = Query(10, ge=1, le=100),
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    按分类获取公共知识

    获取指定分类下的公共知识内容。
    """
    try:
        logger.info(f"按分类获取公共知识 - 分类: {category}")

        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()

        # 按分类获取知识
        memories = await public_memory.get_by_category(category, limit)

        # 转换为响应格式
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "content": memory.content,
                "category": memory.metadata.get("category", ""),
                "title": memory.metadata.get("title", ""),
                "tags": memory.metadata.get("tags", []),
                "priority": memory.metadata.get("priority", 1),
                "is_active": memory.metadata.get("is_active", True),
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
                "updated_at": memory.updated_at.isoformat() if memory.updated_at else None
            })

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取分类知识成功",
                "data": {
                    "category": category,
                    "total_count": len(results),
                    "results": results
                }
            }
        )

    except Exception as e:
        logger.error(f"按分类获取公共知识错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取分类知识失败")


@router.put("/public/{knowledge_id}", response_model=Dict[str, Any])
async def update_public_knowledge(
    knowledge_id: str,
    request: KnowledgeUpdateRequest,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    更新公共知识

    更新指定ID的公共知识内容或元数据。
    """
    try:
        logger.info(f"更新公共知识 - ID: {knowledge_id}")

        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()

        # 准备更新的元数据
        metadata = {}
        if request.category is not None:
            metadata["category"] = request.category
        if request.title is not None:
            metadata["title"] = request.title
        if request.tags is not None:
            metadata["tags"] = request.tags
        if request.priority is not None:
            metadata["priority"] = request.priority
        if request.is_active is not None:
            metadata["is_active"] = request.is_active
        if request.metadata:
            metadata.update(request.metadata)

        # 更新知识
        success = await public_memory.update_memory(
            memory_id=knowledge_id,
            content=request.content,
            metadata=metadata if metadata else None
        )

        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "公共知识更新成功",
                    "data": {
                        "knowledge_id": knowledge_id,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
        else:
            raise HTTPException(status_code=404, detail="知识不存在或更新失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新公共知识错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新公共知识失败")


@router.delete("/public/{knowledge_id}", response_model=Dict[str, Any])
async def delete_public_knowledge(
    knowledge_id: str,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    删除公共知识

    删除指定ID的公共知识。
    """
    try:
        logger.info(f"删除公共知识 - ID: {knowledge_id}")

        # 获取公共记忆服务
        public_memory = memory_factory.get_public_memory_service()

        # 删除知识
        success = await public_memory.delete_memory(knowledge_id)

        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "公共知识删除成功",
                    "data": {
                        "knowledge_id": knowledge_id,
                        "deleted_at": datetime.now().isoformat()
                    }
                }
            )
        else:
            raise HTTPException(status_code=404, detail="知识不存在或删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除公共知识错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除公共知识失败")
