from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Query

from app.controllers.memory_controller import MemoryController, MemoryQueryRequest, MemoryAddRequest
from app.services.memory_service import KnowledgeType

router = APIRouter()
memory_controller = MemoryController()


@router.post("/upload")
async def upload_file_to_knowledge_base(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    knowledge_type: str = Form(KnowledgeType.CUSTOMER_SERVICE),
    is_public: bool = Form(False)
):
    """上传文件到知识库"""
    return await memory_controller.upload_file_to_knowledge_base(
        user_id=user_id,
        file=file,
        knowledge_type=knowledge_type,
        is_public=is_public
    )


@router.post("/query")
async def query_memory(
    user_id: str,
    request: MemoryQueryRequest,
    include_public: bool = Query(True, description="是否包含公共记忆")
):
    """查询记忆内容"""
    return await memory_controller.query_memory(
        user_id=user_id,
        request=request,
        include_public=include_public
    )


@router.post("/add-text")
async def add_text_to_memory(
    user_id: str,
    request: MemoryAddRequest,
    is_public: bool = Query(False, description="是否为公共记忆")
):
    """添加文本到记忆"""
    return await memory_controller.add_text_to_memory(
        user_id=user_id,
        request=request,
        is_public=is_public
    )


@router.delete("/clear")
async def clear_user_memory(
    user_id: str,
    knowledge_type: str = Query(KnowledgeType.CUSTOMER_SERVICE, description="知识库类型"),
    memory_type: str = Query("all", description="记忆类型: chat, private, all")
):
    """清除用户记忆"""
    return await memory_controller.clear_user_memory(
        user_id=user_id,
        knowledge_type=knowledge_type,
        memory_type=memory_type
    )


@router.get("/chat-history")
async def get_chat_history(
    user_id: str,
    limit: Optional[int] = Query(None, description="限制返回数量")
):
    """获取用户聊天历史"""
    return await memory_controller.get_chat_history(
        user_id=user_id,
        limit=limit
    )


@router.get("/stats")
async def get_memory_stats(user_id: str):
    """获取用户记忆统计信息"""
    return await memory_controller.get_memory_stats(user_id=user_id)


@router.get("/knowledge-types")
async def get_knowledge_types():
    """获取支持的知识库类型"""
    return {
        "success": True,
        "message": "获取知识库类型成功",
        "data": {
            "types": [
                {"key": KnowledgeType.CUSTOMER_SERVICE, "name": "智能客服知识库"},
                {"key": KnowledgeType.TEXT_SQL, "name": "TextSQL知识库"},
                {"key": KnowledgeType.RAG, "name": "RAG知识库"},
                {"key": KnowledgeType.CONTENT_CREATION, "name": "文案创作知识库"}
            ]
        }
    }
