"""
文件验证相关API路由
提供文件类型和大小限制的查询接口
"""
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.file_validator import file_validator, validate_uploaded_file
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


class FileTypeInfo(BaseModel):
    """文件类型信息"""
    file_type: str
    extensions: List[str]
    max_size: int
    max_size_formatted: str
    description: str


class ValidationRequest(BaseModel):
    """文件验证请求"""
    filename: str
    file_size: int
    allowed_types: List[str] = None


class ValidationResponse(BaseModel):
    """文件验证响应"""
    is_valid: bool
    file_type: str
    errors: List[str]
    warnings: List[str]


@router.get("/supported-types", summary="获取支持的文件类型", response_model=Dict[str, FileTypeInfo])
async def get_supported_file_types():
    """
    获取系统支持的文件类型信息
    
    Returns:
        支持的文件类型详细信息
    """
    try:
        supported_types = file_validator.get_supported_types()
        
        return {
            "success": True,
            "data": supported_types,
            "msg": "获取支持的文件类型成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件类型信息失败: {str(e)}")


@router.post("/validate-file", summary="验证上传文件", response_model=dict)
async def validate_file(
    file: UploadFile = File(...),
    allowed_types: str = None,  # 逗号分隔的类型列表
    max_size: int = None,
    current_user: User = DependAuth
):
    """
    验证上传的文件
    
    Args:
        file: 上传的文件
        allowed_types: 允许的文件类型（逗号分隔）
        max_size: 最大文件大小（字节）
        current_user: 当前用户
        
    Returns:
        验证结果
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析允许的类型
        allowed_type_list = None
        if allowed_types:
            allowed_type_list = [t.strip() for t in allowed_types.split(',')]
        
        # 验证文件
        validation_result = validate_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            allowed_types=allowed_type_list,
            max_size=max_size
        )
        
        return {
            "success": True,
            "data": validation_result.to_dict(),
            "msg": "文件验证完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件验证失败: {str(e)}")


@router.get("/limits/{knowledge_base_id}", summary="获取知识库文件限制", response_model=dict)
async def get_knowledge_base_limits(
    knowledge_base_id: int,
    current_user: User = DependAuth
):
    """
    获取指定知识库的文件上传限制
    
    Args:
        knowledge_base_id: 知识库ID
        current_user: 当前用户
        
    Returns:
        文件上传限制信息
    """
    try:
        from app.models.knowledge import KnowledgeBase
        from app.services.knowledge_permission_service import check_knowledge_base_access
        
        # 检查权限
        has_access = await check_knowledge_base_access(knowledge_base_id, current_user.id, "read")
        if not has_access:
            raise HTTPException(status_code=403, detail="无权限访问此知识库")
        
        # 获取知识库信息
        kb = await KnowledgeBase.get_or_none(id=knowledge_base_id, is_deleted=False)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 获取限制信息
        limits = {
            "max_file_size": kb.max_file_size,
            "max_file_size_formatted": _format_size(kb.max_file_size),
            "allowed_file_types": kb.allowed_file_types,
            "current_file_count": kb.file_count,
            "current_total_size": kb.total_size,
            "current_total_size_formatted": _format_size(kb.total_size),
            "supported_types": file_validator.get_supported_types()
        }
        
        return {
            "success": True,
            "data": limits,
            "msg": "获取文件限制信息成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件限制失败: {str(e)}")


@router.post("/check-filename", summary="检查文件名安全性", response_model=dict)
async def check_filename_safety(
    filename: str,
    current_user: User = DependAuth
):
    """
    检查文件名是否安全
    
    Args:
        filename: 文件名
        current_user: 当前用户
        
    Returns:
        文件名安全检查结果
    """
    try:
        is_safe = file_validator._is_safe_filename(filename)
        
        issues = []
        if not is_safe:
            if '..' in filename or '/' in filename or '\\' in filename:
                issues.append("文件名包含路径遍历字符")
            
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
            found_chars = [char for char in dangerous_chars if char in filename]
            if found_chars:
                issues.append(f"文件名包含危险字符: {', '.join(found_chars)}")
            
            if len(filename) > 255:
                issues.append("文件名过长（超过255字符）")
        
        return {
            "success": True,
            "data": {
                "filename": filename,
                "is_safe": is_safe,
                "issues": issues
            },
            "msg": "文件名检查完成"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件名检查失败: {str(e)}")


@router.get("/upload-stats", summary="获取上传统计信息", response_model=dict)
async def get_upload_stats(
    current_user: User = DependAuth
):
    """
    获取用户的文件上传统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        上传统计信息
    """
    try:
        from app.models.knowledge import KnowledgeBase, KnowledgeFile
        from tortoise.functions import Count, Sum
        
        # 获取用户的知识库统计
        kb_stats = await KnowledgeBase.filter(
            owner_id=current_user.id,
            is_deleted=False
        ).annotate(
            total_files=Count('files'),
            total_size=Sum('files__file_size')
        ).values('id', 'name', 'total_files', 'total_size')
        
        # 获取文件类型统计
        file_type_stats = await KnowledgeFile.filter(
            knowledge_base__owner_id=current_user.id,
            is_deleted=False
        ).group_by('file_type').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        ).values('file_type', 'count', 'total_size')
        
        # 计算总计
        total_files = sum(stat['count'] for stat in file_type_stats)
        total_size = sum(stat['total_size'] or 0 for stat in file_type_stats)
        
        return {
            "success": True,
            "data": {
                "knowledge_bases": kb_stats,
                "file_types": file_type_stats,
                "totals": {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_formatted": _format_size(total_size)
                },
                "limits": {
                    "max_file_size_per_upload": 50 * 1024 * 1024,  # 50MB
                    "max_total_size_per_user": 1024 * 1024 * 1024,  # 1GB
                    "max_files_per_kb": 1000
                }
            },
            "msg": "获取上传统计成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传统计失败: {str(e)}")


@router.post("/batch-validate", summary="批量验证文件", response_model=dict)
async def batch_validate_files(
    files: List[UploadFile] = File(...),
    allowed_types: str = None,
    max_size: int = None,
    current_user: User = DependAuth
):
    """
    批量验证多个文件
    
    Args:
        files: 上传的文件列表
        allowed_types: 允许的文件类型（逗号分隔）
        max_size: 最大文件大小（字节）
        current_user: 当前用户
        
    Returns:
        批量验证结果
    """
    try:
        if len(files) > 50:  # 限制批量验证数量
            raise HTTPException(status_code=400, detail="批量验证文件数量不能超过50个")
        
        # 解析允许的类型
        allowed_type_list = None
        if allowed_types:
            allowed_type_list = [t.strip() for t in allowed_types.split(',')]
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for file in files:
            try:
                # 读取文件内容
                file_content = await file.read()
                
                # 验证文件
                validation_result = validate_uploaded_file(
                    file_content=file_content,
                    filename=file.filename,
                    allowed_types=allowed_type_list,
                    max_size=max_size
                )
                
                result_dict = validation_result.to_dict()
                result_dict["filename"] = file.filename
                results.append(result_dict)
                
                if validation_result.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "is_valid": False,
                    "errors": [f"验证异常: {str(e)}"],
                    "warnings": []
                })
                invalid_count += 1
        
        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total_files": len(files),
                    "valid_files": valid_count,
                    "invalid_files": invalid_count,
                    "success_rate": f"{(valid_count / len(files) * 100):.1f}%" if files else "0%"
                }
            },
            "msg": f"批量验证完成，有效文件: {valid_count}, 无效文件: {invalid_count}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量验证失败: {str(e)}")


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"
