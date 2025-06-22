"""
智能问答API端点
"""

import json
from typing import List, Optional, Dict, Any

from app.core.security import get_current_user
from app.models.user import User
from app.services.intelligent_qa_service import (
    intelligent_qa_service,
    QAContext,
    QuestionType
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.exceptions import QAException

router = APIRouter()


class QARequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题")
    knowledge_base_id: int = Field(..., description="知识库ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    stream: bool = Field(False, description="是否流式返回")


class QAResponse(BaseModel):
    """问答响应"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning: str = ""
    suggestions: List[str] = []
    related_questions: List[str] = []
    question_type: str = ""
    session_id: str = ""


class QAStreamChunk(BaseModel):
    """流式问答数据块"""
    type: str  # "content", "sources", "complete"
    content: str = ""
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class QuestionAnalysisRequest(BaseModel):
    """问题分析请求"""
    question: str = Field(..., description="用户问题")


class RelatedQuestionsRequest(BaseModel):
    """相关问题生成请求"""
    question: str = Field(..., description="原始问题")
    knowledge_base_id: int = Field(..., description="知识库ID")
    count: int = Field(5, ge=1, le=10, description="生成数量")


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    current_user: User = Depends(get_current_user)
):
    """
    智能问答
    """
    try:
        # 构建问答上下文
        context = QAContext(
            question=request.question,
            question_type=QuestionType.FACTUAL,  # 将在服务中自动分析
            knowledge_base_id=request.knowledge_base_id,
            user_id=str(current_user.id),
            session_id=request.session_id or f"session_{current_user.id}_{hash(request.question)}",
            history=request.history or [],
            constraints=request.constraints or {}
        )
        
        # 执行问答
        if request.stream:
            # 流式响应
            return StreamingResponse(
                _stream_qa_response(context),
                media_type="text/plain"
            )
        else:
            # 普通响应
            result = await intelligent_qa_service.answer_question(context, stream=False)
            
            return QAResponse(
                answer=result.answer,
                confidence=result.confidence,
                sources=result.sources,
                reasoning=result.reasoning,
                suggestions=result.suggestions,
                related_questions=result.related_questions,
                question_type=context.question_type.value,
                session_id=context.session_id
            )
            
    except QAException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/ask/stream")
async def ask_question_stream(
    request: QARequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式智能问答
    """
    try:
        # 构建问答上下文
        context = QAContext(
            question=request.question,
            question_type=QuestionType.FACTUAL,
            knowledge_base_id=request.knowledge_base_id,
            user_id=str(current_user.id),
            session_id=request.session_id or f"session_{current_user.id}_{hash(request.question)}",
            history=request.history or [],
            constraints=request.constraints or {}
        )
        
        return StreamingResponse(
            _stream_qa_response(context),
            media_type="application/x-ndjson"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式问答失败: {str(e)}")


async def _stream_qa_response(context: QAContext):
    """生成流式问答响应"""
    try:
        # 发送开始信号
        yield _format_stream_chunk(QAStreamChunk(
            type="start",
            metadata={"session_id": context.session_id}
        ))
        
        # 流式生成答案
        answer_chunks = []
        async for chunk in intelligent_qa_service.answer_question_stream(context):
            answer_chunks.append(chunk)
            yield _format_stream_chunk(QAStreamChunk(
                type="content",
                content=chunk
            ))
        
        # 获取完整答案用于后续处理
        full_answer = "".join(answer_chunks)
        
        # 获取源文档（简化处理）
        sources = []
        yield _format_stream_chunk(QAStreamChunk(
            type="sources",
            sources=sources
        ))
        
        # 发送完成信号
        yield _format_stream_chunk(QAStreamChunk(
            type="complete",
            metadata={
                "confidence": 0.8,  # 简化处理
                "question_type": context.question_type.value
            }
        ))
        
    except Exception as e:
        # 发送错误信号
        yield _format_stream_chunk(QAStreamChunk(
            type="error",
            content=str(e)
        ))


def _format_stream_chunk(chunk: QAStreamChunk) -> str:
    """格式化流式数据块"""
    return f"data: {json.dumps(chunk.dict(), ensure_ascii=False)}\n\n"


@router.get("/question-types")
async def get_question_types():
    """
    获取支持的问题类型
    """
    return {
        "question_types": [
            {
                "value": q_type.value,
                "name": q_type.name,
                "description": _get_question_type_description(q_type)
            }
            for q_type in QuestionType
        ]
    }


@router.post("/analyze-question")
async def analyze_question(
    request: QuestionAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    分析问题类型和复杂度
    """
    try:
        # 这里可以调用问题分析服务
        # 目前返回简单的分析结果

        # 简单的关键词分析
        question_lower = request.question.lower()
        
        if any(word in question_lower for word in ["什么是", "谁是", "哪里", "何时"]):
            question_type = QuestionType.FACTUAL
            complexity = "simple"
        elif any(word in question_lower for word in ["为什么", "原因", "影响"]):
            question_type = QuestionType.ANALYTICAL
            complexity = "medium"
        elif any(word in question_lower for word in ["比较", "区别", "不同"]):
            question_type = QuestionType.COMPARATIVE
            complexity = "medium"
        elif any(word in question_lower for word in ["如何", "怎样", "步骤"]):
            question_type = QuestionType.PROCEDURAL
            complexity = "medium"
        else:
            question_type = QuestionType.FACTUAL
            complexity = "simple"
        
        return {
            "question": request.question,
            "question_type": question_type.value,
            "complexity": complexity,
            "estimated_response_time": _estimate_response_time(complexity),
            "suggested_search_strategy": _suggest_search_strategy(question_type)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问题分析失败: {str(e)}")


@router.post("/generate-related-questions")
async def generate_related_questions(
    request: RelatedQuestionsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成相关问题
    """
    try:
        # 构建简单的上下文
        context = QAContext(
            question=request.question,
            question_type=QuestionType.FACTUAL,
            knowledge_base_id=request.knowledge_base_id,
            user_id=str(current_user.id),
            session_id=f"temp_{hash(request.question)}"
        )

        # 生成相关问题
        related_questions = await intelligent_qa_service._generate_related_questions(context)

        return {
            "original_question": request.question,
            "related_questions": related_questions[:request.count]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成相关问题失败: {str(e)}")


@router.get("/qa-history/{session_id}")
async def get_qa_history(
    session_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    获取问答历史
    """
    try:
        # 这里应该从数据库获取历史记录
        # 目前返回模拟数据
        history = [
            {
                "id": f"qa_{i}",
                "question": f"示例问题 {i}",
                "answer": f"示例答案 {i}",
                "timestamp": "2024-01-01T00:00:00Z",
                "confidence": 0.8 + i * 0.02
            }
            for i in range(1, min(limit + 1, 6))
        ]
        
        return {
            "session_id": session_id,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问答历史失败: {str(e)}")


def _get_question_type_description(question_type: QuestionType) -> str:
    """获取问题类型描述"""
    descriptions = {
        QuestionType.FACTUAL: "事实性问题，询问具体信息",
        QuestionType.ANALYTICAL: "分析性问题，需要深入分析",
        QuestionType.COMPARATIVE: "比较性问题，比较不同事物",
        QuestionType.PROCEDURAL: "程序性问题，询问操作步骤",
        QuestionType.CREATIVE: "创造性问题，需要创新思维",
        QuestionType.MULTIMODAL: "多模态问题，涉及图片等"
    }
    return descriptions.get(question_type, "未知问题类型")


def _estimate_response_time(complexity: str) -> str:
    """估算响应时间"""
    time_estimates = {
        "simple": "1-3秒",
        "medium": "3-8秒",
        "complex": "8-15秒"
    }
    return time_estimates.get(complexity, "未知")


def _suggest_search_strategy(question_type: QuestionType) -> str:
    """建议搜索策略"""
    strategies = {
        QuestionType.FACTUAL: "向量搜索",
        QuestionType.ANALYTICAL: "混合搜索",
        QuestionType.COMPARATIVE: "语义搜索",
        QuestionType.PROCEDURAL: "关键词搜索",
        QuestionType.CREATIVE: "图谱搜索",
        QuestionType.MULTIMODAL: "多模态搜索"
    }
    return strategies.get(question_type, "混合搜索")
