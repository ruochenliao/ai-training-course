"""
文档处理API端点
提供文档上传、解析、搜索等功能
"""

import os
import uuid
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.config import settings
from app.services.enhanced_document_service import enhanced_document_service
from app.models.user import User

router = APIRouter(prefix="/document", tags=["文档处理"])


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    file_name: str
    file_size: int
    status: str
    message: str


class DocumentSearchRequest(BaseModel):
    """文档搜索请求"""
    query: str = Field(..., description="搜索查询")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="相似度阈值")


class DocumentSearchResult(BaseModel):
    """文档搜索结果"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    similarity_score: float
    chunk_index: int


class DocumentInfo(BaseModel):
    """文档信息"""
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: Optional[int]
    created_at: str
    processed_at: Optional[str]
    metadata: dict


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    extract_images: bool = Form(True),
    extract_tables: bool = Form(True),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    current_user: User = Depends(get_current_user)
):
    """
    上传并处理文档
    
    支持的格式：PDF, Word, Excel, PowerPoint, 文本文件等
    """
    try:
        # 检查文件格式
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in enhanced_document_service.supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(enhanced_document_service.supported_formats)}"
            )
        
        # 检查文件大小
        if file.size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制: {file.size} bytes > {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # 保存文件
        upload_dir = Path(settings.UPLOAD_DIR) / "documents"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 后台处理文档
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            file.filename,
            current_user.id,
            conversation_id,
            extract_images,
            extract_tables,
            chunk_size,
            chunk_overlap
        )
        
        return DocumentUploadResponse(
            document_id=file_id,
            file_name=file.filename,
            file_size=file.size,
            status="processing",
            message="文档上传成功，正在后台处理中..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


async def process_document_background(
    file_path: str,
    file_name: str,
    user_id: int,
    conversation_id: Optional[str],
    extract_images: bool,
    extract_tables: bool,
    chunk_size: int,
    chunk_overlap: int
):
    """后台处理文档"""
    try:
        await enhanced_document_service.process_document(
            file_path=file_path,
            file_name=file_name,
            user_id=user_id,
            conversation_id=conversation_id,
            extract_images=extract_images,
            extract_tables=extract_tables,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    except Exception as e:
        # 记录错误，但不抛出异常（避免影响主流程）
        from loguru import logger
        logger.error(f"后台文档处理失败: {e}")


@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    搜索文档内容
    
    基于语义相似度搜索用户上传的文档
    """
    try:
        results = await enhanced_document_service.search_documents(
            query=request.query,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        return [
            DocumentSearchResult(
                chunk_id=result['chunk_id'],
                document_id=result['document_id'],
                document_name=result['document_name'],
                content=result['content'],
                similarity_score=result['similarity_score'],
                chunk_index=result['chunk_index']
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档搜索失败: {str(e)}")


@router.get("/info/{document_id}", response_model=DocumentInfo)
async def get_document_info(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取文档信息"""
    try:
        document_info = await enhanced_document_service.get_document_info(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not document_info:
            raise HTTPException(status_code=404, detail="文档不存在或无权访问")
        
        return DocumentInfo(**document_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档信息失败: {str(e)}")


@router.delete("/delete/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除文档"""
    try:
        success = await enhanced_document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在或无权删除")
        
        return {"message": "文档删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.get("/list")
async def list_user_documents(
    conversation_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user)
):
    """获取用户文档列表"""
    try:
        from app.core.database import get_async_session
        from app.models.document import Document
        from sqlalchemy import and_, desc
        
        async with get_async_session() as session:
            # 构建查询条件
            conditions = [Document.user_id == current_user.id]
            
            if conversation_id:
                conditions.append(Document.conversation_id == conversation_id)
            
            if status:
                conditions.append(Document.status == status)
            
            # 查询文档
            query = session.query(Document).filter(and_(*conditions))
            query = query.order_by(desc(Document.created_at))
            
            # 分页
            offset = (page - 1) * page_size
            documents = await query.offset(offset).limit(page_size).all()
            
            # 统计总数
            total_count = await session.query(Document).filter(and_(*conditions)).count()
            
            return {
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "file_type": doc.file_type,
                        "file_size": doc.file_size,
                        "status": doc.status,
                        "chunk_count": doc.chunk_count,
                        "created_at": doc.created_at.isoformat(),
                        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                        "conversation_id": doc.conversation_id
                    }
                    for doc in documents
                ],
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文档格式"""
    return {
        "supported_formats": list(enhanced_document_service.supported_formats),
        "format_descriptions": {
            ".pdf": "PDF文档",
            ".docx": "Word文档",
            ".doc": "Word文档（旧版）",
            ".pptx": "PowerPoint演示文稿",
            ".ppt": "PowerPoint演示文稿（旧版）",
            ".xlsx": "Excel电子表格",
            ".xls": "Excel电子表格（旧版）",
            ".txt": "纯文本文件",
            ".md": "Markdown文档",
            ".html": "HTML网页",
            ".htm": "HTML网页",
            ".csv": "CSV数据文件",
            ".json": "JSON数据文件",
            ".xml": "XML文档",
            ".rtf": "富文本格式"
        },
        "max_file_size": settings.MAX_UPLOAD_SIZE,
        "max_file_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024)
    }


@router.post("/analyze")
async def analyze_document_content(
    document_id: str,
    analysis_type: str = "summary",  # summary, keywords, entities, sentiment
    current_user: User = Depends(get_current_user)
):
    """
    分析文档内容
    
    提供文档摘要、关键词提取、实体识别、情感分析等功能
    """
    try:
        # 获取文档信息
        document_info = await enhanced_document_service.get_document_info(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not document_info:
            raise HTTPException(status_code=404, detail="文档不存在或无权访问")
        
        # 这里可以集成各种文档分析功能
        # 暂时返回基础信息
        return {
            "document_id": document_id,
            "analysis_type": analysis_type,
            "result": {
                "message": f"文档 {analysis_type} 分析功能正在开发中",
                "document_info": document_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")
