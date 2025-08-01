"""
知识库搜索API路由
"""

from fastapi import APIRouter, HTTPException

from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.knowledge import KnowledgeBase
from app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult
)
from app.services.unified_vector_service import search_multiple_knowledge_bases, search_knowledge_base

router = APIRouter()


@router.post("/search", summary="搜索知识库内容", response_model=dict)
async def search_knowledge_content(
    request: KnowledgeSearchRequest,
    current_user: User = DependAuth
):
    """
    搜索知识库内容
    
    Args:
        request: 搜索请求参数
        current_user: 当前用户
        
    Returns:
        搜索结果
    """
    try:
        import time
        start_time = time.time()
        
        # 如果没有指定知识库ID，则搜索用户有权限的所有知识库
        if not request.knowledge_base_ids:
            # 获取用户有权限的知识库列表
            accessible_kbs = await KnowledgeBase.filter(
                owner_id=current_user.id,
                is_deleted=False,
                status="active"
            ).all()
            
            # 同时包含公开的知识库
            public_kbs = await KnowledgeBase.filter(
                is_public=True,
                is_deleted=False,
                status="active"
            ).all()
            
            # 合并并去重
            all_kbs = list({kb.id: kb for kb in (accessible_kbs + public_kbs)}.values())
            kb_ids = [kb.id for kb in all_kbs]
        else:
            # 验证用户对指定知识库的访问权限
            kb_ids = []
            for kb_id in request.knowledge_base_ids:
                kb = await KnowledgeBase.get_or_none(id=kb_id)
                if not kb:
                    continue
                
                # 检查权限：用户是所有者或知识库是公开的
                if kb.owner_id == current_user.id or kb.is_public:
                    kb_ids.append(kb_id)
        
        if not kb_ids:
            return {
                "success": True,
                "data": {
                    "query": request.query,
                    "results": [],
                    "total": 0,
                    "took": 0.0
                },
                "msg": "没有可搜索的知识库"
            }
        
        # 执行向量搜索 - 使用新的统一向量服务
        try:
            # 使用统一向量服务进行跨知识库搜索
            vector_results = await search_multiple_knowledge_bases(
                knowledge_base_ids=kb_ids,
                query=request.query,
                limit=request.limit,
                score_threshold=0.3
            )

            # 转换结果格式
            search_results = []
            for result in vector_results:
                search_results.append({
                    "content": result.content,
                    "score": result.score,
                    "file_id": int(result.metadata.get("file_id", 0)),
                    "knowledge_base_id": int(result.metadata.get("knowledge_base_id", 0)),
                    "chunk_index": result.metadata.get("chunk_index", 0),
                    "metadata": result.metadata
                })

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            # 搜索失败，返回空结果
            search_results = []

        # 按分数排序并限制结果数量
        search_results.sort(key=lambda x: x["score"], reverse=True)
        search_results = search_results[:request.limit]
        
        # 转换搜索结果格式
        formatted_results = []
        for result in search_results:
            # 获取文件和知识库信息
            try:
                from app.models.knowledge import KnowledgeFile
                file_obj = await KnowledgeFile.get_or_none(id=result.get("file_id"))
                kb_obj = await KnowledgeBase.get_or_none(id=result.get("knowledge_base_id"))
                
                formatted_result = KnowledgeSearchResult(
                    content=result.get("content", ""),
                    score=result.get("score", 0.0),
                    file_id=result.get("file_id", 0),
                    file_name=file_obj.name if file_obj else "未知文件",
                    knowledge_base_id=result.get("knowledge_base_id", 0),
                    knowledge_base_name=kb_obj.name if kb_obj else "未知知识库",
                    chunk_index=result.get("chunk_index", 0),
                    metadata=result.get("metadata", {})
                )
                formatted_results.append(formatted_result.dict())
            except Exception as e:
                # 如果获取文件或知识库信息失败，仍然返回基本信息
                formatted_result = {
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "file_id": result.get("file_id", 0),
                    "file_name": "未知文件",
                    "knowledge_base_id": result.get("knowledge_base_id", 0),
                    "knowledge_base_name": "未知知识库",
                    "chunk_index": result.get("chunk_index", 0),
                    "metadata": result.get("metadata", {})
                }
                formatted_results.append(formatted_result)
        
        end_time = time.time()
        took = end_time - start_time
        
        response_data = KnowledgeSearchResponse(
            query=request.query,
            results=formatted_results,
            total=len(formatted_results),
            took=took
        )
        
        return {
            "success": True,
            "data": response_data.dict(),
            "msg": f"搜索完成，找到 {len(formatted_results)} 条结果"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/knowledge-bases", summary="获取可搜索的知识库列表", response_model=dict)
async def get_searchable_knowledge_bases(
    current_user: User = DependAuth
):
    """
    获取用户可搜索的知识库列表
    
    Args:
        current_user: 当前用户
        
    Returns:
        知识库列表
    """
    try:
        # 获取用户拥有的知识库
        owned_kbs = await KnowledgeBase.filter(
            owner_id=current_user.id,
            is_deleted=False,
            status="active"
        ).all()
        
        # 获取公开的知识库
        public_kbs = await KnowledgeBase.filter(
            is_public=True,
            is_deleted=False,
            status="active"
        ).exclude(owner_id=current_user.id).all()
        
        # 格式化结果
        owned_list = []
        for kb in owned_kbs:
            owned_list.append({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "knowledge_type": kb.knowledge_type,
                "file_count": kb.file_count,
                "is_owner": True
            })
        
        public_list = []
        for kb in public_kbs:
            public_list.append({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "knowledge_type": kb.knowledge_type,
                "file_count": kb.file_count,
                "is_owner": False
            })
        
        return {
            "success": True,
            "data": {
                "owned": owned_list,
                "public": public_list,
                "total": len(owned_list) + len(public_list)
            },
            "msg": "获取知识库列表成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.post("/similar", summary="相似内容搜索", response_model=dict)
async def search_similar_content(
    content: str,
    knowledge_base_id: int,
    limit: int = 5,
    current_user: User = DependAuth
):
    """
    基于给定内容搜索相似内容
    
    Args:
        content: 参考内容
        knowledge_base_id: 知识库ID
        limit: 返回结果数量
        current_user: 当前用户
        
    Returns:
        相似内容列表
    """
    try:
        # 验证知识库访问权限
        kb = await KnowledgeBase.get_or_none(id=knowledge_base_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        if kb.owner_id != current_user.id and not kb.is_public:
            raise HTTPException(status_code=403, detail="无权限访问该知识库")
        
        # 执行相似内容搜索
        search_results = await search_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            query=content,
            limit=limit
        )
        
        # 格式化结果
        similar_contents = []
        for result in search_results:
            similar_contents.append({
                "content": result.content,
                "score": result.score,
                "file_id": int(result.metadata.get("file_id", 0)),
                "chunk_index": result.metadata.get("chunk_index", 0),
                "metadata": result.metadata
            })
        
        return {
            "success": True,
            "data": {
                "reference_content": content,
                "knowledge_base_id": knowledge_base_id,
                "knowledge_base_name": kb.name,
                "similar_contents": similar_contents,
                "total": len(similar_contents)
            },
            "msg": f"找到 {len(similar_contents)} 条相似内容"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相似内容搜索失败: {str(e)}")


@router.get("/stats", summary="获取搜索统计信息", response_model=dict)
async def get_search_stats(
    current_user: User = DependAuth
):
    """
    获取用户的搜索统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        搜索统计信息
    """
    try:
        # 获取用户可访问的知识库统计
        owned_kbs = await KnowledgeBase.filter(
            owner_id=current_user.id,
            is_deleted=False
        ).all()
        
        public_kbs = await KnowledgeBase.filter(
            is_public=True,
            is_deleted=False
        ).exclude(owner_id=current_user.id).all()
        
        # 计算统计信息
        total_owned_files = sum(kb.file_count for kb in owned_kbs)
        total_public_files = sum(kb.file_count for kb in public_kbs)
        
        stats = {
            "accessible_knowledge_bases": len(owned_kbs) + len(public_kbs),
            "owned_knowledge_bases": len(owned_kbs),
            "public_knowledge_bases": len(public_kbs),
            "total_files": total_owned_files + total_public_files,
            "owned_files": total_owned_files,
            "public_files": total_public_files
        }
        
        return {
            "success": True,
            "data": stats,
            "msg": "获取搜索统计信息成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
