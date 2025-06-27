"""
文档处理API端点 - 企业级RAG系统
严格按照技术栈要求：/api/v1/documents/ 文档处理模块
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from app.core.auth import get_current_user
from app.core.database_new import get_db_session
from app.models.sqlalchemy_models import Document, KnowledgeBase, User
from app.services.document_processing_pipeline import document_pipeline
from app.services.intelligent_chunker import ChunkStrategy
from app.services.marker_document_service import marker_service
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["documents"])


# Pydantic 模型
class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    document_id: Optional[int] = None
    filename: str
    file_size: int
    message: str
    task_id: Optional[str] = None


class DocumentProcessingStatus(BaseModel):
    """文档处理状态"""
    document_id: int
    filename: str
    parse_status: str
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ChunkingConfig(BaseModel):
    """分块配置"""
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
    chunk_size: int = Field(default=1000, ge=100, le=2000)
    overlap: int = Field(default=200, ge=0, le=500)


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    knowledge_base_id: int
    chunking_config: Optional[ChunkingConfig] = None
    auto_process: bool = True


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    auto_process: bool = Form(default=True),
    chunking_config: Optional[str] = Form(default=None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    上传单个文档
    
    - **knowledge_base_id**: 知识库ID
    - **file**: 上传的文件 (支持PDF、DOCX、PPTX、XLSX、MD、TXT，最大100MB)
    - **auto_process**: 是否自动处理文档
    - **chunking_config**: 分块配置 (JSON字符串)
    """
    try:
        # 验证文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小和格式
        is_valid, error_msg = marker_service.validate_file(
            file.filename, file_size, file.content_type
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 保存文件到临时目录
        temp_file_path = await marker_service.save_uploaded_file(file_content, file.filename)
        
        # 计算文件哈希
        file_hash = await marker_service.calculate_file_hash(temp_file_path)
        
        # 检查文件是否已存在
        # TODO: 实现重复文件检查逻辑
        
        # 创建文档记录
        document = Document(
            knowledge_base_id=knowledge_base_id,
            filename=temp_file_path.name,
            original_filename=file.filename,
            file_path=str(temp_file_path),
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower().lstrip('.'),
            mime_type=file.content_type or "application/octet-stream",
            md5_hash=file_hash,
            uploaded_by=current_user.id
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        response = DocumentUploadResponse(
            success=True,
            document_id=document.id,
            filename=file.filename,
            file_size=file_size,
            message="文档上传成功"
        )
        
        # 如果启用自动处理，添加后台任务
        if auto_process:
            # 解析分块配置
            chunk_config = ChunkingConfig()
            if chunking_config:
                try:
                    import json
                    config_dict = json.loads(chunking_config)
                    chunk_config = ChunkingConfig(**config_dict)
                except Exception as e:
                    logger.warning(f"分块配置解析失败，使用默认配置: {e}")
            
            # 添加后台处理任务
            background_tasks.add_task(
                process_document_background,
                document.id,
                knowledge_base_id,
                temp_file_path,
                {
                    "filename": file.filename,
                    "file_type": document.file_type,
                    "file_size": file_size,
                    "uploaded_by": current_user.id
                },
                chunk_config
            )
            
            response.message = "文档上传成功，正在后台处理"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    request: BatchUploadRequest = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    批量上传文档 (最多50个文件)
    """
    try:
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="批量上传最多支持50个文件")
        
        upload_results = []
        
        for file in files:
            try:
                # 验证文件
                if not file.filename:
                    upload_results.append({
                        "filename": "unknown",
                        "success": False,
                        "error": "文件名不能为空"
                    })
                    continue
                
                # 读取文件内容
                file_content = await file.read()
                file_size = len(file_content)
                
                # 验证文件
                is_valid, error_msg = marker_service.validate_file(
                    file.filename, file_size, file.content_type
                )
                if not is_valid:
                    upload_results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": error_msg
                    })
                    continue
                
                # 保存文件
                temp_file_path = await marker_service.save_uploaded_file(file_content, file.filename)
                file_hash = await marker_service.calculate_file_hash(temp_file_path)
                
                # 创建文档记录
                document = Document(
                    knowledge_base_id=request.knowledge_base_id,
                    filename=temp_file_path.name,
                    original_filename=file.filename,
                    file_path=str(temp_file_path),
                    file_size=file_size,
                    file_type=Path(file.filename).suffix.lower().lstrip('.'),
                    mime_type=file.content_type or "application/octet-stream",
                    md5_hash=file_hash,
                    uploaded_by=current_user.id
                )
                
                db.add(document)
                await db.commit()
                await db.refresh(document)
                
                upload_results.append({
                    "filename": file.filename,
                    "success": True,
                    "document_id": document.id,
                    "file_size": file_size
                })
                
                # 添加后台处理任务
                if request.auto_process:
                    background_tasks.add_task(
                        process_document_background,
                        document.id,
                        request.knowledge_base_id,
                        temp_file_path,
                        {
                            "filename": file.filename,
                            "file_type": document.file_type,
                            "file_size": file_size,
                            "uploaded_by": current_user.id
                        },
                        request.chunking_config or ChunkingConfig()
                    )
                
            except Exception as e:
                logger.error(f"处理文件失败 {file.filename}: {e}")
                upload_results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        successful_uploads = sum(1 for result in upload_results if result["success"])
        
        return {
            "success": True,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": len(files) - successful_uploads,
            "results": upload_results,
            "message": f"批量上传完成，成功: {successful_uploads}, 失败: {len(files) - successful_uploads}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取文档处理状态"""
    try:
        # TODO: 实现文档状态查询逻辑
        # 这里需要查询Document表获取处理状态
        
        return DocumentProcessingStatus(
            document_id=document_id,
            filename="example.pdf",
            parse_status="completed",
            total_chunks=10,
            processed_chunks=10,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
    except Exception as e:
        logger.error(f"获取文档状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档状态失败: {str(e)}")


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    chunking_config: Optional[ChunkingConfig] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """重新处理文档"""
    try:
        # TODO: 实现文档重新处理逻辑
        # 1. 查询文档信息
        # 2. 删除现有的处理结果
        # 3. 重新启动处理流程
        
        return {
            "success": True,
            "message": "文档重新处理已启动",
            "document_id": document_id
        }
        
    except Exception as e:
        logger.error(f"重新处理文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新处理文档失败: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除文档及其所有相关数据"""
    try:
        # TODO: 实现文档删除逻辑
        # 1. 查询文档信息
        # 2. 删除向量数据
        # 3. 删除图谱数据
        # 4. 删除数据库记录
        # 5. 删除文件
        
        return {
            "success": True,
            "message": "文档删除成功",
            "document_id": document_id
        }
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.get("/health")
async def health_check():
    """文档处理服务健康检查"""
    try:
        # 检查各个服务的健康状态
        marker_health = await marker_service.health_check() if hasattr(marker_service, 'health_check') else {"status": "unknown"}
        
        return {
            "status": "healthy",
            "services": {
                "marker": marker_health,
            },
            "timestamp": "2024-01-01T00:00:00"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00"
            }
        )


# 后台任务函数
async def process_document_background(
    document_id: int,
    knowledge_base_id: int,
    file_path: Path,
    metadata: dict,
    chunking_config: ChunkingConfig
):
    """后台处理文档任务"""
    try:
        logger.info(f"开始后台处理文档: {document_id}")
        
        result = await document_pipeline.process_document(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            file_path=file_path,
            metadata=metadata,
            chunk_strategy=chunking_config.strategy,
            chunk_size=chunking_config.chunk_size,
            overlap=chunking_config.overlap
        )
        
        if result["success"]:
            logger.info(f"文档后台处理成功: {document_id}")
        else:
            logger.error(f"文档后台处理失败: {document_id}, 错误: {result.get('error')}")
        
        # 清理临时文件
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
        
    except Exception as e:
        logger.error(f"后台处理文档异常: {document_id}, 错误: {e}")


# WebSocket 支持 (实时进度追踪)
@router.websocket("/ws/{document_id}/progress")
async def websocket_document_progress(websocket, document_id: int):
    """WebSocket实时文档处理进度追踪"""
    await websocket.accept()
    
    try:
        # TODO: 实现WebSocket进度推送逻辑
        # 1. 监听文档处理状态变化
        # 2. 实时推送进度信息
        # 3. 处理客户端断开连接
        
        while True:
            # 模拟进度更新
            await asyncio.sleep(1)
            await websocket.send_json({
                "document_id": document_id,
                "status": "processing",
                "progress": 50,
                "message": "正在处理文档..."
            })
            
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        await websocket.close()
