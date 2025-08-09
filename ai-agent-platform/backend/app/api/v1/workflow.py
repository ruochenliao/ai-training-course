"""
# Copyright (c) 2025 左岚. All rights reserved.

工作流API端点

提供工作流管理的REST API接口。
"""

# # Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

# # Third-party imports
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# # Local application imports
from app.agents.base import agent_registry
from app.agents.workflow import WorkflowStatus, workflow_manager
from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter()


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    user_request: str
    context: Optional[Dict[str, Any]] = {}


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    status: str
    user_request: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class AgentStatusResponse(BaseModel):
    """智能体状态响应"""
    name: str
    description: str
    is_active: bool
    model: str
    capabilities: List[str]


@router.on_event("startup")
async def startup_event():
    """启动时初始化工作流管理器"""
    await workflow_manager.initialize()


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的工作流
    """
    try:
        # 生成工作流ID
        workflow_id = str(uuid.uuid4())
        
        # 创建工作流
        workflow = await workflow_manager.create_workflow(
            workflow_id=workflow_id,
            user_request=request.user_request,
            user_id=str(current_user.id)
        )
        
        # 设置上下文
        for key, value in request.context.items():
            workflow.context.set_variable(key, value)
        
        # 在后台启动工作流
        background_tasks.add_task(workflow.start)
        
        return WorkflowResponse(
            workflow_id=workflow.id,
            status=workflow.status.value,
            user_request=workflow.user_request,
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
            error_message=workflow.error_message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工作流失败: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的工作流列表
    """
    try:
        workflows = workflow_manager.list_workflows()
        
        # 过滤当前用户的工作流
        user_workflows = [
            workflow for workflow in workflows 
            if workflow.user_id == str(current_user.id)
        ]
        
        return [
            WorkflowResponse(
                workflow_id=workflow.id,
                status=workflow.status.value,
                user_request=workflow.user_request,
                created_at=workflow.created_at.isoformat(),
                started_at=workflow.started_at.isoformat() if workflow.started_at else None,
                completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
                error_message=workflow.error_message,
                progress=workflow.get_progress()
            )
            for workflow in user_workflows
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流列表失败: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定工作流的详细信息
    """
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查权限
        if workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此工作流"
            )
        
        return WorkflowResponse(
            workflow_id=workflow.id,
            status=workflow.status.value,
            user_request=workflow.user_request,
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
            error_message=workflow.error_message,
            progress=workflow.get_progress()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流失败: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    暂停工作流
    """
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查权限
        if workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此工作流"
            )
        
        workflow.pause()
        
        return {"message": "工作流已暂停"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停工作流失败: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    恢复工作流
    """
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查权限
        if workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此工作流"
            )
        
        workflow.resume()
        
        return {"message": "工作流已恢复"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复工作流失败: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消工作流
    """
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查权限
        if workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此工作流"
            )
        
        workflow.cancel()
        
        return {"message": "工作流已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消工作流失败: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除工作流
    """
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查权限
        if workflow.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此工作流"
            )
        
        # 如果工作流正在运行，先取消
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.cancel()
        
        # 删除工作流
        workflow_manager.remove_workflow(workflow_id)
        
        return {"message": "工作流已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工作流失败: {str(e)}"
        )


@router.get("/agents", response_model=List[AgentStatusResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有智能体状态
    """
    try:
        agents = agent_registry.list_agents()
        
        return [
            AgentStatusResponse(
                name=agent_name,
                description=agent_registry.get(agent_name).description,
                is_active=agent_registry.get(agent_name).is_active,
                model=agent_registry.get(agent_name).model,
                capabilities=agent_registry.get(agent_name).capabilities
            )
            for agent_name in agents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体列表失败: {str(e)}"
        )
