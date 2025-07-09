"""
知识文件控制器
提供文件上传、处理、删除等功能
"""
import os
import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist, IntegrityError

from ..models.knowledge import KnowledgeBase, KnowledgeFile
from ..models.enums import FileType, EmbeddingStatus
from ..utils.response import Success, Fail

logger = logging.getLogger(__name__)


class KnowledgeFileController:
    """知识文件控制器"""
    
    # 文件大小限制（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # 支持的文件类型映射
    MIME_TYPE_MAPPING = {
        "application/pdf": FileType.PDF,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
        "application/msword": FileType.DOC,
        "text/plain": FileType.TXT,
        "text/markdown": FileType.MD,
        "text/html": FileType.HTML,
        "image/jpeg": FileType.JPEG,
        "image/jpg": FileType.JPG,
        "image/png": FileType.PNG,
        "image/gif": FileType.GIF,
        "image/webp": FileType.WEBP,
    }
    
    @staticmethod
    def _get_file_hash(file_content: bytes) -> str:
        """计算文件SHA256哈希"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def _get_file_type_from_filename(filename: str) -> Optional[FileType]:
        """从文件名获取文件类型"""
        ext = Path(filename).suffix.lower()
        ext_mapping = {
            ".pdf": FileType.PDF,
            ".docx": FileType.DOCX,
            ".doc": FileType.DOC,
            ".txt": FileType.TXT,
            ".md": FileType.MD,
            ".html": FileType.HTML,
            ".htm": FileType.HTML,
            ".jpg": FileType.JPG,
            ".jpeg": FileType.JPEG,
            ".png": FileType.PNG,
            ".gif": FileType.GIF,
            ".webp": FileType.WEBP,
        }
        return ext_mapping.get(ext)
    
    @staticmethod
    def _get_upload_path(kb_id: int, filename: str) -> str:
        """生成文件上传路径"""
        # 创建基于知识库ID的目录结构
        upload_dir = Path("uploads") / "knowledge_bases" / str(kb_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        import uuid
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        return str(upload_dir / unique_filename)
    
    @staticmethod
    async def upload_file(
        kb_id: int,
        file: UploadFile,
        user_id: int
    ) -> Dict[str, Any]:
        """
        上传文件到知识库
        
        Args:
            kb_id: 知识库ID
            file: 上传的文件
            user_id: 用户ID
            
        Returns:
            上传结果
        """
        try:
            # 检查知识库是否存在和权限
            try:
                knowledge_base = await KnowledgeBase.get(id=kb_id)
            except DoesNotExist:
                return Fail(msg="知识库不存在")
            
            if not await knowledge_base.can_modify(user_id):
                return Fail(msg="无权限上传文件到此知识库")
            
            # 检查文件大小
            file_content = await file.read()
            file_size = len(file_content)
            
            if file_size > knowledge_base.max_file_size:
                max_size_mb = knowledge_base.max_file_size / (1024 * 1024)
                return Fail(msg=f"文件大小超过限制 ({max_size_mb:.1f}MB)")
            
            if file_size == 0:
                return Fail(msg="文件为空")
            
            # 检查文件类型
            file_type = KnowledgeFileController._get_file_type_from_filename(file.filename)
            if not file_type:
                return Fail(msg="不支持的文件类型")
            
            if file_type.value not in knowledge_base.allowed_file_types:
                return Fail(msg=f"知识库不允许上传 {file_type.value} 类型的文件")
            
            # 计算文件哈希
            file_hash = KnowledgeFileController._get_file_hash(file_content)
            
            # 检查文件是否已存在（基于哈希）
            existing_file = await KnowledgeFile.filter(
                knowledge_base_id=kb_id,
                file_hash=file_hash
            ).first()
            
            if existing_file:
                return Fail(msg="文件已存在")
            
            # 生成文件存储路径
            file_path = KnowledgeFileController._get_upload_path(kb_id, file.filename)
            
            # 保存文件到磁盘
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 获取MIME类型
            mime_type, _ = mimetypes.guess_type(file.filename)
            
            # 创建文件记录
            knowledge_file = await KnowledgeFile.create(
                name=Path(file.filename).stem,  # 不包含扩展名的文件名
                original_name=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                file_hash=file_hash,
                uploaded_by=user_id,
                knowledge_base_id=kb_id,
                embedding_status=EmbeddingStatus.PENDING
            )
            
            # 更新知识库统计
            await knowledge_base.update_statistics()
            
            logger.info(f"文件上传成功: {knowledge_file.id} - {file.filename}")
            
            # TODO: 触发异步处理任务
            # await queue_file_processing(knowledge_file.id)
            
            return Success(
                data=await knowledge_file.to_dict(),
                msg="文件上传成功"
            )
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return Fail(msg=f"文件上传失败: {str(e)}")
    
    @staticmethod
    async def get_file(file_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取文件详情
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            文件信息
        """
        try:
            knowledge_file = await KnowledgeFile.get(id=file_id).prefetch_related("knowledge_base")
            
            # 检查访问权限
            if not await knowledge_file.can_access(user_id):
                return Fail(msg="无权限访问此文件")
            
            file_dict = await knowledge_file.to_dict()
            
            # 添加知识库信息
            kb = await knowledge_file.knowledge_base
            file_dict["knowledge_base"] = {
                "id": kb.id,
                "name": kb.name,
                "knowledge_type": kb.knowledge_type
            }
            
            # 添加权限信息
            file_dict["can_modify"] = await knowledge_file.can_modify(user_id)
            
            return Success(data=file_dict)
            
        except DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"获取文件失败: {e}")
            return Fail(msg=f"获取文件失败: {str(e)}")
    
    @staticmethod
    async def list_files(
        kb_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        file_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识库文件列表
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            file_type: 文件类型过滤
            status: 状态过滤
            search: 搜索关键词
            
        Returns:
            文件列表
        """
        try:
            # 检查知识库权限
            try:
                knowledge_base = await KnowledgeBase.get(id=kb_id)
            except DoesNotExist:
                return Fail(msg="知识库不存在")
            
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")
            
            # 构建查询条件
            query = Q(knowledge_base_id=kb_id)
            
            # 文件类型过滤
            if file_type:
                query &= Q(file_type=file_type)
            
            # 状态过滤
            if status:
                query &= Q(embedding_status=status)
            
            # 搜索过滤
            if search:
                query &= Q(name__icontains=search) | Q(original_name__icontains=search)
            
            # 计算总数
            total = await KnowledgeFile.filter(query).count()
            
            # 分页查询
            offset = (page - 1) * page_size
            files = await KnowledgeFile.filter(query).offset(offset).limit(page_size).order_by("-created_at")
            
            # 转换为字典
            file_list = []
            for file in files:
                file_dict = await file.to_dict()
                file_dict["can_modify"] = await file.can_modify(user_id)
                file_list.append(file_dict)
            
            return Success(data={
                "items": file_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            
        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return Fail(msg=f"获取文件列表失败: {str(e)}")
    
    @staticmethod
    async def delete_file(file_id: int, user_id: int) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            knowledge_file = await KnowledgeFile.get(id=file_id).prefetch_related("knowledge_base")
            
            # 检查删除权限
            if not await knowledge_file.can_modify(user_id):
                return Fail(msg="无权限删除此文件")
            
            # 删除磁盘文件
            try:
                if os.path.exists(knowledge_file.file_path):
                    os.remove(knowledge_file.file_path)
            except Exception as e:
                logger.warning(f"删除磁盘文件失败: {e}")
            
            # 删除数据库记录
            kb = await knowledge_file.knowledge_base
            await knowledge_file.delete()
            
            # 更新知识库统计
            await kb.update_statistics()
            
            logger.info(f"删除文件成功: {file_id}")
            
            return Success(msg="文件删除成功")
            
        except DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return Fail(msg=f"删除文件失败: {str(e)}")
    
    @staticmethod
    async def retry_processing(file_id: int, user_id: int) -> Dict[str, Any]:
        """
        重试文件处理
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            重试结果
        """
        try:
            knowledge_file = await KnowledgeFile.get(id=file_id)
            
            # 检查修改权限
            if not await knowledge_file.can_modify(user_id):
                return Fail(msg="无权限操作此文件")
            
            # 只有失败的文件才能重试
            if knowledge_file.embedding_status != EmbeddingStatus.FAILED:
                return Fail(msg="只有处理失败的文件才能重试")
            
            # 重置状态
            knowledge_file.embedding_status = EmbeddingStatus.PENDING
            knowledge_file.error_message = None
            await knowledge_file.save(update_fields=["embedding_status", "error_message", "updated_at"])
            
            # TODO: 触发异步处理任务
            # await queue_file_processing(file_id)
            
            logger.info(f"重试文件处理: {file_id}")
            
            return Success(msg="已重新提交处理")
            
        except DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"重试文件处理失败: {e}")
            return Fail(msg=f"重试处理失败: {str(e)}")
    
    @staticmethod
    async def get_file_types() -> Dict[str, Any]:
        """获取支持的文件类型"""
        try:
            types = [
                {"value": ft.value, "label": ft.value.upper()}
                for ft in FileType
            ]
            return Success(data=types)
        except Exception as e:
            logger.error(f"获取文件类型失败: {e}")
            return Fail(msg=f"获取文件类型失败: {str(e)}")
    
    @staticmethod
    async def get_processing_statistics(kb_id: int, user_id: int) -> Dict[str, Any]:
        """获取文件处理统计信息"""
        try:
            # 检查知识库权限
            try:
                knowledge_base = await KnowledgeBase.get(id=kb_id)
            except DoesNotExist:
                return Fail(msg="知识库不存在")
            
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")
            
            # 统计各状态的文件数量
            files = await KnowledgeFile.filter(knowledge_base_id=kb_id)
            
            stats = {
                "total": len(files),
                "by_status": {},
                "by_type": {},
                "total_size": 0,
                "avg_size": 0
            }
            
            # 按状态统计
            for status in EmbeddingStatus:
                count = len([f for f in files if f.embedding_status == status])
                stats["by_status"][status.value] = count
            
            # 按类型统计
            for file_type in FileType:
                count = len([f for f in files if f.file_type == file_type])
                if count > 0:
                    stats["by_type"][file_type.value] = count
            
            # 大小统计
            total_size = sum(f.file_size for f in files if f.file_size)
            stats["total_size"] = total_size
            stats["avg_size"] = total_size / len(files) if files else 0
            
            return Success(data=stats)
            
        except Exception as e:
            logger.error(f"获取处理统计失败: {e}")
            return Fail(msg=f"获取处理统计失败: {str(e)}")
