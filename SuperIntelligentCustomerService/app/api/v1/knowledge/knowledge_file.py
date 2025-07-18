"""
知识文件管理API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.controllers.knowledge import knowledge_file_controller
from app.schemas.knowledge import (
    KnowledgeFileResponse,
    KnowledgeFileListQuery,
    KnowledgeFileUploadResponse
)
from app.services.file_storage import file_storage
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


@router.post("/{kb_id}/upload", summary="上传文件到知识库", response_model=dict)
async def upload_file(
    kb_id: int,
    file: UploadFile = File(...),
    current_user: User = DependAuth
):
    """上传文件到指定知识库"""
    result = await knowledge_file_controller.upload_file(
        knowledge_base_id=kb_id,
        file=file,
        user_id=current_user.id
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("msg", "上传失败"))
    
    return result


@router.get("/{kb_id}/list", summary="获取知识库文件列表", response_model=dict)
async def list_files(
    kb_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[str] = Query(None, description="状态过滤"),
    current_user: User = DependAuth
):
    """获取知识库文件列表"""
    result = await knowledge_file_controller.list_files(
        knowledge_base_id=kb_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("msg", "获取失败"))
    
    return result


@router.get("/{file_id}/info", summary="获取文件信息", response_model=dict)
async def get_file_info(
    file_id: int,
    current_user: User = DependAuth
):
    """获取文件详细信息"""
    result = await knowledge_file_controller.get_file_info(file_id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404 if "不存在" in result.get("msg", "") else 403,
                          detail=result.get("msg", "获取失败"))
    
    return result


@router.get("/{file_id}/download", summary="下载文件")
async def download_file(
    file_id: int,
    current_user: User = DependAuth
):
    """下载文件"""
    # 先获取文件信息
    result = await knowledge_file_controller.get_file_info(file_id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404 if "不存在" in result.get("msg", "") else 403,
                          detail=result.get("msg", "文件不存在或无权限"))
    
    file_data = result.get("data", {})
    file_path = file_data.get("file_path")
    original_name = file_data.get("original_name")
    
    if not file_path:
        raise HTTPException(status_code=404, detail="文件路径不存在")
    
    try:
        return file_storage.get_file_response(file_path, original_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"文件下载失败: {str(e)}")


@router.delete("/{file_id}", summary="删除文件", response_model=dict)
async def delete_file(
    file_id: int,
    current_user: User = DependAuth
):
    """删除文件"""
    result = await knowledge_file_controller.delete_file(file_id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404 if "不存在" in result.get("msg", "") else 403,
                          detail=result.get("msg", "删除失败"))
    
    return result


@router.post("/{file_id}/reprocess", summary="重新处理文件", response_model=dict)
async def reprocess_file(
    file_id: int,
    current_user: User = DependAuth
):
    """重新处理文件"""
    from app.services.file_processor import file_processor
    
    # 先检查文件权限
    result = await knowledge_file_controller.get_file_info(file_id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404 if "不存在" in result.get("msg", "") else 403,
                          detail=result.get("msg", "文件不存在或无权限"))
    
    # 重新处理文件
    try:
        success = await file_processor.reprocess_file(file_id)
        if success:
            return {
                "success": True,
                "msg": "文件重新处理已启动"
            }
        else:
            return {
                "success": False,
                "msg": "文件重新处理失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新处理失败: {str(e)}")


@router.get("/{file_id}/processing-status", summary="获取文件处理状态", response_model=dict)
async def get_processing_status(
    file_id: int,
    current_user: User = DependAuth
):
    """获取文件处理状态"""
    result = await knowledge_file_controller.get_file_info(file_id, current_user.id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=404 if "不存在" in result.get("msg", "") else 403,
                          detail=result.get("msg", "文件不存在或无权限"))
    
    file_data = result.get("data", {})
    
    status_info = {
        "file_id": file_id,
        "filename": file_data.get("name"),
        "status": file_data.get("embedding_status"),
        "error_message": file_data.get("embedding_error"),
        "chunk_count": file_data.get("chunk_count", 0),
        "processed_at": file_data.get("processed_at"),
        "created_at": file_data.get("created_at"),
        "updated_at": file_data.get("updated_at")
    }
    
    return {
        "success": True,
        "data": status_info,
        "msg": "获取处理状态成功"
    }


@router.post("/batch-upload/{kb_id}", summary="批量上传文件", response_model=dict)
async def batch_upload_files(
    kb_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = DependAuth
):
    """批量上传文件到知识库"""
    results = {
        "success_count": 0,
        "failed_count": 0,
        "success_files": [],
        "failed_files": []
    }
    
    for file in files:
        try:
            result = await knowledge_file_controller.upload_file(
                knowledge_base_id=kb_id,
                file=file,
                user_id=current_user.id
            )
            
            if result.get("success", False):
                results["success_count"] += 1
                results["success_files"].append({
                    "filename": file.filename,
                    "file_id": result.get("data", {}).get("id"),
                    "status": "success"
                })
            else:
                results["failed_count"] += 1
                results["failed_files"].append({
                    "filename": file.filename,
                    "error": result.get("msg", "上传失败")
                })
                
        except Exception as e:
            results["failed_count"] += 1
            results["failed_files"].append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success": True,
        "data": results,
        "msg": f"批量上传完成，成功: {results['success_count']}, 失败: {results['failed_count']}"
    }
