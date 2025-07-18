"""
批量操作API路由
"""
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.services.batch_operations import batch_operation_service
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    file_ids: List[int]


class BatchReprocessRequest(BaseModel):
    """批量重新处理请求"""
    file_ids: List[int]


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    kb_ids: List[int]
    export_format: str = "json"


@router.post("/upload/{kb_id}", summary="批量上传文件", response_model=dict)
async def batch_upload_files(
    kb_id: int,
    files: List[UploadFile] = File(...),
    max_concurrent: int = 3,
    current_user: User = DependAuth
):
    """
    批量上传文件到知识库
    
    Args:
        kb_id: 知识库ID
        files: 文件列表
        max_concurrent: 最大并发数
        current_user: 当前用户
        
    Returns:
        批量上传结果
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        if len(files) > 50:  # 限制批量上传数量
            raise HTTPException(status_code=400, detail="批量上传文件数量不能超过50个")
        
        result = await batch_operation_service.batch_upload_files(
            knowledge_base_id=kb_id,
            files=files,
            user_id=current_user.id,
            max_concurrent=max_concurrent
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
            "msg": f"批量上传完成，成功: {result.success}, 失败: {result.failed}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.post("/delete", summary="批量删除文件", response_model=dict)
async def batch_delete_files(
    request: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除文件
    
    Args:
        request: 批量删除请求
        current_user: 当前用户
        
    Returns:
        批量删除结果
    """
    try:
        if not request.file_ids:
            raise HTTPException(status_code=400, detail="没有选择要删除的文件")
        
        if len(request.file_ids) > 100:  # 限制批量删除数量
            raise HTTPException(status_code=400, detail="批量删除文件数量不能超过100个")
        
        result = await batch_operation_service.batch_delete_files(
            file_ids=request.file_ids,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
            "msg": f"批量删除完成，成功: {result.success}, 失败: {result.failed}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.post("/reprocess", summary="批量重新处理文件", response_model=dict)
async def batch_reprocess_files(
    request: BatchReprocessRequest,
    current_user: User = DependAuth
):
    """
    批量重新处理文件
    
    Args:
        request: 批量重新处理请求
        current_user: 当前用户
        
    Returns:
        批量重新处理结果
    """
    try:
        if not request.file_ids:
            raise HTTPException(status_code=400, detail="没有选择要重新处理的文件")
        
        if len(request.file_ids) > 50:  # 限制批量重新处理数量
            raise HTTPException(status_code=400, detail="批量重新处理文件数量不能超过50个")
        
        result = await batch_operation_service.batch_reprocess_files(
            file_ids=request.file_ids,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
            "msg": f"批量重新处理完成，成功: {result.success}, 失败: {result.failed}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量重新处理失败: {str(e)}")


@router.post("/export", summary="批量导出知识库", response_model=dict)
async def batch_export_knowledge_bases(
    request: BatchExportRequest,
    current_user: User = DependAuth
):
    """
    批量导出知识库
    
    Args:
        request: 批量导出请求
        current_user: 当前用户
        
    Returns:
        批量导出结果
    """
    try:
        if not request.kb_ids:
            raise HTTPException(status_code=400, detail="没有选择要导出的知识库")
        
        if len(request.kb_ids) > 20:  # 限制批量导出数量
            raise HTTPException(status_code=400, detail="批量导出知识库数量不能超过20个")
        
        if request.export_format not in ["json", "full"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        result = await batch_operation_service.batch_export_knowledge_bases(
            kb_ids=request.kb_ids,
            user_id=current_user.id,
            export_format=request.export_format
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
            "msg": f"批量导出完成，成功: {result.success}, 失败: {result.failed}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导出失败: {str(e)}")


@router.get("/operations/status", summary="获取批量操作状态", response_model=dict)
async def get_batch_operations_status(
    current_user: User = DependAuth
):
    """
    获取当前用户的批量操作状态
    
    Args:
        current_user: 当前用户
        
    Returns:
        批量操作状态
    """
    try:
        # 这里可以实现批量操作状态跟踪
        # 目前返回简单的状态信息
        
        from app.services.file_processing_monitor import file_processing_monitor
        
        # 获取处理统计
        stats = await file_processing_monitor.get_statistics()
        
        # 获取用户相关的处理状态
        all_status = file_processing_monitor.get_all_status()
        user_processing = []
        
        for status in all_status:
            # 这里可以添加权限检查，确保只返回用户有权限的文件
            user_processing.append(status.to_dict())
        
        return {
            "success": True,
            "data": {
                "global_stats": stats,
                "user_processing": user_processing,
                "limits": {
                    "max_upload_files": 50,
                    "max_delete_files": 100,
                    "max_reprocess_files": 50,
                    "max_export_kbs": 20
                }
            },
            "msg": "获取批量操作状态成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量操作状态失败: {str(e)}")


@router.post("/validate", summary="验证批量操作", response_model=dict)
async def validate_batch_operation(
    operation_type: str,
    target_ids: List[int],
    current_user: User = DependAuth
):
    """
    验证批量操作的可行性
    
    Args:
        operation_type: 操作类型 (upload, delete, reprocess, export)
        target_ids: 目标ID列表
        current_user: 当前用户
        
    Returns:
        验证结果
    """
    try:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "valid_ids": [],
            "invalid_ids": []
        }
        
        if operation_type == "delete":
            # 验证删除权限
            from app.services.knowledge_permission_service import check_file_access
            
            for file_id in target_ids:
                try:
                    has_permission = await check_file_access(file_id, current_user.id, "write")
                    if has_permission:
                        validation_result["valid_ids"].append(file_id)
                    else:
                        validation_result["invalid_ids"].append(file_id)
                        validation_result["errors"].append(f"文件 {file_id}: 无删除权限")
                except Exception as e:
                    validation_result["invalid_ids"].append(file_id)
                    validation_result["errors"].append(f"文件 {file_id}: {str(e)}")
        
        elif operation_type == "reprocess":
            # 验证重新处理权限
            from app.services.knowledge_permission_service import check_file_access
            from app.models.knowledge import KnowledgeFile
            
            for file_id in target_ids:
                try:
                    has_permission = await check_file_access(file_id, current_user.id, "write")
                    if not has_permission:
                        validation_result["invalid_ids"].append(file_id)
                        validation_result["errors"].append(f"文件 {file_id}: 无重新处理权限")
                        continue
                    
                    # 检查文件状态
                    file_obj = await KnowledgeFile.get_or_none(id=file_id)
                    if not file_obj:
                        validation_result["invalid_ids"].append(file_id)
                        validation_result["errors"].append(f"文件 {file_id}: 文件不存在")
                        continue
                    
                    if file_obj.embedding_status in ["pending", "processing"]:
                        validation_result["invalid_ids"].append(file_id)
                        validation_result["warnings"].append(f"文件 {file_id}: 正在处理中，无需重新处理")
                        continue
                    
                    validation_result["valid_ids"].append(file_id)
                    
                except Exception as e:
                    validation_result["invalid_ids"].append(file_id)
                    validation_result["errors"].append(f"文件 {file_id}: {str(e)}")
        
        elif operation_type == "export":
            # 验证导出权限
            from app.services.knowledge_permission_service import check_knowledge_base_access
            
            for kb_id in target_ids:
                try:
                    has_permission = await check_knowledge_base_access(kb_id, current_user.id, "read")
                    if has_permission:
                        validation_result["valid_ids"].append(kb_id)
                    else:
                        validation_result["invalid_ids"].append(kb_id)
                        validation_result["errors"].append(f"知识库 {kb_id}: 无导出权限")
                except Exception as e:
                    validation_result["invalid_ids"].append(kb_id)
                    validation_result["errors"].append(f"知识库 {kb_id}: {str(e)}")
        
        else:
            validation_result["valid"] = False
            validation_result["errors"].append(f"不支持的操作类型: {operation_type}")
        
        # 检查是否有有效的目标
        if not validation_result["valid_ids"] and validation_result["invalid_ids"]:
            validation_result["valid"] = False
        
        return {
            "success": True,
            "data": validation_result,
            "msg": "验证完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证批量操作失败: {str(e)}")
