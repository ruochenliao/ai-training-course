from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.ai import AIRequest, AIResponse, AISession
from app.schemas.user import User
from app.models.ai_session import AISession as AISessionModel
from app.services.ai_service import ai_service
from app.utils.agent_utils import agent_manager
from app.api.deps import get_current_active_user
import json

router = APIRouter()


@router.post("/generate", response_model=AIResponse)
def create_ai_session(
    ai_request: AIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建AI生成会话"""
    try:
        session = ai_service.create_session(db=db, user_id=current_user.id, ai_request=ai_request)
        return AIResponse(
            session_id=session.session_id,
            status=session.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{session_id}")
async def stream_ai_response(
    session_id: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """流式获取AI响应"""
    # 验证token
    from app.services.auth import verify_token, get_user_by_username
    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    current_user = get_user_by_username(db, token_data.username)
    if not current_user:
        raise HTTPException(status_code=401, detail="User not found")

    # 验证会话是否属于当前用户
    session = db.query(AISessionModel).filter(
        AISessionModel.session_id == session_id,
        AISessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def generate():
        try:
            async for response in ai_service.generate_stream_response(
                db=db,
                session_id=session_id,
                ai_type=session.ai_type,
                prompt=session.prompt,
                context=session.session_metadata.get("context") if session.session_metadata else None
            ):
                yield f"data: {json.dumps(response.dict())}\n\n"
        except Exception as e:
            error_response = {
                "session_id": session_id,
                "content": "",
                "is_complete": True,
                "error": str(e)
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("/session/{session_id}", response_model=AISession)
def get_ai_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取AI会话信息"""
    session = db.query(AISessionModel).filter(
        AISessionModel.session_id == session_id,
        AISessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.post("/collaborative", response_model=AIResponse)
def create_collaborative_session(
    ai_request: AIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建协作写作会话"""
    try:
        # 强制设置为协作模式
        ai_request.ai_type = "ai_collaborative"
        session = ai_service.create_session(db=db, user_id=current_user.id, ai_request=ai_request)
        return AIResponse(
            session_id=session.session_id,
            status=session.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review", response_model=AIResponse)
def create_review_session(
    ai_request: AIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建专家评审会话"""
    try:
        # 强制设置为评审模式
        ai_request.ai_type = "ai_review"
        session = ai_service.create_session(db=db, user_id=current_user.id, ai_request=ai_request)
        return AIResponse(
            session_id=session.session_id,
            status=session.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
def get_available_agents():
    """获取可用的智能体列表"""
    return {
        "agents": agent_manager.get_available_agents(),
        "collaboration_modes": agent_manager.get_collaboration_modes()
    }


@router.post("/suggest-strategy")
def suggest_collaboration_strategy(
    request: dict,
    current_user: User = Depends(get_current_active_user)
):
    """建议协作策略"""
    prompt = request.get("prompt", "")
    task_type = request.get("ai_type", "ai_writer")
    context = request.get("context")

    # 评估任务复杂度
    complexity = agent_manager.get_task_complexity_score(prompt, context)

    # 获取建议策略
    strategy = agent_manager.suggest_collaboration_strategy(task_type, complexity, prompt)

    # 获取推荐智能体
    recommended_agents = agent_manager.get_recommended_agents_for_task(prompt)

    return {
        "strategy": strategy,
        "recommended_agents": recommended_agents,
        "complexity_score": complexity
    }


@router.post("/writing-wizard", response_model=AIResponse)
def create_writing_wizard_session(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建写作向导会话"""
    try:
        scenario = request.get("scenario", {})

        # 构建专门的写作提示
        prompt = build_writing_prompt(scenario)

        # 根据写作类型选择合适的AI类型
        ai_type = determine_ai_type_for_writing(scenario)

        # 创建AI请求
        ai_request = AIRequest(
            ai_type=ai_type,
            prompt=prompt,
            context=scenario.get("contentReference") or scenario.get("dataReference"),
            metadata={
                "writing_wizard": True,
                "scenario": scenario,
                "category": scenario.get("category"),
                "type": scenario.get("type")
            }
        )

        session = ai_service.create_session(db=db, user_id=current_user.id, ai_request=ai_request)
        return AIResponse(
            session_id=session.session_id,
            status=session.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def build_writing_prompt(scenario: dict) -> str:
    """构建写作向导的提示词"""
    category = scenario.get("category", "")
    doc_type = scenario.get("type", "")
    title = scenario.get("title", "")
    keywords = scenario.get("keywords", "")
    reason = scenario.get("reason", "")
    content = scenario.get("content", "")
    purpose = scenario.get("purpose", "")

    prompt = f"请帮我写一份{category}类型的{doc_type}文档。\n\n"

    if title:
        prompt += f"标题：{title}\n"

    if keywords:
        prompt += f"关键词：{keywords}\n"

    if reason:
        prompt += f"表彰原因：{reason}\n"

    if content:
        prompt += f"表彰内容：{content}\n"

    if purpose:
        prompt += f"表彰目的：{purpose}\n"

    prompt += "\n请根据以上信息，生成一份专业、规范、结构完整的文档。"
    prompt += "文档应该包含适当的格式、标题层次和专业的语言表达。"

    return prompt


def determine_ai_type_for_writing(scenario: dict) -> str:
    """根据写作场景确定AI类型"""
    category = scenario.get("category", "")
    doc_type = scenario.get("type", "")

    # 根据文档类型选择合适的AI智能体
    if category in ["通报", "表彰"]:
        return "writing_wizard"  # 使用专门的公文写作智能体
    elif doc_type in ["调研", "研究"]:
        return "deepseek"  # 使用研究型智能体
    elif doc_type in ["讲话", "演讲"]:
        return "ai_creative"  # 使用创意写作
    else:
        return "writing_wizard"  # 默认使用公文写作智能体
