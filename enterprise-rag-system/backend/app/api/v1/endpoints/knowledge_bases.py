"""
知识库管理API端点
"""

from typing import Any

from app.core.security import get_current_user
from app.models.knowledge import KnowledgeBase
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.get("/", summary="获取知识库列表")
async def get_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    knowledge_type: str = Query(None, description="知识库类型"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取知识库列表
    """
    # 构建查询
    query = KnowledgeBase.filter(is_deleted=False)
    
    # 非超级用户只能看到自己的和公开的知识库
    if not current_user.is_superuser:
        query = query.filter(
            owner_id=current_user.id
        ).union(
            KnowledgeBase.filter(visibility="public", is_deleted=False)
        )
    
    if search:
        query = query.filter(name__icontains=search)
    
    if knowledge_type:
        query = query.filter(knowledge_type=knowledge_type)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    knowledge_bases = await query.offset(offset).limit(size).order_by("-created_at")
    
    # 转换为响应格式
    kb_list = []
    for kb in knowledge_bases:
        kb_dict = await kb.to_dict()
        kb_list.append(kb_dict)
    
    return {
        "knowledge_bases": kb_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.post("/", summary="创建知识库")
async def create_knowledge_base(
    name: str,
    description: str = None,
    knowledge_type: str = "general",
    visibility: str = "private",
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建知识库
    """
    # 检查名称是否重复
    existing_kb = await KnowledgeBase.get_or_none(
        name=name, 
        owner_id=current_user.id,
        is_deleted=False
    )
    if existing_kb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="知识库名称已存在"
        )
    
    # 创建知识库
    knowledge_base = await KnowledgeBase.create(
        name=name,
        description=description,
        knowledge_type=knowledge_type,
        visibility=visibility,
        owner_id=current_user.id
    )
    
    return await knowledge_base.to_dict()


@router.get("/{kb_id}", summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取知识库详情
    """
    knowledge_base = await KnowledgeBase.get_or_none(id=kb_id, is_deleted=False)
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查访问权限
    if not current_user.is_superuser:
        if knowledge_base.owner_id != current_user.id and knowledge_base.visibility != "public":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此知识库"
            )
    
    return await knowledge_base.to_dict()


@router.put("/{kb_id}", summary="更新知识库")
async def update_knowledge_base(
    kb_id: int,
    name: str = None,
    description: str = None,
    visibility: str = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新知识库
    """
    knowledge_base = await KnowledgeBase.get_or_none(id=kb_id, is_deleted=False)
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查权限
    if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此知识库"
        )
    
    # 更新字段
    if name is not None:
        knowledge_base.name = name
    if description is not None:
        knowledge_base.description = description
    if visibility is not None:
        knowledge_base.visibility = visibility
    
    await knowledge_base.save()
    
    return await knowledge_base.to_dict()


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除知识库
    """
    knowledge_base = await KnowledgeBase.get_or_none(id=kb_id, is_deleted=False)
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查权限
    if not current_user.is_superuser and knowledge_base.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此知识库"
        )
    
    # 软删除
    await knowledge_base.soft_delete()
    
    return {"message": "知识库已删除"}
