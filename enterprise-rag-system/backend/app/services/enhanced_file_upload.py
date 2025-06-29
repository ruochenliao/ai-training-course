"""
增强的文件上传服务
"""

import os
import hashlib
import mimetypes
import asyncio
from typing import Dict, List, Optional, Any, BinaryIO, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import aiofiles

from fastapi import UploadFile, HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis_cache import get_redis_cache
from app.core.error_codes import ErrorCode, create_error_response
from app.services.file_storage import file_storage


class UploadStatus(str, Enum):
    """上传状态"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChunkStatus(str, Enum):
    """分片状态"""
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"


@dataclass
class FileUploadConfig:
    """文件上传配置"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 1024 * 1024  # 1MB分片
    allowed_extensions: List[str] = None
    allowed_mime_types: List[str] = None
    scan_for_viruses: bool = True
    auto_process: bool = True
    temp_dir: str = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = [
                '.pdf', '.docx', '.pptx', '.txt', '.md', '.html', 
                '.csv', '.xlsx', '.json', '.xml', '.rtf'
            ]
        
        if self.allowed_mime_types is None:
            self.allowed_mime_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'text/plain', 'text/markdown', 'text/html', 'text/csv',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/json', 'application/xml', 'application/rtf'
            ]
        
        if self.temp_dir is None:
            self.temp_dir = tempfile.gettempdir()


@dataclass
class ChunkInfo:
    """分片信息"""
    chunk_number: int
    chunk_size: int
    chunk_hash: str
    status: ChunkStatus = ChunkStatus.PENDING
    uploaded_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class UploadSession:
    """上传会话"""
    session_id: str
    file_name: str
    file_size: int
    total_chunks: int
    chunk_size: int
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    status: UploadStatus = UploadStatus.PENDING
    chunks: List[ChunkInfo] = None
    created_at: datetime = None
    updated_at: datetime = None
    uploaded_by: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class EnhancedFileUploadService:
    """增强的文件上传服务"""
    
    def __init__(self, config: FileUploadConfig = None):
        self.config = config or FileUploadConfig()
        self.file_storage = file_storage
        
        # 上传会话缓存（Redis）
        self.session_ttl = 3600 * 24  # 24小时
        
        # 支持的文件类型检测
        self.file_type_detectors = {
            'pdf': self._detect_pdf,
            'docx': self._detect_docx,
            'image': self._detect_image,
            'text': self._detect_text,
        }
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """验证文件"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        try:
            # 1. 检查文件名
            if not file.filename:
                validation_result["valid"] = False
                validation_result["errors"].append("文件名不能为空")
                return validation_result
            
            # 2. 检查文件扩展名
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.config.allowed_extensions:
                validation_result["valid"] = False
                validation_result["errors"].append(f"不支持的文件类型: {file_ext}")
            
            # 3. 检查MIME类型
            if file.content_type and file.content_type not in self.config.allowed_mime_types:
                validation_result["warnings"].append(f"MIME类型可能不正确: {file.content_type}")
            
            # 4. 检查文件大小
            if hasattr(file, 'size') and file.size:
                if file.size > self.config.max_file_size:
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        f"文件大小超过限制: {file.size} > {self.config.max_file_size}"
                    )
                validation_result["file_info"]["size"] = file.size
            
            # 5. 检查文件内容（读取前几个字节）
            if validation_result["valid"]:
                content_check = await self._check_file_content(file)
                validation_result["file_info"].update(content_check)
                
                if not content_check.get("content_valid", True):
                    validation_result["valid"] = False
                    validation_result["errors"].append("文件内容验证失败")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            validation_result["valid"] = False
            validation_result["errors"].append(f"文件验证异常: {str(e)}")
            return validation_result
    
    async def create_upload_session(
        self,
        file_name: str,
        file_size: int,
        file_hash: Optional[str] = None,
        mime_type: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> UploadSession:
        """创建上传会话"""
        try:
            # 生成会话ID
            session_id = hashlib.md5(
                f"{file_name}_{file_size}_{datetime.now().isoformat()}_{uploaded_by}".encode()
            ).hexdigest()
            
            # 计算分片数量
            total_chunks = (file_size + self.config.chunk_size - 1) // self.config.chunk_size
            
            # 创建上传会话
            session = UploadSession(
                session_id=session_id,
                file_name=file_name,
                file_size=file_size,
                total_chunks=total_chunks,
                chunk_size=self.config.chunk_size,
                file_hash=file_hash,
                mime_type=mime_type,
                uploaded_by=uploaded_by,
                metadata=metadata or {}
            )
            
            # 初始化分片信息
            for i in range(total_chunks):
                chunk_size = min(self.config.chunk_size, file_size - i * self.config.chunk_size)
                session.chunks.append(ChunkInfo(
                    chunk_number=i,
                    chunk_size=chunk_size,
                    chunk_hash=""
                ))
            
            # 保存会话到Redis
            await self._save_upload_session(session)
            
            logger.info(f"创建上传会话: {session_id}, 文件: {file_name}, 分片数: {total_chunks}")
            return session
            
        except Exception as e:
            logger.error(f"创建上传会话失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建上传会话失败: {str(e)}"
            )
    
    async def upload_chunk(
        self,
        session_id: str,
        chunk_number: int,
        chunk_data: bytes,
        chunk_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传文件分片"""
        try:
            # 获取上传会话
            session = await self._get_upload_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="上传会话不存在"
                )
            
            # 验证分片编号
            if chunk_number >= session.total_chunks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的分片编号"
                )
            
            # 验证分片大小
            expected_size = session.chunks[chunk_number].chunk_size
            if len(chunk_data) != expected_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"分片大小不匹配: {len(chunk_data)} != {expected_size}"
                )
            
            # 验证分片哈希
            if chunk_hash:
                calculated_hash = hashlib.md5(chunk_data).hexdigest()
                if calculated_hash != chunk_hash:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="分片哈希验证失败"
                    )
            
            # 保存分片到临时文件
            chunk_file_path = await self._save_chunk_to_temp(session_id, chunk_number, chunk_data)
            
            # 更新分片状态
            session.chunks[chunk_number].status = ChunkStatus.UPLOADED
            session.chunks[chunk_number].chunk_hash = chunk_hash or hashlib.md5(chunk_data).hexdigest()
            session.chunks[chunk_number].uploaded_at = datetime.now()
            session.updated_at = datetime.now()
            
            # 检查是否所有分片都已上传
            uploaded_chunks = sum(1 for chunk in session.chunks if chunk.status == ChunkStatus.UPLOADED)
            
            if uploaded_chunks == session.total_chunks:
                session.status = UploadStatus.PROCESSING
                # 异步合并文件
                asyncio.create_task(self._merge_chunks(session))
            else:
                session.status = UploadStatus.UPLOADING
            
            # 保存会话
            await self._save_upload_session(session)
            
            return {
                "success": True,
                "chunk_number": chunk_number,
                "uploaded_chunks": uploaded_chunks,
                "total_chunks": session.total_chunks,
                "progress": uploaded_chunks / session.total_chunks,
                "status": session.status.value
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"上传分片失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上传分片失败: {str(e)}"
            )
    
    async def upload_complete_file(
        self,
        file: UploadFile,
        uploaded_by: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """上传完整文件（小文件直接上传）"""
        try:
            # 验证文件
            validation = await self.validate_file(file)
            if not validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件验证失败: {', '.join(validation['errors'])}"
                )
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            # 计算文件哈希
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # 检查重复文件
            duplicate_check = await self._check_duplicate_file(file_hash, file.filename)
            if duplicate_check["is_duplicate"]:
                return {
                    "success": True,
                    "is_duplicate": True,
                    "existing_file": duplicate_check["existing_file"],
                    "message": "文件已存在，跳过上传"
                }
            
            # 上传到存储
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            upload_result = await self.file_storage.upload_file(
                file_data=file_obj,
                file_name=file.filename,
                content_type=file.content_type,
                folder="documents",
                metadata={
                    "uploaded_by": str(uploaded_by) if uploaded_by else "",
                    "file_hash": file_hash,
                    "upload_method": "complete",
                    **(metadata or {})
                }
            )
            
            logger.info(f"完整文件上传成功: {file.filename}, 大小: {file_size}")
            
            return {
                "success": True,
                "is_duplicate": False,
                "file_info": upload_result,
                "file_hash": file_hash,
                "validation_info": validation["file_info"],
                "message": "文件上传成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"完整文件上传失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件上传失败: {str(e)}"
            )
    
    async def get_upload_progress(self, session_id: str) -> Dict[str, Any]:
        """获取上传进度"""
        try:
            session = await self._get_upload_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="上传会话不存在"
                )
            
            uploaded_chunks = sum(1 for chunk in session.chunks if chunk.status == ChunkStatus.UPLOADED)
            failed_chunks = sum(1 for chunk in session.chunks if chunk.status == ChunkStatus.FAILED)
            
            return {
                "session_id": session_id,
                "file_name": session.file_name,
                "file_size": session.file_size,
                "status": session.status.value,
                "uploaded_chunks": uploaded_chunks,
                "failed_chunks": failed_chunks,
                "total_chunks": session.total_chunks,
                "progress": uploaded_chunks / session.total_chunks,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取上传进度失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取上传进度失败: {str(e)}"
            )
    
    async def cancel_upload(self, session_id: str) -> Dict[str, Any]:
        """取消上传"""
        try:
            session = await self._get_upload_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="上传会话不存在"
                )
            
            # 更新状态
            session.status = UploadStatus.CANCELLED
            session.updated_at = datetime.now()
            
            # 清理临时文件
            await self._cleanup_temp_files(session_id)
            
            # 保存会话
            await self._save_upload_session(session)
            
            logger.info(f"取消上传: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "上传已取消"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"取消上传失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"取消上传失败: {str(e)}"
            )
    
    async def _check_file_content(self, file: UploadFile) -> Dict[str, Any]:
        """检查文件内容"""
        try:
            # 读取文件头部用于检测
            current_pos = file.file.tell()
            header = await file.read(1024)  # 读取前1KB
            file.file.seek(current_pos)  # 重置文件位置
            
            result = {
                "content_valid": True,
                "detected_type": None,
                "encoding": None
            }
            
            # 检测文件类型
            if header.startswith(b'%PDF'):
                result["detected_type"] = "pdf"
            elif header.startswith(b'PK\x03\x04'):
                result["detected_type"] = "office"  # docx, xlsx, pptx等
            elif header.startswith(b'\x89PNG'):
                result["detected_type"] = "png"
            elif header.startswith(b'\xff\xd8\xff'):
                result["detected_type"] = "jpeg"
            else:
                # 尝试检测文本编码
                try:
                    text = header.decode('utf-8')
                    result["detected_type"] = "text"
                    result["encoding"] = "utf-8"
                except UnicodeDecodeError:
                    try:
                        text = header.decode('gbk')
                        result["detected_type"] = "text"
                        result["encoding"] = "gbk"
                    except UnicodeDecodeError:
                        result["detected_type"] = "binary"
            
            return result
            
        except Exception as e:
            logger.error(f"检查文件内容失败: {e}")
            return {"content_valid": False, "error": str(e)}
    
    async def _save_chunk_to_temp(self, session_id: str, chunk_number: int, chunk_data: bytes) -> str:
        """保存分片到临时文件"""
        temp_dir = Path(self.config.temp_dir) / "uploads" / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_file_path = temp_dir / f"chunk_{chunk_number:06d}"
        
        async with aiofiles.open(chunk_file_path, 'wb') as f:
            await f.write(chunk_data)
        
        return str(chunk_file_path)
    
    async def _merge_chunks(self, session: UploadSession):
        """合并分片文件"""
        try:
            session.status = UploadStatus.PROCESSING
            await self._save_upload_session(session)
            
            # 创建临时合并文件
            temp_dir = Path(self.config.temp_dir) / "uploads" / session.session_id
            merged_file_path = temp_dir / "merged_file"
            
            # 合并分片
            async with aiofiles.open(merged_file_path, 'wb') as merged_file:
                for i in range(session.total_chunks):
                    chunk_file_path = temp_dir / f"chunk_{i:06d}"
                    if chunk_file_path.exists():
                        async with aiofiles.open(chunk_file_path, 'rb') as chunk_file:
                            chunk_data = await chunk_file.read()
                            await merged_file.write(chunk_data)
            
            # 验证合并后的文件
            if session.file_hash:
                merged_hash = await self._calculate_file_hash(str(merged_file_path))
                if merged_hash != session.file_hash:
                    raise Exception("合并后文件哈希验证失败")
            
            # 上传到存储
            async with aiofiles.open(merged_file_path, 'rb') as f:
                upload_result = await self.file_storage.upload_file(
                    file_data=f,
                    file_name=session.file_name,
                    content_type=session.mime_type,
                    folder="documents",
                    metadata={
                        "uploaded_by": str(session.uploaded_by) if session.uploaded_by else "",
                        "file_hash": session.file_hash or "",
                        "upload_method": "chunked",
                        "session_id": session.session_id,
                        **session.metadata
                    }
                )
            
            # 更新会话状态
            session.status = UploadStatus.COMPLETED
            session.metadata["upload_result"] = upload_result
            session.updated_at = datetime.now()
            await self._save_upload_session(session)
            
            # 清理临时文件
            await self._cleanup_temp_files(session.session_id)
            
            logger.info(f"文件合并完成: {session.file_name}")
            
        except Exception as e:
            logger.error(f"合并分片失败: {e}")
            session.status = UploadStatus.FAILED
            session.metadata["error"] = str(e)
            session.updated_at = datetime.now()
            await self._save_upload_session(session)
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hash_md5 = hashlib.md5()
        async with aiofiles.open(file_path, 'rb') as f:
            async for chunk in f:
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def _check_duplicate_file(self, file_hash: str, file_name: str) -> Dict[str, Any]:
        """检查重复文件"""
        # 这里应该查询数据库检查是否有相同哈希的文件
        # 简化实现，返回不重复
        return {
            "is_duplicate": False,
            "existing_file": None
        }
    
    async def _save_upload_session(self, session: UploadSession):
        """保存上传会话到Redis"""
        try:
            redis_cache = await get_redis_cache()
            session_data = {
                "session_id": session.session_id,
                "file_name": session.file_name,
                "file_size": session.file_size,
                "total_chunks": session.total_chunks,
                "chunk_size": session.chunk_size,
                "file_hash": session.file_hash,
                "mime_type": session.mime_type,
                "status": session.status.value,
                "chunks": [
                    {
                        "chunk_number": chunk.chunk_number,
                        "chunk_size": chunk.chunk_size,
                        "chunk_hash": chunk.chunk_hash,
                        "status": chunk.status.value,
                        "uploaded_at": chunk.uploaded_at.isoformat() if chunk.uploaded_at else None,
                        "error_message": chunk.error_message
                    }
                    for chunk in session.chunks
                ],
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "uploaded_by": session.uploaded_by,
                "metadata": session.metadata
            }
            
            await redis_cache.set(
                f"upload_session:{session.session_id}",
                session_data,
                self.session_ttl,
                "file_upload"
            )
            
        except Exception as e:
            logger.error(f"保存上传会话失败: {e}")
    
    async def _get_upload_session(self, session_id: str) -> Optional[UploadSession]:
        """从Redis获取上传会话"""
        try:
            redis_cache = await get_redis_cache()
            session_data = await redis_cache.get(f"upload_session:{session_id}", "file_upload")
            
            if not session_data:
                return None
            
            # 重构UploadSession对象
            chunks = []
            for chunk_data in session_data["chunks"]:
                chunk = ChunkInfo(
                    chunk_number=chunk_data["chunk_number"],
                    chunk_size=chunk_data["chunk_size"],
                    chunk_hash=chunk_data["chunk_hash"],
                    status=ChunkStatus(chunk_data["status"]),
                    uploaded_at=datetime.fromisoformat(chunk_data["uploaded_at"]) if chunk_data["uploaded_at"] else None,
                    error_message=chunk_data["error_message"]
                )
                chunks.append(chunk)
            
            session = UploadSession(
                session_id=session_data["session_id"],
                file_name=session_data["file_name"],
                file_size=session_data["file_size"],
                total_chunks=session_data["total_chunks"],
                chunk_size=session_data["chunk_size"],
                file_hash=session_data["file_hash"],
                mime_type=session_data["mime_type"],
                status=UploadStatus(session_data["status"]),
                chunks=chunks,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"]),
                uploaded_by=session_data["uploaded_by"],
                metadata=session_data["metadata"]
            )
            
            return session
            
        except Exception as e:
            logger.error(f"获取上传会话失败: {e}")
            return None
    
    async def _cleanup_temp_files(self, session_id: str):
        """清理临时文件"""
        try:
            temp_dir = Path(self.config.temp_dir) / "uploads" / session_id
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"清理临时文件: {temp_dir}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")

    def _detect_pdf(self, header: bytes) -> bool:
        """检测PDF文件"""
        return header.startswith(b'%PDF')

    def _detect_docx(self, header: bytes) -> bool:
        """检测Office文档"""
        return header.startswith(b'PK\x03\x04')

    def _detect_image(self, header: bytes) -> bool:
        """检测图片文件"""
        return (header.startswith(b'\x89PNG') or
                header.startswith(b'\xff\xd8\xff') or
                header.startswith(b'GIF8'))

    def _detect_text(self, header: bytes) -> bool:
        """检测文本文件"""
        try:
            header.decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                header.decode('gbk')
                return True
            except UnicodeDecodeError:
                return False


# 全局文件上传服务实例
enhanced_file_upload_service = None


def get_enhanced_file_upload_service() -> EnhancedFileUploadService:
    """获取增强文件上传服务实例"""
    global enhanced_file_upload_service
    if enhanced_file_upload_service is None:
        enhanced_file_upload_service = EnhancedFileUploadService()
    return enhanced_file_upload_service
