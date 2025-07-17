"""
智能体配置API路由
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.agent_service import agent_service
from app.services.agent_execution_service import agent_execution_service
from app.schemas.agent_config import (
    AgentConfig, AgentConfigCreate, AgentConfigUpdate,
    AgentTool, AgentToolCreate, AgentToolUpdate,
    AgentModel, AgentModelCreate, AgentModelUpdate,
    WritingFieldConfig, WritingFieldConfigUpdate,
    AIGenerateRequest, AIGenerateDirectRequest, AIGenerateResponse
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/agent-configs", tags=["智能体配置"])


# 智能体配置管理
@router.get("/agents", response_model=List[AgentConfig])
def get_agent_configs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体配置列表"""
    return agent_service.get_agent_configs(db, skip=skip, limit=limit)


@router.get("/agents/{agent_id}", response_model=AgentConfig)
def get_agent_config(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个智能体配置"""
    agent = agent_service.get_agent_config(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体配置不存在"
        )
    return agent


@router.post("/agents", response_model=AgentConfig)
def create_agent_config(
    agent_data: AgentConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建智能体配置"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return agent_service.create_agent_config(db, agent_data)


@router.put("/agents/{agent_id}", response_model=AgentConfig)
def update_agent_config(
    agent_id: int,
    agent_data: AgentConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新智能体配置"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    agent = agent_service.update_agent_config(db, agent_id, agent_data)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体配置不存在"
        )
    return agent


@router.delete("/agents/{agent_id}")
def delete_agent_config(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除智能体配置"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = agent_service.delete_agent_config(db, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="智能体配置不存在"
        )
    return {"message": "删除成功"}


# 工具管理
@router.get("/tools", response_model=List[AgentTool])
def get_agent_tools(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体工具列表"""
    return agent_service.get_agent_tools(db, skip=skip, limit=limit)


@router.post("/tools", response_model=AgentTool)
def create_agent_tool(
    tool_data: AgentToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建智能体工具"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return agent_service.create_agent_tool(db, tool_data)


# 模型管理
@router.get("/models", response_model=List[AgentModel])
def get_agent_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体模型列表"""
    return agent_service.get_agent_models(db, skip=skip, limit=limit)


@router.post("/models", response_model=AgentModel)
def create_agent_model(
    model_data: AgentModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建智能体模型"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return agent_service.create_agent_model(db, model_data)


# 字段配置管理
@router.get("/fields/scenario/{scenario_config_id}", response_model=List[WritingFieldConfig])
def get_field_configs_by_scenario(
    scenario_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取写作场景的字段配置"""
    return agent_service.get_field_configs_by_scenario(db, scenario_config_id)


@router.put("/fields/{field_id}", response_model=WritingFieldConfig)
def update_field_config(
    field_id: int,
    field_data: WritingFieldConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新字段配置"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    field = agent_service.update_field_config(db, field_id, field_data)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="字段配置不存在"
        )
    return field


@router.post("/fields/{field_id}/assign-agent/{agent_id}")
def assign_agent_to_field(
    field_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为字段分配智能体"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = agent_service.assign_agent_to_field(db, field_id, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="字段或智能体不存在"
        )
    return {"message": "分配成功"}


@router.delete("/fields/{field_id}/agent")
def remove_agent_from_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除字段的智能体分配"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = agent_service.remove_agent_from_field(db, field_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="字段不存在"
        )
    return {"message": "移除成功"}


# AI生成相关API
@router.post("/ai-generate", response_model=AIGenerateResponse)
async def ai_generate_content(
    request: AIGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成内容"""
    try:
        # 根据模板类型ID和字段键名查找字段配置
        from app.models.template import WritingScenarioConfig, WritingFieldConfig

        # 获取写作场景配置
        scenario_config = db.query(WritingScenarioConfig).filter(
            WritingScenarioConfig.template_type_id == request.template_type_id
        ).first()

        if not scenario_config:
            return AIGenerateResponse(
                success=False,
                error="未找到写作场景配置"
            )

        # 查找对应的字段配置
        field_config = db.query(WritingFieldConfig).filter(
            WritingFieldConfig.scenario_config_id == scenario_config.id,
            WritingFieldConfig.field_key == request.field_key
        ).first()

        if not field_config:
            return AIGenerateResponse(
                success=False,
                error="未找到字段配置"
            )

        if not field_config.ai_enabled or not field_config.agent_config_id:
            return AIGenerateResponse(
                success=False,
                error="该字段未启用AI生成或未配置智能体"
            )

        # 执行智能体
        result = await agent_execution_service.execute_agent_for_field(
            db=db,
            field_id=field_config.id,
            context=request.context,
            user_input=request.user_input
        )

        return AIGenerateResponse(
            success=result["success"],
            content=result.get("content"),
            error=result.get("error")
        )

    except Exception as e:
        return AIGenerateResponse(
            success=False,
            error=f"生成失败: {str(e)}"
        )


@router.post("/ai-generate-direct/{agent_id}", response_model=AIGenerateResponse)
async def ai_generate_direct(
    agent_id: int,
    request: AIGenerateDirectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """直接通过智能体ID生成内容"""
    try:
        result = await agent_execution_service.execute_agent_by_id(
            db=db,
            agent_id=agent_id,
            user_prompt=request.user_prompt,
            context=request.context
        )

        return AIGenerateResponse(
            success=result["success"],
            content=result.get("content"),
            error=result.get("error")
        )

    except Exception as e:
        return AIGenerateResponse(
            success=False,
            error=f"生成失败: {str(e)}"
        )
