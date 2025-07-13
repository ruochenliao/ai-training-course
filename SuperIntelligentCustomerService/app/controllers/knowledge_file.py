"""
知识文件控制器
提供知识文件的上传、管理和处理功能
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import UploadFile
from tortoise.exceptions import DoesNotExist

from ..models.enums import FileType, EmbeddingStatus
from ..models.knowledge import KnowledgeBase, KnowledgeFile
from ..schemas.base import SuccessExtra
from ..utils.response import Success, Fail

logger = logging.getLogger(__name__)


class KnowledgeFileController:
    """知识文件控制器"""
    
    @staticmethod
    def _get_file_type_from_filename(filename: str) -> Optional[FileType]:
        """从文件名获取文件类型"""
        if not filename:
            return None
        
        ext = filename.lower().split('.')[-1]
        type_mapping = {
            'pdf': FileType.PDF,
            'docx': FileType.DOCX,
            'doc': FileType.DOCX,
            'txt': FileType.TXT,
            'md': FileType.MD,
            'jpg': FileType.JPG,
            'jpeg': FileType.JPG,
            'png': FileType.PNG,
            'xlsx': FileType.XLSX,
            'xls': FileType.XLSX,
            'pptx': FileType.PPTX,
            'ppt': FileType.PPTX
        }
        
        return type_mapping.get(ext)
    
    @staticmethod
    def _get_file_hash(content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def _get_upload_path(kb_id: int, filename: str) -> str:
        """生成文件上传路径"""
        # 创建上传目录
        upload_dir = Path("uploads") / "knowledge" / str(kb_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        import uuid
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else str(uuid.uuid4().hex)
        
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
            
            # 创建文件记录
            knowledge_file = await KnowledgeFile.create(
                name=file.filename,
                original_name=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                file_hash=file_hash,
                knowledge_base_id=kb_id,
                uploaded_by=user_id,
                embedding_status=EmbeddingStatus.PENDING
            )
            
            # 更新知识库统计
            knowledge_base.file_count += 1
            knowledge_base.total_size += file_size
            await knowledge_base.save(update_fields=["file_count", "total_size", "updated_at"])

            # 触发文件处理
            try:
                from ..controllers.file_processor import FileProcessor
                processor = FileProcessor()
                # 异步处理文件，不阻塞响应
                import asyncio
                asyncio.create_task(processor.process_file(knowledge_file.id))
                logger.info(f"已启动文件处理任务: {knowledge_file.id}")
            except Exception as e:
                logger.error(f"启动文件处理失败: {e}")

            file_dict = await knowledge_file.to_dict()
            return Success(data=file_dict, msg="文件上传成功")

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return Fail(msg="文件上传失败")


    @staticmethod
    async def retry_file_processing(
        knowledge_id: int,
        file_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """重试文件处理"""
        try:
            # 检查知识库权限
            knowledge_base = await KnowledgeBase.get(id=knowledge_id)
            if not await knowledge_base.can_modify(user_id):
                return Fail(msg="无权限操作此知识库")

            # 获取文件信息
            knowledge_file = await KnowledgeFile.get(id=file_id, knowledge_base_id=knowledge_id)

            # 检查文件状态
            if knowledge_file.embedding_status not in [EmbeddingStatus.FAILED, EmbeddingStatus.PENDING]:
                return Fail(msg="只能重试失败或待处理的文件")

            # 重置文件状态为待处理
            knowledge_file.embedding_status = EmbeddingStatus.PENDING
            knowledge_file.error_message = None
            await knowledge_file.save(update_fields=["embedding_status", "error_message", "updated_at"])

            # 触发文件处理
            try:
                from .file_processor import file_processor
                # 异步处理文件，不阻塞响应
                import asyncio
                asyncio.create_task(file_processor.process_file(knowledge_file.id))
                logger.info(f"已启动文件重试处理任务: {knowledge_file.id}")
            except Exception as e:
                logger.error(f"启动文件重试处理失败: {e}")
                return Fail(msg=f"启动处理失败: {str(e)}")

            file_dict = await knowledge_file.to_dict()
            return Success(data=file_dict, msg="重试处理已启动")

        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except KnowledgeFile.DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"重试文件处理失败: {e}")
            return Fail(msg="重试处理失败")
    
    @staticmethod
    async def list_files(
        kb_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
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
            query_filter = {"knowledge_base_id": kb_id, "is_deleted": False}
            
            if status:
                query_filter["embedding_status"] = status
            
            # 计算总数
            total = await KnowledgeFile.filter(**query_filter).count()
            
            # 分页查询
            offset = (page - 1) * page_size
            files = await KnowledgeFile.filter(**query_filter).offset(offset).limit(page_size).order_by('-created_at')
            
            # 如果有搜索条件，进一步过滤
            if search:
                files = [f for f in files if search.lower() in f.name.lower()]
            
            # 转换为字典格式
            file_list = []
            for file in files:
                file_dict = await file.to_dict()
                file_list.append(file_dict)
            
            return SuccessExtra(
                data=file_list,
                total=total,
                page=page,
                page_size=page_size
            )
            
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
            
            # 检查权限
            if not await knowledge_file.can_modify(user_id):
                return Fail(msg="无权限删除此文件")
            
            # 软删除文件
            knowledge_file.is_deleted = True
            await knowledge_file.save(update_fields=["is_deleted", "updated_at"])
            
            # 更新知识库统计
            kb = await knowledge_file.knowledge_base
            kb.file_count = max(0, kb.file_count - 1)
            kb.total_size = max(0, kb.total_size - knowledge_file.file_size)
            await kb.save(update_fields=["file_count", "total_size", "updated_at"])
            
            # 删除物理文件
            try:
                if os.path.exists(knowledge_file.file_path):
                    os.remove(knowledge_file.file_path)
            except Exception as e:
                logger.warning(f"删除物理文件失败: {e}")
            
            return Success(msg="文件删除成功")
            
        except DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return Fail(msg=f"删除文件失败: {str(e)}")
    
    @staticmethod
    async def get_file_statistics(kb_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取文件统计信息
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            # 检查权限
            try:
                knowledge_base = await KnowledgeBase.get(id=kb_id)
            except DoesNotExist:
                return Fail(msg="知识库不存在")
            
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")
            
            # 获取所有文件
            files = await KnowledgeFile.filter(knowledge_base_id=kb_id, is_deleted=False).all()
            
            # 统计信息
            total = len(files)
            by_status = {}
            by_type = {}
            total_size = 0
            
            for file in files:
                # 按状态统计
                status = file.embedding_status.value if file.embedding_status else 'unknown'
                by_status[status] = by_status.get(status, 0) + 1
                
                # 按类型统计
                file_type = file.file_type.value if file.file_type else 'unknown'
                by_type[file_type] = by_type.get(file_type, 0) + 1
                
                # 总大小
                total_size += file.file_size or 0
            
            stats = {
                "total": total,
                "by_status": by_status,
                "by_type": by_type,
                "total_size": total_size
            }
            
            return Success(data=stats)
            
        except Exception as e:
            logger.error(f"获取文件统计失败: {e}")
            return Fail(msg=f"获取文件统计失败: {str(e)}")
