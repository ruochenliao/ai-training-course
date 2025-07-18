"""
文件存储服务
支持本地文件存储，替代MinIO存储
参考006项目的设计架构
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, BinaryIO, Union
from datetime import datetime

from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.settings.config import settings
from app.log import logger


class FileStorageService:
    """文件存储服务"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化文件存储服务
        
        Args:
            base_dir: 基础存储目录，如果为None则使用配置中的目录
        """
        if base_dir is None:
            self.base_dir = Path(settings.BASE_DIR) / "data" / "files"
        else:
            self.base_dir = Path(base_dir)
        
        # 确保存储目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.knowledge_files_dir = self.base_dir / "knowledge_files"
        self.temp_dir = self.base_dir / "temp"
        self.knowledge_files_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"文件存储服务初始化完成，存储目录: {self.base_dir}")

    def generate_file_path(self, knowledge_base_id: int, original_filename: str) -> str:
        """
        生成文件存储路径
        
        Args:
            knowledge_base_id: 知识库ID
            original_filename: 原始文件名
            
        Returns:
            文件存储路径
        """
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_ext = Path(original_filename).suffix
        filename = f"{file_id}{file_ext}"
        
        # 按知识库ID分目录存储
        relative_path = f"knowledge_files/{knowledge_base_id}/{filename}"
        return relative_path

    def get_absolute_path(self, relative_path: str) -> Path:
        """
        获取文件的绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对路径
        """
        return self.base_dir / relative_path

    async def save_file(
        self, 
        file: UploadFile, 
        knowledge_base_id: int,
        relative_path: Optional[str] = None
    ) -> str:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件
            knowledge_base_id: 知识库ID
            relative_path: 指定的相对路径，如果为None则自动生成
            
        Returns:
            文件的相对路径
        """
        try:
            # 生成文件路径
            if relative_path is None:
                relative_path = self.generate_file_path(knowledge_base_id, file.filename)
            
            absolute_path = self.get_absolute_path(relative_path)
            
            # 确保目录存在
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(absolute_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"文件保存成功: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    async def save_file_content(
        self, 
        content: bytes, 
        knowledge_base_id: int,
        filename: str,
        relative_path: Optional[str] = None
    ) -> str:
        """
        保存文件内容
        
        Args:
            content: 文件内容
            knowledge_base_id: 知识库ID
            filename: 文件名
            relative_path: 指定的相对路径，如果为None则自动生成
            
        Returns:
            文件的相对路径
        """
        try:
            # 生成文件路径
            if relative_path is None:
                relative_path = self.generate_file_path(knowledge_base_id, filename)
            
            absolute_path = self.get_absolute_path(relative_path)
            
            # 确保目录存在
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(absolute_path, "wb") as buffer:
                buffer.write(content)
            
            logger.info(f"文件内容保存成功: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"文件内容保存失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件内容保存失败: {str(e)}")

    def get_file_response(self, relative_path: str, filename: Optional[str] = None) -> FileResponse:
        """
        获取文件响应
        
        Args:
            relative_path: 文件相对路径
            filename: 下载时的文件名，如果为None则使用原文件名
            
        Returns:
            文件响应
        """
        absolute_path = self.get_absolute_path(relative_path)
        
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if filename is None:
            filename = absolute_path.name
        
        return FileResponse(
            path=str(absolute_path),
            filename=filename,
            media_type='application/octet-stream'
        )

    def read_file(self, relative_path: str) -> bytes:
        """
        读取文件内容
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            文件内容
        """
        absolute_path = self.get_absolute_path(relative_path)
        
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        try:
            with open(absolute_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            是否删除成功
        """
        try:
            absolute_path = self.get_absolute_path(relative_path)
            
            if absolute_path.exists():
                absolute_path.unlink()
                logger.info(f"文件删除成功: {relative_path}")
                return True
            else:
                logger.warning(f"文件不存在: {relative_path}")
                return False
                
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False

    def file_exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            文件是否存在
        """
        absolute_path = self.get_absolute_path(relative_path)
        return absolute_path.exists()

    def get_file_size(self, relative_path: str) -> int:
        """
        获取文件大小
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            文件大小（字节）
        """
        absolute_path = self.get_absolute_path(relative_path)
        
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return absolute_path.stat().st_size

    def get_file_info(self, relative_path: str) -> dict:
        """
        获取文件信息
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            文件信息字典
        """
        absolute_path = self.get_absolute_path(relative_path)
        
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        stat = absolute_path.stat()
        
        return {
            "name": absolute_path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "path": relative_path
        }

    def cleanup_empty_directories(self, knowledge_base_id: int):
        """
        清理空目录
        
        Args:
            knowledge_base_id: 知识库ID
        """
        try:
            kb_dir = self.knowledge_files_dir / str(knowledge_base_id)
            if kb_dir.exists() and not any(kb_dir.iterdir()):
                kb_dir.rmdir()
                logger.info(f"清理空目录: {kb_dir}")
        except Exception as e:
            logger.error(f"清理目录失败: {str(e)}")

    def get_storage_stats(self) -> dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.knowledge_files_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        total_size += file_path.stat().st_size
                        file_count += 1
            
            return {
                "total_files": file_count,
                "total_size": total_size,
                "storage_dir": str(self.base_dir),
                "knowledge_files_dir": str(self.knowledge_files_dir)
            }
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {
                "total_files": 0,
                "total_size": 0,
                "storage_dir": str(self.base_dir),
                "knowledge_files_dir": str(self.knowledge_files_dir)
            }


# 全局文件存储服务实例
file_storage = FileStorageService()
