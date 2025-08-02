"""
文件上传管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime
import mimetypes

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.core.config import settings
from app.models.knowledge import UploadedFile
from app.schemas.files import FileResponse, FileUploadResponse

router = APIRouter()

# 支持的文件类型
ALLOWED_FILE_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/msword": [".doc"],
    "text/plain": [".txt"],
    "text/markdown": [".md"],
    "text/csv": [".csv"],
    "application/vnd.ms-excel": [".xls"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"]
}

# 最大文件大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def validate_file_type(file: UploadFile) -> bool:
    """验证文件类型"""
    if file.content_type not in ALLOWED_FILE_TYPES:
        return False
    
    file_ext = get_file_extension(file.filename)
    allowed_extensions = ALLOWED_FILE_TYPES[file.content_type]
    
    return file_ext in allowed_extensions


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    file_ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    单文件上传
    """
    # 验证文件类型
    if not validate_file_type(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 读取文件内容并验证大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
        )
    
    # 生成唯一文件名
    unique_filename = generate_unique_filename(file.filename)
    
    # 确保上传目录存在
    upload_dir = os.path.join(settings.UPLOAD_DIR, "files")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # 创建文件记录
    uploaded_file = UploadedFile(
        original_filename=file.filename,
        stored_filename=unique_filename,
        file_path=file_path,
        file_size=len(content),
        content_type=file.content_type,
        description=description,
        uploaded_by=current_user.id
    )
    
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    
    return {
        "file_id": uploaded_file.id,
        "original_filename": uploaded_file.original_filename,
        "file_size": uploaded_file.file_size,
        "content_type": uploaded_file.content_type,
        "upload_url": f"/api/v1/files/{uploaded_file.id}",
        "message": "文件上传成功"
    }


@router.post("/upload/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    descriptions: Optional[List[str]] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    多文件上传
    """
    if len(files) > 10:  # 限制最多10个文件
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="一次最多上传10个文件"
        )
    
    results = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, "files")
    os.makedirs(upload_dir, exist_ok=True)
    
    for i, file in enumerate(files):
        try:
            # 验证文件类型
            if not validate_file_type(file):
                results.append({
                    "original_filename": file.filename,
                    "error": f"不支持的文件类型: {file.content_type}"
                })
                continue
            
            # 读取文件内容并验证大小
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                results.append({
                    "original_filename": file.filename,
                    "error": f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
                })
                continue
            
            # 生成唯一文件名
            unique_filename = generate_unique_filename(file.filename)
            
            # 保存文件
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # 获取描述
            description = descriptions[i] if descriptions and i < len(descriptions) else None
            
            # 创建文件记录
            uploaded_file = UploadedFile(
                original_filename=file.filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=len(content),
                content_type=file.content_type,
                description=description,
                uploaded_by=current_user.id
            )
            
            db.add(uploaded_file)
            db.commit()
            db.refresh(uploaded_file)
            
            results.append({
                "file_id": uploaded_file.id,
                "original_filename": uploaded_file.original_filename,
                "file_size": uploaded_file.file_size,
                "content_type": uploaded_file.content_type,
                "upload_url": f"/api/v1/files/{uploaded_file.id}",
                "message": "文件上传成功"
            })
            
        except Exception as e:
            results.append({
                "original_filename": file.filename,
                "error": str(e)
            })
    
    return results


@router.get("/", response_model=List[FileResponse])
async def get_files(
    skip: int = 0,
    limit: int = 20,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户上传的文件列表
    """
    query = db.query(UploadedFile).filter(UploadedFile.uploaded_by == current_user.id)
    
    if file_type:
        query = query.filter(UploadedFile.content_type.contains(file_type))
    
    files = query.order_by(UploadedFile.created_at.desc()).offset(skip).limit(limit).all()
    
    return files


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_info(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取文件信息
    """
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return file_record


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载文件
    """
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件已被删除"
        )
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除文件
    """
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 删除物理文件
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # 删除数据库记录
    db.delete(file_record)
    db.commit()
    
    return {"message": "文件删除成功"}


@router.get("/types/supported")
async def get_supported_file_types():
    """
    获取支持的文件类型
    """
    return {
        "supported_types": ALLOWED_FILE_TYPES,
        "max_file_size": MAX_FILE_SIZE,
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024
    }
