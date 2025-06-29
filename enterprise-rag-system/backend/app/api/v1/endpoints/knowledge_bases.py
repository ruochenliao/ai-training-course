"""
知识库管理API端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core import get_current_user, PermissionChecker
from app.core.resource_permissions import require_knowledge_base_access, get_knowledge_base_filter
from app.core.permission_audit import audit_resource_access
from app.models import KnowledgeBase
from app.models import User

router = APIRouter()

# 权限检查器
require_kb_read = PermissionChecker("knowledge_base:read")
require_kb_write = PermissionChecker("knowledge_base:write")
require_kb_delete = PermissionChecker("knowledge_base:delete")
require_kb_manage = PermissionChecker("knowledge_base:manage")


@router.get("/", summary="获取知识库列表")
async def get_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    knowledge_type: str = Query(None, description="知识库类型"),
    current_user: User = Depends(require_kb_read)
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
    
    # 转换为响应格式，手动构建避免序列化问题
    kb_list = []
    for kb in knowledge_bases:
        kb_dict = {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "knowledge_type": kb.knowledge_type,
            "visibility": kb.visibility,
            "owner_id": kb.owner_id,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None
        }
        kb_list.append(kb_dict)

    return {
        "items": kb_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.post("/", summary="创建知识库")
async def create_knowledge_base(
    kb_data: dict,
    current_user: User = Depends(require_kb_write)
) -> Any:
    """
    创建知识库
    """
    # 提取参数
    name = kb_data.get("name")
    description = kb_data.get("description")
    is_public = kb_data.get("is_public", False)

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="知识库名称不能为空"
        )

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
        knowledge_type="general",
        visibility="public" if is_public else "private",
        owner_id=current_user.id
    )

    # 手动构建响应，避免序列化问题
    result = {
        "id": knowledge_base.id,
        "name": knowledge_base.name,
        "description": knowledge_base.description,
        "knowledge_type": knowledge_base.knowledge_type,
        "visibility": knowledge_base.visibility,
        "owner_id": knowledge_base.owner_id,
        "created_at": knowledge_base.created_at.isoformat() if knowledge_base.created_at else None,
        "updated_at": knowledge_base.updated_at.isoformat() if knowledge_base.updated_at else None
    }

    return result


@router.get("/{kb_id}", summary="获取知识库详情")
@require_knowledge_base_access("kb_id", "knowledge_base:read")
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

    # 权限检查已由装饰器处理
    # 记录审计日志
    audit_resource_access(
        user_id=current_user.id,
        username=current_user.username,
        resource_type="KnowledgeBase",
        resource_id=str(kb_id),
        action="read",
        success=True
    )
    
    # 手动构建响应，避免序列化问题
    result = {
        "id": knowledge_base.id,
        "name": knowledge_base.name,
        "description": knowledge_base.description,
        "knowledge_type": knowledge_base.knowledge_type,
        "visibility": knowledge_base.visibility,
        "owner_id": knowledge_base.owner_id,
        "created_at": knowledge_base.created_at.isoformat() if knowledge_base.created_at else None,
        "updated_at": knowledge_base.updated_at.isoformat() if knowledge_base.updated_at else None
    }

    return result


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
    
    # 手动构建响应，避免序列化问题
    result = {
        "id": knowledge_base.id,
        "name": knowledge_base.name,
        "description": knowledge_base.description,
        "knowledge_type": knowledge_base.knowledge_type,
        "visibility": knowledge_base.visibility,
        "owner_id": knowledge_base.owner_id,
        "created_at": knowledge_base.created_at.isoformat() if knowledge_base.created_at else None,
        "updated_at": knowledge_base.updated_at.isoformat() if knowledge_base.updated_at else None
    }

    return result


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
