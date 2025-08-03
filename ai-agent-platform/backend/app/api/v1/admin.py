"""
管理员API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.agent import Agent
from app.models.knowledge import KnowledgeBase
from app.models.chat import Conversation, Message
from app.schemas.admin import (
    AdminStatsResponse,
    UserManagementResponse,
    SystemHealthResponse
)

router = APIRouter()


def verify_admin_permission(current_user_id: str, db: Session):
    """验证管理员权限"""
    user = db.query(User).filter(User.id == int(current_user_id)).first()
    if not user or not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return user


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取管理员统计数据
    """
    verify_admin_permission(current_user_id, db)
    
    # 用户统计
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    new_users_today = db.query(User).filter(
        func.date(User.created_at) == datetime.utcnow().date()
    ).count()
    
    # 智能体统计
    total_agents = db.query(Agent).count()
    public_agents = db.query(Agent).filter(Agent.is_public == True).count()
    active_agents = db.query(Agent).filter(Agent.is_active == True).count()
    
    # 知识库统计
    total_knowledge_bases = db.query(KnowledgeBase).count()
    total_documents = 0  # 暂时设为0，因为Document模型可能不存在
    
    # 对话统计
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    conversations_today = db.query(Conversation).filter(
        func.date(Conversation.created_at) == datetime.utcnow().date()
    ).count()
    
    # 最近7天的对话趋势
    conversation_trend = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = db.query(Conversation).filter(
            func.date(Conversation.created_at) == date
        ).count()
        conversation_trend.append({
            "date": date.isoformat(),
            "count": count
        })
    
    return {
        "user_stats": {
            "total": total_users,
            "active": active_users,
            "new_today": new_users_today
        },
        "agent_stats": {
            "total": total_agents,
            "public": public_agents,
            "active": active_agents
        },
        "knowledge_stats": {
            "total_knowledge_bases": total_knowledge_bases,
            "total_documents": total_documents
        },
        "conversation_stats": {
            "total": total_conversations,
            "total_messages": total_messages,
            "today": conversations_today,
            "trend": conversation_trend
        }
    }


@router.get("/users", response_model=List[UserManagementResponse])
async def get_users_management(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取用户管理列表
    """
    verify_admin_permission(current_user_id, db)
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.full_name.contains(search))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # 统计用户数据
        agent_count = db.query(Agent).filter(Agent.owner_id == user.id).count()
        kb_count = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).count()
        conversation_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
        
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "agent_count": agent_count,
            "knowledge_base_count": kb_count,
            "conversation_count": conversation_count
        })
    
    return result


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    更新用户状态
    """
    verify_admin_permission(current_user_id, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能禁用自己
    if user_id == int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的状态"
        )
    
    user.is_active = is_active
    db.commit()
    
    return {
        "message": f"用户状态已更新为{'激活' if is_active else '禁用'}",
        "user_id": user_id,
        "is_active": is_active
    }


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取系统健康状态
    """
    verify_admin_permission(current_user_id, db)
    
    try:
        # 数据库连接测试
        db.execute("SELECT 1")
        db_status = "healthy"
        db_message = "数据库连接正常"
    except Exception as e:
        db_status = "error"
        db_message = f"数据库连接异常: {str(e)}"
    
    # 磁盘空间检查（简化版）
    import shutil
    try:
        disk_usage = shutil.disk_usage("/")
        disk_free_gb = disk_usage.free / (1024**3)
        disk_total_gb = disk_usage.total / (1024**3)
        disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        if disk_usage_percent > 90:
            disk_status = "warning"
            disk_message = f"磁盘使用率过高: {disk_usage_percent:.1f}%"
        elif disk_usage_percent > 95:
            disk_status = "error"
            disk_message = f"磁盘空间严重不足: {disk_usage_percent:.1f}%"
        else:
            disk_status = "healthy"
            disk_message = f"磁盘空间充足: {disk_usage_percent:.1f}%"
    except Exception as e:
        disk_status = "error"
        disk_message = f"磁盘检查失败: {str(e)}"
        disk_free_gb = 0
        disk_total_gb = 0
        disk_usage_percent = 0
    
    # 内存使用检查（简化版）
    import psutil
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        
        if memory_usage_percent > 90:
            memory_status = "warning"
            memory_message = f"内存使用率过高: {memory_usage_percent:.1f}%"
        elif memory_usage_percent > 95:
            memory_status = "error"
            memory_message = f"内存严重不足: {memory_usage_percent:.1f}%"
        else:
            memory_status = "healthy"
            memory_message = f"内存使用正常: {memory_usage_percent:.1f}%"
    except Exception as e:
        memory_status = "error"
        memory_message = f"内存检查失败: {str(e)}"
        memory_usage_percent = 0
    
    # 整体健康状态
    if db_status == "error" or disk_status == "error" or memory_status == "error":
        overall_status = "error"
    elif db_status == "warning" or disk_status == "warning" or memory_status == "warning":
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    return {
        "overall_status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {
                "status": db_status,
                "message": db_message
            },
            "disk": {
                "status": disk_status,
                "message": disk_message,
                "free_gb": disk_free_gb,
                "total_gb": disk_total_gb,
                "usage_percent": disk_usage_percent
            },
            "memory": {
                "status": memory_status,
                "message": memory_message,
                "usage_percent": memory_usage_percent
            }
        }
    }


@router.delete("/cleanup/old-data")
async def cleanup_old_data(
    days: int = 30,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    清理旧数据
    """
    verify_admin_permission(current_user_id, db)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 删除旧的对话（非活跃用户的）
    old_conversations = db.query(Conversation).filter(
        Conversation.updated_at < cutoff_date,
        Conversation.status != "active"
    ).count()
    
    db.query(Conversation).filter(
        Conversation.updated_at < cutoff_date,
        Conversation.status != "active"
    ).delete()
    
    db.commit()
    
    return {
        "message": f"清理完成，删除了 {old_conversations} 个旧对话",
        "cutoff_date": cutoff_date.isoformat(),
        "days": days
    }
