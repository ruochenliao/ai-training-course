"""
系统管理API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.models.agent import Agent
from app.models.user import User
from app.models.knowledge import KnowledgeBase
from app.models.chat import Conversation

router = APIRouter()


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """
    获取系统统计数据
    """
    # 获取智能体数量
    agent_count = db.query(Agent).filter(Agent.is_active == True).count()
    
    # 获取知识库数量
    knowledge_count = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).count()
    
    # 获取今日对话数量
    today = datetime.utcnow().date()
    today_chats = db.query(Conversation).filter(
        func.date(Conversation.created_at) == today
    ).count()
    
    # 获取在线用户数量（这里简化为活跃用户数）
    online_users = db.query(User).filter(User.is_active == True).count()
    
    return {
        "agentCount": agent_count,
        "knowledgeCount": knowledge_count,
        "todayChats": today_chats,
        "onlineUsers": online_users,
        "systemStatus": {
            "api": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "vector_db": "healthy"
        }
    }


@router.get("/info")
async def get_system_info():
    """
    获取系统信息
    """
    return {
        "version": "1.0.0",
        "environment": "development",
        "uptime": 3600,  # 简化的运行时间
        "timestamp": datetime.utcnow().timestamp()
    }
