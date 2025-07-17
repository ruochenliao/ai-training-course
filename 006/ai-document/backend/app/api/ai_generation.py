"""
统一的AI生成API模块
处理前端所有字段对应内容的生成请求
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.ai_service import ai_service
from app.services.agent_service import agent_service
from app.services.agent_execution_service import agent_execution_service
from app.models.user import User
from app.api.auth import get_current_active_user
from app.schemas.ai_generation import (
    FieldGenerateRequest, FieldGenerateResponse,
    BatchGenerateRequest, BatchGenerateResponse,
    SmartGenerateRequest, SmartGenerateResponse,
    GenerationContext, FieldType
)

router = APIRouter()


@router.post("/field", response_model=FieldGenerateResponse)
async def generate_field_content(
    request: FieldGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成单个字段内容
    支持基于字段类型的智能生成
    """
    try:
        # 根据字段类型选择合适的生成策略
        if request.field_type == FieldType.CONFIGURED:
            # 使用配置的智能体生成
            result = await _generate_with_configured_agent(db, request)
        elif request.field_type == FieldType.SMART:
            # 智能选择智能体生成
            result = await _generate_with_smart_agent(db, request)
        else:
            # 默认生成方式
            result = await _generate_with_default_agent(db, request)
        
        return FieldGenerateResponse(
            success=result["success"],
            content=result.get("content"),
            error=result.get("error"),
            field_key=request.field_key,
            generation_time=result.get("generation_time", 0)
        )
        
    except Exception as e:
        return FieldGenerateResponse(
            success=False,
            error=f"生成失败: {str(e)}",
            field_key=request.field_key
        )


@router.post("/batch", response_model=BatchGenerateResponse)
async def generate_batch_content(
    request: BatchGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    批量生成多个字段内容
    支持并发生成和依赖关系处理
    """
    try:
        results = []
        
        # 按依赖关系排序字段
        sorted_fields = _sort_fields_by_dependency(request.fields)
        
        for field_request in sorted_fields:
            # 更新上下文（包含之前生成的内容）
            field_request.context.update(request.global_context)
            
            # 生成单个字段
            field_result = await generate_field_content(
                field_request, db, current_user
            )
            
            results.append(field_result)
            
            # 如果生成成功，将结果添加到全局上下文
            if field_result.success and field_result.content:
                request.global_context[field_request.field_key] = field_result.content
        
        # 统计成功和失败数量
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        return BatchGenerateResponse(
            success=success_count > 0,
            results=results,
            success_count=success_count,
            total_count=total_count,
            error=None if success_count > 0 else "所有字段生成失败"
        )
        
    except Exception as e:
        return BatchGenerateResponse(
            success=False,
            results=[],
            success_count=0,
            total_count=len(request.fields),
            error=f"批量生成失败: {str(e)}"
        )


@router.post("/smart", response_model=SmartGenerateResponse)
async def smart_generate_content(
    request: SmartGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    智能内容生成
    根据上下文自动选择最佳生成策略和智能体
    """
    try:
        # 分析上下文，确定生成策略
        strategy = await _analyze_generation_strategy(request)
        
        # 根据策略选择智能体
        agent_config = await _select_optimal_agent(db, strategy, request)
        
        # 构建优化的提示词
        optimized_prompt = _build_optimized_prompt(request, strategy)
        
        # 执行生成
        result = await agent_execution_service.execute_agent_by_id(
            db=db,
            agent_id=agent_config.id,
            user_prompt=optimized_prompt,
            context=request.context.dict()
        )
        
        return SmartGenerateResponse(
            success=result["success"],
            content=result.get("content"),
            error=result.get("error"),
            strategy_used=strategy["name"],
            agent_used=agent_config.name,
            confidence_score=strategy.get("confidence", 0.8),
            generation_time=result.get("generation_time", 0)
        )
        
    except Exception as e:
        return SmartGenerateResponse(
            success=False,
            error=f"智能生成失败: {str(e)}",
            strategy_used="unknown",
            agent_used="unknown"
        )


@router.get("/agents/suitable")
async def get_suitable_agents(
    field_type: str,
    content_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取适合特定字段类型和内容类型的智能体列表
    """
    try:
        agents = agent_service.get_agent_configs(db)
        
        # 根据字段类型和内容类型筛选合适的智能体
        suitable_agents = []
        for agent in agents:
            if _is_agent_suitable(agent, field_type, content_type):
                suitable_agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "suitability_score": _calculate_suitability_score(agent, field_type, content_type)
                })
        
        # 按适合度排序
        suitable_agents.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        return {
            "success": True,
            "agents": suitable_agents,
            "total_count": len(suitable_agents)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取适合智能体失败: {str(e)}",
            "agents": [],
            "total_count": 0
        }


# 私有辅助函数

async def _generate_with_configured_agent(db: Session, request: FieldGenerateRequest) -> Dict[str, Any]:
    """使用配置的智能体生成内容"""
    if not request.agent_id:
        raise ValueError("配置模式下必须指定智能体ID")
    
    # 构建提示词
    prompt = _build_field_prompt(request)
    
    # 执行生成
    return await agent_execution_service.execute_agent_by_id(
        db=db,
        agent_id=request.agent_id,
        user_prompt=prompt,
        context=request.context
    )


async def _generate_with_smart_agent(db: Session, request: FieldGenerateRequest) -> Dict[str, Any]:
    """智能选择智能体生成内容"""
    # 获取所有可用智能体
    agents = agent_service.get_agent_configs(db)
    
    # 选择最适合的智能体
    best_agent = _select_best_agent_for_field(agents, request)
    
    if not best_agent:
        raise ValueError("未找到适合的智能体")
    
    # 构建提示词
    prompt = _build_field_prompt(request)
    
    # 执行生成
    return await agent_execution_service.execute_agent_by_id(
        db=db,
        agent_id=best_agent.id,
        user_prompt=prompt,
        context=request.context
    )


async def _generate_with_default_agent(db: Session, request: FieldGenerateRequest) -> Dict[str, Any]:
    """使用默认智能体生成内容"""
    # 获取默认智能体（通常是通用写作智能体）
    agents = agent_service.get_agent_configs(db)
    default_agent = next(
        (a for a in agents if "写作" in a.name or "生成" in a.name),
        agents[0] if agents else None
    )
    
    if not default_agent:
        raise ValueError("未找到可用的智能体")
    
    # 构建提示词
    prompt = _build_field_prompt(request)
    
    # 执行生成
    return await agent_execution_service.execute_agent_by_id(
        db=db,
        agent_id=default_agent.id,
        user_prompt=prompt,
        context=request.context
    )


def _build_field_prompt(request: FieldGenerateRequest) -> str:
    """构建字段生成提示词"""
    context = request.context
    
    # 基础提示词
    prompt = f"请为一份{context.get('category', '文档')}类型的{context.get('type', '内容')}生成{request.field_name}。\n\n"
    
    # 添加上下文信息
    if context.get('title') and request.field_key != 'title':
        prompt += f"标题：{context['title']}\n"
    if context.get('keywords') and request.field_key != 'keywords':
        prompt += f"关键词：{context['keywords']}\n"
    if context.get('content') and request.field_key != 'content':
        prompt += f"主要内容：{context['content']}\n"
    
    # 添加用户输入
    if request.user_input:
        prompt += f"\n用户要求：{request.user_input}\n"
    
    # 添加生成要求
    prompt += f"\n请生成专业、准确的{request.field_name}内容。"
    
    return prompt


def _select_best_agent_for_field(agents: List, request: FieldGenerateRequest):
    """为字段选择最佳智能体"""
    # 简单的选择逻辑，可以根据需要扩展
    field_key = request.field_key.lower()
    
    # 优先级匹配
    for agent in agents:
        agent_name = agent.name.lower()
        if field_key in agent_name or request.field_name in agent_name:
            return agent
    
    # 通用匹配
    for agent in agents:
        agent_name = agent.name.lower()
        if any(keyword in agent_name for keyword in ['写作', '生成', '标题', '内容']):
            return agent
    
    # 返回第一个可用的智能体
    return agents[0] if agents else None


def _sort_fields_by_dependency(fields: List[FieldGenerateRequest]) -> List[FieldGenerateRequest]:
    """按依赖关系排序字段"""
    # 简单的排序逻辑：标题 -> 关键词 -> 内容 -> 其他
    priority_order = {'title': 1, 'keywords': 2, 'content': 3}
    
    return sorted(fields, key=lambda f: priority_order.get(f.field_key, 999))


async def _analyze_generation_strategy(request: SmartGenerateRequest) -> Dict[str, Any]:
    """分析生成策略"""
    # 这里可以实现复杂的策略分析逻辑
    return {
        "name": "smart_generation",
        "confidence": 0.8,
        "approach": "context_aware"
    }


async def _select_optimal_agent(db: Session, strategy: Dict[str, Any], request: SmartGenerateRequest):
    """选择最优智能体"""
    agents = agent_service.get_agent_configs(db)
    # 简单选择逻辑，可以根据策略优化
    return agents[0] if agents else None


def _build_optimized_prompt(request: SmartGenerateRequest, strategy: Dict[str, Any]) -> str:
    """构建优化的提示词"""
    return f"根据以下上下文生成内容：\n{request.prompt}\n\n上下文信息：{request.context.dict()}"


def _is_agent_suitable(agent, field_type: str, content_type: str) -> bool:
    """判断智能体是否适合特定字段和内容类型"""
    # 简单的适合性判断逻辑
    return True


def _calculate_suitability_score(agent, field_type: str, content_type: str) -> float:
    """计算智能体适合度分数"""
    # 简单的评分逻辑
    score = 0.5
    
    agent_name = agent.name.lower()
    if field_type.lower() in agent_name:
        score += 0.3
    if content_type.lower() in agent_name:
        score += 0.2
    
    return min(score, 1.0)
