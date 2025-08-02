"""
智能体管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.agent import Agent, AgentTemplate, AgentType, AgentStatus
from app.models.user import User
from app.schemas.agent import (
    AgentCreate, 
    AgentResponse, 
    AgentUpdate,
    AgentTemplateResponse
)

router = APIRouter()


@router.get("/debug")
async def debug_auth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    调试认证信息
    """
    # 测试数据库查询
    try:
        agent_count = db.query(Agent).count()
        user_agents = db.query(Agent).filter(Agent.owner_id == current_user.id).count()
        public_agents = db.query(Agent).filter(Agent.is_public == True).count()

        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "total_agents": agent_count,
            "user_agents": user_agents,
            "public_agents": public_agents,
            "message": "Authentication and database working correctly"
        }
    except Exception as e:
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "error": str(e),
            "message": "Authentication working but database error"
        }


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建智能体
    """
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        avatar_url=agent_data.avatar_url,
        type=agent_data.type,
        config=agent_data.config,
        prompt_template=agent_data.prompt_template,
        model_name=agent_data.model_name,
        temperature=str(agent_data.temperature) if agent_data.temperature else "0.7",
        max_tokens=str(agent_data.max_tokens) if agent_data.max_tokens else "2000",
        owner_id=current_user.id,
        knowledge_base_ids=agent_data.knowledge_base_ids,
        is_public=agent_data.is_public or False
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent


@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    skip: int = 0,
    limit: int = 20,
    type: Optional[AgentType] = None,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取智能体列表
    """
    query = db.query(Agent).filter(
        (Agent.owner_id == current_user.id) | (Agent.is_public == True)
    )

    if type:
        query = query.filter(Agent.type == type)

    if is_public is not None:
        query = query.filter(Agent.is_public == is_public)

    if search:
        query = query.filter(
            (Agent.name.contains(search)) |
            (Agent.description.contains(search))
        )

    agents = query.filter(Agent.is_active == True).order_by(
        Agent.updated_at.desc()
    ).offset(skip).limit(limit).all()

    return agents


@router.get("/my", response_model=List[AgentResponse])
async def get_my_agents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取我的智能体列表
    """
    agents = db.query(Agent).filter(
        Agent.owner_id == current_user.id,
        Agent.is_active == True
    ).order_by(Agent.updated_at.desc()).offset(skip).limit(limit).all()
    
    return agents


@router.get("/templates", response_model=List[AgentTemplateResponse])
async def get_agent_templates(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取智能体模板列表
    """
    query = db.query(AgentTemplate).filter(AgentTemplate.is_active == True)
    
    if category:
        query = query.filter(AgentTemplate.category == category)
    
    templates = query.order_by(
        AgentTemplate.is_featured.desc(),
        AgentTemplate.sort_order.asc(),
        AgentTemplate.use_count.desc()
    ).offset(skip).limit(limit).all()
    
    return templates


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定智能体详情
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 检查权限：公开的智能体或者是自己的智能体
    if not agent.is_public and agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新智能体
    """
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在或权限不足"
        )
    
    # 更新智能体信息
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["temperature", "max_tokens"] and value is not None:
            setattr(agent, field, str(value))
        else:
            setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除智能体（软删除）
    """
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在或权限不足"
        )
    
    # 软删除
    agent.is_active = False
    db.commit()
    
    return {"message": "智能体删除成功"}


@router.post("/{agent_id}/clone", response_model=AgentResponse)
async def clone_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    克隆智能体
    """
    original_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not original_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 检查权限：公开的智能体或者是自己的智能体
    if not original_agent.is_public and original_agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 创建克隆的智能体
    cloned_agent = Agent(
        name=f"{original_agent.name} (副本)",
        description=original_agent.description,
        avatar_url=original_agent.avatar_url,
        type=original_agent.type,
        config=original_agent.config,
        prompt_template=original_agent.prompt_template,
        model_name=original_agent.model_name,
        temperature=original_agent.temperature,
        max_tokens=original_agent.max_tokens,
        owner_id=current_user.id,
        knowledge_base_ids=original_agent.knowledge_base_ids,
        is_public=False  # 克隆的智能体默认为私有
    )
    
    db.add(cloned_agent)
    db.commit()
    db.refresh(cloned_agent)
    
    return cloned_agent


@router.post("/{agent_id}/like")
async def like_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    点赞智能体
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体不存在"
        )
    
    # 增加点赞数
    current_likes = int(agent.like_count) if agent.like_count else 0
    agent.like_count = str(current_likes + 1)
    db.commit()
    
    return {"message": "点赞成功", "like_count": agent.like_count}


@router.post("/templates/{template_id}/create", response_model=AgentResponse)
async def create_agent_from_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从模板创建智能体
    """
    template = db.query(AgentTemplate).filter(
        AgentTemplate.id == template_id,
        AgentTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 从模板创建智能体
    agent = Agent(
        name=template.name,
        description=template.description,
        avatar_url=template.avatar_url,
        type=AgentType.CUSTOM,  # 从模板创建的默认为自定义类型
        config=template.template_config,
        prompt_template=template.prompt_template,
        owner_id=current_user.id,
        is_public=False
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    # 增加模板使用次数
    current_use_count = int(template.use_count) if template.use_count else 0
    template.use_count = str(current_use_count + 1)
    db.commit()
    
    return agent
