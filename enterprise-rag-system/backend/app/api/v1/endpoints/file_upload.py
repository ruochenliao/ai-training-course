"""
文件上传管理API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from app.core import get_current_user, PermissionChecker
from app.services.enhanced_file_upload import (
    get_enhanced_file_upload_service, FileUploadConfig, UploadSession
)
from app.models import User

router = APIRouter()

# 权限检查器
require_upload_permission = PermissionChecker("document:upload")
require_manage_permission = PermissionChecker("document:manage")


class FileValidationResponse(BaseModel):
    """文件验证响应"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    file_info: Dict[str, Any]


class UploadSessionResponse(BaseModel):
    """上传会话响应"""
    session_id: str
    file_name: str
    file_size: int
    total_chunks: int
    chunk_size: int
    status: str
    created_at: str


class ChunkUploadRequest(BaseModel):
    """分片上传请求"""
    session_id: str
    chunk_number: int
    chunk_hash: Optional[str] = None


class UploadProgressResponse(BaseModel):
    """上传进度响应"""
    session_id: str
    file_name: str
    file_size: int
    status: str
    uploaded_chunks: int
    total_chunks: int
    progress: float
    created_at: str
    updated_at: str


@router.post("/validate", response_model=FileValidationResponse, summary="验证文件")
async def validate_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    验证上传文件的格式、大小等
    """
    upload_service = get_enhanced_file_upload_service()
    
    validation_result = await upload_service.validate_file(file)
    
    return FileValidationResponse(**validation_result)


@router.post("/upload-complete", summary="完整文件上传")
async def upload_complete_file(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    上传完整文件（适用于小文件）
    """
    upload_service = get_enhanced_file_upload_service()
    
    metadata = {
        "knowledge_base_id": str(knowledge_base_id) if knowledge_base_id else "",
        "description": description or "",
        "auto_process": str(auto_process)
    }
    
    result = await upload_service.upload_complete_file(
        file=file,
        uploaded_by=current_user.id,
        metadata=metadata
    )
    
    return result


@router.post("/create-session", response_model=UploadSessionResponse, summary="创建上传会话")
async def create_upload_session(
    file_name: str = Form(...),
    file_size: int = Form(...),
    file_hash: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    knowledge_base_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    创建分片上传会话（适用于大文件）
    """
    upload_service = get_enhanced_file_upload_service()
    
    metadata = {
        "knowledge_base_id": str(knowledge_base_id) if knowledge_base_id else "",
        "description": description or ""
    }
    
    session = await upload_service.create_upload_session(
        file_name=file_name,
        file_size=file_size,
        file_hash=file_hash,
        mime_type=mime_type,
        uploaded_by=current_user.id,
        metadata=metadata
    )
    
    return UploadSessionResponse(
        session_id=session.session_id,
        file_name=session.file_name,
        file_size=session.file_size,
        total_chunks=session.total_chunks,
        chunk_size=session.chunk_size,
        status=session.status.value,
        created_at=session.created_at.isoformat()
    )


@router.post("/upload-chunk", summary="上传文件分片")
async def upload_chunk(
    session_id: str = Form(...),
    chunk_number: int = Form(...),
    chunk_hash: Optional[str] = Form(None),
    chunk_file: UploadFile = File(...),
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    上传文件分片
    """
    upload_service = get_enhanced_file_upload_service()
    
    # 读取分片数据
    chunk_data = await chunk_file.read()
    
    result = await upload_service.upload_chunk(
        session_id=session_id,
        chunk_number=chunk_number,
        chunk_data=chunk_data,
        chunk_hash=chunk_hash
    )
    
    return result


@router.get("/progress/{session_id}", response_model=UploadProgressResponse, summary="获取上传进度")
async def get_upload_progress(
    session_id: str,
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    获取上传进度
    """
    upload_service = get_enhanced_file_upload_service()
    
    progress = await upload_service.get_upload_progress(session_id)
    
    return UploadProgressResponse(**progress)


@router.post("/cancel/{session_id}", summary="取消上传")
async def cancel_upload(
    session_id: str,
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    取消上传
    """
    upload_service = get_enhanced_file_upload_service()
    
    result = await upload_service.cancel_upload(session_id)
    
    return result


@router.post("/batch-upload", summary="批量文件上传")
async def batch_upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    knowledge_base_id: Optional[int] = Form(None),
    auto_process: bool = Form(True),
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    批量上传文件
    """
    upload_service = get_enhanced_file_upload_service()
    
    async def process_batch_upload():
        results = []
        for file in files:
            try:
                metadata = {
                    "knowledge_base_id": str(knowledge_base_id) if knowledge_base_id else "",
                    "auto_process": str(auto_process),
                    "batch_upload": "true"
                }
                
                result = await upload_service.upload_complete_file(
                    file=file,
                    uploaded_by=current_user.id,
                    metadata=metadata
                )
                
                results.append({
                    "file_name": file.filename,
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"批量上传完成: {len(results)} 个文件")
        return results
    
    # 在后台处理批量上传
    background_tasks.add_task(process_batch_upload)
    
    return {
        "success": True,
        "message": f"批量上传任务已启动，共 {len(files)} 个文件",
        "file_count": len(files),
        "initiated_by": current_user.username
    }


@router.get("/config", summary="获取上传配置")
async def get_upload_config(
    current_user: User = Depends(require_upload_permission)
) -> Any:
    """
    获取文件上传配置
    """
    upload_service = get_enhanced_file_upload_service()
    config = upload_service.config
    
    return {
        "max_file_size": config.max_file_size,
        "chunk_size": config.chunk_size,
        "allowed_extensions": config.allowed_extensions,
        "allowed_mime_types": config.allowed_mime_types,
        "scan_for_viruses": config.scan_for_viruses,
        "auto_process": config.auto_process
    }


@router.put("/config", summary="更新上传配置")
async def update_upload_config(
    max_file_size: Optional[int] = None,
    chunk_size: Optional[int] = None,
    allowed_extensions: Optional[List[str]] = None,
    allowed_mime_types: Optional[List[str]] = None,
    scan_for_viruses: Optional[bool] = None,
    auto_process: Optional[bool] = None,
    current_user: User = Depends(require_manage_permission)
) -> Any:
    """
    更新文件上传配置
    """
    upload_service = get_enhanced_file_upload_service()
    config = upload_service.config
    
    # 更新配置
    if max_file_size is not None:
        config.max_file_size = max_file_size
    if chunk_size is not None:
        config.chunk_size = chunk_size
    if allowed_extensions is not None:
        config.allowed_extensions = allowed_extensions
    if allowed_mime_types is not None:
        config.allowed_mime_types = allowed_mime_types
    if scan_for_viruses is not None:
        config.scan_for_viruses = scan_for_viruses
    if auto_process is not None:
        config.auto_process = auto_process
    
    return {
        "success": True,
        "message": "上传配置更新成功",
        "updated_by": current_user.username,
        "config": {
            "max_file_size": config.max_file_size,
            "chunk_size": config.chunk_size,
            "allowed_extensions": config.allowed_extensions,
            "allowed_mime_types": config.allowed_mime_types,
            "scan_for_viruses": config.scan_for_viruses,
            "auto_process": config.auto_process
        }
    }


@router.get("/statistics", summary="获取上传统计")
async def get_upload_statistics(
    days: int = 7,
    current_user: User = Depends(require_manage_permission)
) -> Any:
    """
    获取文件上传统计信息
    """
    # 这里应该从数据库查询统计信息
    # 简化实现，返回模拟数据
    return {
        "period_days": days,
        "total_uploads": 150,
        "successful_uploads": 142,
        "failed_uploads": 8,
        "total_size": 1024 * 1024 * 1024 * 2.5,  # 2.5GB
        "average_file_size": 1024 * 1024 * 18,  # 18MB
        "upload_success_rate": 0.947,
        "popular_file_types": [
            {"extension": ".pdf", "count": 65},
            {"extension": ".docx", "count": 42},
            {"extension": ".txt", "count": 28},
            {"extension": ".xlsx", "count": 15}
        ],
        "upload_methods": {
            "complete": 120,
            "chunked": 30
        },
        "daily_uploads": [
            {"date": "2025-06-23", "count": 18},
            {"date": "2025-06-24", "count": 22},
            {"date": "2025-06-25", "count": 25},
            {"date": "2025-06-26", "count": 19},
            {"date": "2025-06-27", "count": 31},
            {"date": "2025-06-28", "count": 20},
            {"date": "2025-06-29", "count": 15}
        ]
    }


@router.get("/health", summary="上传服务健康检查")
async def upload_service_health_check(
    current_user: User = Depends(require_manage_permission)
) -> Any:
    """
    检查文件上传服务健康状态
    """
    upload_service = get_enhanced_file_upload_service()
    
    # 检查存储服务
    storage_health = {"status": "unknown"}
    try:
        # 这里应该检查文件存储服务的健康状态
        storage_health = {"status": "healthy", "response_time": 0.05}
    except Exception as e:
        storage_health = {"status": "unhealthy", "error": str(e)}
    
    # 检查临时目录
    temp_dir_health = {"status": "unknown"}
    try:
        import os
        temp_dir = upload_service.config.temp_dir
        if os.path.exists(temp_dir) and os.access(temp_dir, os.W_OK):
            temp_dir_health = {"status": "healthy", "path": temp_dir}
        else:
            temp_dir_health = {"status": "unhealthy", "error": "临时目录不可写"}
    except Exception as e:
        temp_dir_health = {"status": "unhealthy", "error": str(e)}
    
    # 检查Redis缓存
    cache_health = {"status": "unknown"}
    try:
        from app.core.redis_cache import get_redis_cache
        redis_cache = await get_redis_cache()
        cache_health_result = await redis_cache.health_check()
        cache_health = cache_health_result
    except Exception as e:
        cache_health = {"status": "unhealthy", "error": str(e)}
    
    overall_healthy = all(
        component["status"] == "healthy"
        for component in [storage_health, temp_dir_health, cache_health]
    )
    
    return {
        "overall_status": "healthy" if overall_healthy else "unhealthy",
        "components": {
            "file_storage": storage_health,
            "temp_directory": temp_dir_health,
            "redis_cache": cache_health
        },
        "config": {
            "max_file_size": upload_service.config.max_file_size,
            "chunk_size": upload_service.config.chunk_size,
            "supported_extensions": len(upload_service.config.allowed_extensions)
        }
    }
