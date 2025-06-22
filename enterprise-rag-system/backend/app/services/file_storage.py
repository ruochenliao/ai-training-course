"""
文件存储服务
"""

import mimetypes
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, BinaryIO

import aiofiles
from app.core.config import settings
from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.exceptions import ExternalServiceException


class FileStorageService:
    """文件存储服务类"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
            else:
                logger.info(f"存储桶已存在: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"检查/创建存储桶失败: {e}")
            raise ExternalServiceException(f"存储服务初始化失败: {e}")
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str = None,
        folder: str = "documents",
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """上传文件"""
        try:
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_ext = Path(file_name).suffix
            object_name = f"{folder}/{file_id}{file_ext}"
            
            # 获取文件大小
            file_data.seek(0, 2)  # 移动到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到文件开头
            
            # 自动检测内容类型
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # 准备元数据
            file_metadata = {
                'original-name': file_name,
                'upload-time': datetime.now().isoformat(),
                'file-id': file_id,
                **(metadata or {})
            }
            
            # 上传文件
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=file_metadata
            )
            
            logger.info(f"文件上传成功: {file_name} -> {object_name}")
            
            return {
                'file_id': file_id,
                'object_name': object_name,
                'original_name': file_name,
                'file_size': file_size,
                'content_type': content_type,
                'etag': result.etag,
                'upload_time': datetime.now(),
                'url': self.get_file_url(object_name)
            }
            
        except S3Error as e:
            logger.error(f"文件上传失败: {e}")
            raise ExternalServiceException(f"文件上传失败: {e}")
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            raise ExternalServiceException(f"文件上传异常: {e}")
    
    async def upload_file_from_path(
        self,
        file_path: str,
        folder: str = "documents",
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """从文件路径上传文件"""
        try:
            file_name = Path(file_path).name
            
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
                
            # 创建BytesIO对象
            from io import BytesIO
            file_obj = BytesIO(file_data)
            
            return await self.upload_file(
                file_data=file_obj,
                file_name=file_name,
                folder=folder,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"从路径上传文件失败: {e}")
            raise ExternalServiceException(f"从路径上传文件失败: {e}")
    
    async def download_file(self, object_name: str) -> bytes:
        """下载文件"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.debug(f"文件下载成功: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"文件下载失败: {e}")
            raise ExternalServiceException(f"文件下载失败: {e}")
    
    async def download_file_to_path(self, object_name: str, local_path: str) -> bool:
        """下载文件到本地路径"""
        try:
            self.client.fget_object(self.bucket_name, object_name, local_path)
            logger.info(f"文件下载到本地: {object_name} -> {local_path}")
            return True
            
        except S3Error as e:
            logger.error(f"文件下载到本地失败: {e}")
            raise ExternalServiceException(f"文件下载到本地失败: {e}")
    
    def get_file_url(self, object_name: str, expires: timedelta = None) -> str:
        """获取文件访问URL"""
        try:
            if expires is None:
                expires = timedelta(hours=1)  # 默认1小时有效期
            
            url = self.client.presigned_get_object(
                self.bucket_name, 
                object_name, 
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"生成文件URL失败: {e}")
            raise ExternalServiceException(f"生成文件URL失败: {e}")
    
    def get_upload_url(
        self, 
        object_name: str, 
        expires: timedelta = None,
        content_type: str = None
    ) -> str:
        """获取上传URL（用于前端直传）"""
        try:
            if expires is None:
                expires = timedelta(minutes=15)  # 默认15分钟有效期
            
            conditions = {}
            if content_type:
                conditions['content-type'] = content_type
            
            url = self.client.presigned_put_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"生成上传URL失败: {e}")
            raise ExternalServiceException(f"生成上传URL失败: {e}")
    
    async def delete_file(self, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"文件删除成功: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件删除失败: {e}")
            raise ExternalServiceException(f"文件删除失败: {e}")
    
    async def delete_files(self, object_names: List[str]) -> Dict[str, bool]:
        """批量删除文件"""
        results = {}
        
        for object_name in object_names:
            try:
                await self.delete_file(object_name)
                results[object_name] = True
            except Exception as e:
                logger.error(f"删除文件失败 {object_name}: {e}")
                results[object_name] = False
        
        return results
    
    def list_files(
        self, 
        prefix: str = "", 
        recursive: bool = True,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """列出文件"""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=recursive,
                max_keys=max_keys
            )
            
            files = []
            for obj in objects:
                file_info = {
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'etag': obj.etag,
                    'last_modified': obj.last_modified,
                    'content_type': obj.content_type,
                    'metadata': obj.metadata
                }
                files.append(file_info)
            
            logger.debug(f"列出 {len(files)} 个文件，前缀: {prefix}")
            return files
            
        except S3Error as e:
            logger.error(f"列出文件失败: {e}")
            raise ExternalServiceException(f"列出文件失败: {e}")
    
    def get_file_info(self, object_name: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            file_info = {
                'object_name': object_name,
                'size': stat.size,
                'etag': stat.etag,
                'last_modified': stat.last_modified,
                'content_type': stat.content_type,
                'metadata': stat.metadata,
                'version_id': stat.version_id
            }
            
            return file_info
            
        except S3Error as e:
            logger.error(f"获取文件信息失败: {e}")
            raise ExternalServiceException(f"获取文件信息失败: {e}")
    
    def file_exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    async def copy_file(self, source_object: str, dest_object: str) -> bool:
        """复制文件"""
        try:
            from minio.commonconfig import CopySource
            
            copy_source = CopySource(self.bucket_name, source_object)
            self.client.copy_object(self.bucket_name, dest_object, copy_source)
            
            logger.info(f"文件复制成功: {source_object} -> {dest_object}")
            return True
            
        except S3Error as e:
            logger.error(f"文件复制失败: {e}")
            raise ExternalServiceException(f"文件复制失败: {e}")
    
    def get_bucket_stats(self) -> Dict[str, Any]:
        """获取存储桶统计信息"""
        try:
            # 获取所有对象
            objects = list(self.client.list_objects(self.bucket_name, recursive=True))
            
            total_size = sum(obj.size for obj in objects)
            total_count = len(objects)
            
            # 按文件类型分组
            type_stats = {}
            for obj in objects:
                content_type = obj.content_type or 'unknown'
                if content_type not in type_stats:
                    type_stats[content_type] = {'count': 0, 'size': 0}
                type_stats[content_type]['count'] += 1
                type_stats[content_type]['size'] += obj.size
            
            return {
                'bucket_name': self.bucket_name,
                'total_objects': total_count,
                'total_size': total_size,
                'type_statistics': type_stats,
                'last_updated': datetime.now()
            }
            
        except S3Error as e:
            logger.error(f"获取存储桶统计失败: {e}")
            raise ExternalServiceException(f"获取存储桶统计失败: {e}")
    
    async def cleanup_expired_files(self, folder: str, days: int = 30) -> int:
        """清理过期文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            objects = self.client.list_objects(self.bucket_name, prefix=folder, recursive=True)
            
            deleted_count = 0
            for obj in objects:
                if obj.last_modified < cutoff_date:
                    try:
                        await self.delete_file(obj.object_name)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除过期文件失败 {obj.object_name}: {e}")
            
            logger.info(f"清理了 {deleted_count} 个过期文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理过期文件失败: {e}")
            raise ExternalServiceException(f"清理过期文件失败: {e}")


# 全局文件存储服务实例
file_storage = FileStorageService()
