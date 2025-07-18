"""
批量操作服务
实现知识库和文件的批量操作功能，包括批量上传、删除、处理等
"""
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from fastapi import UploadFile

from app.models.knowledge import KnowledgeBase, KnowledgeFile
from app.models.enums import EmbeddingStatus
from app.services.file_storage import file_storage
from app.services.file_processor import start_file_processing
from app.services.knowledge_permission_service import check_knowledge_base_access, check_file_access
from app.log import logger


@dataclass
class BatchOperationResult:
    """批量操作结果"""
    total: int = 0
    success: int = 0
    failed: int = 0
    success_items: List[Dict[str, Any]] = None
    failed_items: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.success_items is None:
            self.success_items = []
        if self.failed_items is None:
            self.failed_items = []
    
    def add_success(self, item: Dict[str, Any]):
        """添加成功项"""
        self.success_items.append(item)
        self.success += 1
        self.total += 1
    
    def add_failed(self, item: Dict[str, Any], error: str):
        """添加失败项"""
        item["error"] = error
        self.failed_items.append(item)
        self.failed += 1
        self.total += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "success_rate": (self.success / self.total * 100) if self.total > 0 else 0,
            "success_items": self.success_items,
            "failed_items": self.failed_items
        }


class BatchOperationService:
    """批量操作服务"""
    
    def __init__(self):
        self.logger = logger
    
    async def batch_upload_files(
        self,
        knowledge_base_id: int,
        files: List[UploadFile],
        user_id: int,
        max_concurrent: int = 3
    ) -> BatchOperationResult:
        """
        批量上传文件
        
        Args:
            knowledge_base_id: 知识库ID
            files: 文件列表
            user_id: 用户ID
            max_concurrent: 最大并发数
            
        Returns:
            批量操作结果
        """
        result = BatchOperationResult()
        
        try:
            # 检查知识库权限
            if not await check_knowledge_base_access(knowledge_base_id, user_id, "write"):
                for file in files:
                    result.add_failed(
                        {"filename": file.filename},
                        "无权限上传到该知识库"
                    )
                return result
            
            # 获取知识库信息
            kb = await KnowledgeBase.get_or_none(id=knowledge_base_id)
            if not kb:
                for file in files:
                    result.add_failed(
                        {"filename": file.filename},
                        "知识库不存在"
                    )
                return result
            
            # 创建信号量控制并发
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # 创建上传任务
            tasks = []
            for file in files:
                task = asyncio.create_task(
                    self._upload_single_file(semaphore, kb, file, user_id, result)
                )
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.info(f"批量上传完成: 成功 {result.success}, 失败 {result.failed}")
            return result
            
        except Exception as e:
            self.logger.error(f"批量上传失败: {e}")
            for file in files:
                if not any(item.get("filename") == file.filename for item in result.success_items + result.failed_items):
                    result.add_failed(
                        {"filename": file.filename},
                        f"批量上传异常: {str(e)}"
                    )
            return result
    
    async def _upload_single_file(
        self,
        semaphore: asyncio.Semaphore,
        kb: KnowledgeBase,
        file: UploadFile,
        user_id: int,
        result: BatchOperationResult
    ):
        """上传单个文件"""
        async with semaphore:
            try:
                # 检查文件类型
                file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
                if file_ext not in kb.allowed_file_types:
                    result.add_failed(
                        {"filename": file.filename},
                        f"不支持的文件类型: {file_ext}"
                    )
                    return
                
                # 检查文件大小
                file_content = await file.read()
                if len(file_content) > kb.max_file_size:
                    result.add_failed(
                        {"filename": file.filename},
                        f"文件大小超过限制: {len(file_content)} > {kb.max_file_size}"
                    )
                    return
                
                # 重置文件指针
                await file.seek(0)
                
                # 保存文件
                file_path = await file_storage.save_file(file, kb.id)
                
                # 计算文件哈希
                import hashlib
                file_hash = hashlib.md5(file_content).hexdigest()
                
                # 创建文件记录
                knowledge_file = await KnowledgeFile.create(
                    name=file.filename,
                    original_name=file.filename,
                    file_path=file_path,
                    file_size=len(file_content),
                    file_type=file_ext,
                    file_hash=file_hash,
                    knowledge_base_id=kb.id,
                    embedding_status=EmbeddingStatus.PENDING
                )
                
                # 启动文件处理
                start_file_processing(knowledge_file.id)
                
                result.add_success({
                    "file_id": knowledge_file.id,
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "status": "uploaded"
                })
                
            except Exception as e:
                result.add_failed(
                    {"filename": file.filename},
                    str(e)
                )
    
    async def batch_delete_files(
        self,
        file_ids: List[int],
        user_id: int
    ) -> BatchOperationResult:
        """
        批量删除文件
        
        Args:
            file_ids: 文件ID列表
            user_id: 用户ID
            
        Returns:
            批量操作结果
        """
        result = BatchOperationResult()
        
        try:
            for file_id in file_ids:
                try:
                    # 检查文件权限
                    if not await check_file_access(file_id, user_id, "write"):
                        result.add_failed(
                            {"file_id": file_id},
                            "无权限删除该文件"
                        )
                        continue
                    
                    # 获取文件信息
                    file_obj = await KnowledgeFile.get_or_none(id=file_id)
                    if not file_obj:
                        result.add_failed(
                            {"file_id": file_id},
                            "文件不存在"
                        )
                        continue
                    
                    # 软删除文件
                    file_obj.is_deleted = True
                    file_obj.deleted_at = datetime.now()
                    await file_obj.save()
                    
                    # 删除物理文件
                    try:
                        file_storage.delete_file(file_obj.file_path)
                    except Exception as e:
                        self.logger.warning(f"删除物理文件失败: {e}")
                    
                    result.add_success({
                        "file_id": file_id,
                        "filename": file_obj.name,
                        "status": "deleted"
                    })
                    
                except Exception as e:
                    result.add_failed(
                        {"file_id": file_id},
                        str(e)
                    )
            
            self.logger.info(f"批量删除完成: 成功 {result.success}, 失败 {result.failed}")
            return result
            
        except Exception as e:
            self.logger.error(f"批量删除失败: {e}")
            return result
    
    async def batch_reprocess_files(
        self,
        file_ids: List[int],
        user_id: int
    ) -> BatchOperationResult:
        """
        批量重新处理文件
        
        Args:
            file_ids: 文件ID列表
            user_id: 用户ID
            
        Returns:
            批量操作结果
        """
        result = BatchOperationResult()
        
        try:
            for file_id in file_ids:
                try:
                    # 检查文件权限
                    if not await check_file_access(file_id, user_id, "write"):
                        result.add_failed(
                            {"file_id": file_id},
                            "无权限重新处理该文件"
                        )
                        continue
                    
                    # 获取文件信息
                    file_obj = await KnowledgeFile.get_or_none(id=file_id)
                    if not file_obj:
                        result.add_failed(
                            {"file_id": file_id},
                            "文件不存在"
                        )
                        continue
                    
                    # 重置处理状态
                    file_obj.embedding_status = EmbeddingStatus.PENDING
                    file_obj.embedding_error = None
                    file_obj.processed_at = None
                    file_obj.chunk_count = 0
                    file_obj.vector_ids = []
                    await file_obj.save()
                    
                    # 启动重新处理
                    start_file_processing(file_id)
                    
                    result.add_success({
                        "file_id": file_id,
                        "filename": file_obj.name,
                        "status": "reprocessing"
                    })
                    
                except Exception as e:
                    result.add_failed(
                        {"file_id": file_id},
                        str(e)
                    )
            
            self.logger.info(f"批量重新处理完成: 成功 {result.success}, 失败 {result.failed}")
            return result
            
        except Exception as e:
            self.logger.error(f"批量重新处理失败: {e}")
            return result
    
    async def batch_export_knowledge_bases(
        self,
        kb_ids: List[int],
        user_id: int,
        export_format: str = "json"
    ) -> BatchOperationResult:
        """
        批量导出知识库
        
        Args:
            kb_ids: 知识库ID列表
            user_id: 用户ID
            export_format: 导出格式
            
        Returns:
            批量操作结果
        """
        result = BatchOperationResult()
        
        try:
            for kb_id in kb_ids:
                try:
                    # 检查知识库权限
                    if not await check_knowledge_base_access(kb_id, user_id, "read"):
                        result.add_failed(
                            {"kb_id": kb_id},
                            "无权限导出该知识库"
                        )
                        continue
                    
                    # 获取知识库信息
                    kb = await KnowledgeBase.get_or_none(id=kb_id)
                    if not kb:
                        result.add_failed(
                            {"kb_id": kb_id},
                            "知识库不存在"
                        )
                        continue
                    
                    # 导出知识库数据
                    export_data = await self._export_knowledge_base(kb, export_format)
                    
                    result.add_success({
                        "kb_id": kb_id,
                        "name": kb.name,
                        "export_data": export_data,
                        "status": "exported"
                    })
                    
                except Exception as e:
                    result.add_failed(
                        {"kb_id": kb_id},
                        str(e)
                    )
            
            self.logger.info(f"批量导出完成: 成功 {result.success}, 失败 {result.failed}")
            return result
            
        except Exception as e:
            self.logger.error(f"批量导出失败: {e}")
            return result
    
    async def _export_knowledge_base(self, kb: KnowledgeBase, format: str) -> Dict[str, Any]:
        """导出知识库数据"""
        # 获取知识库文件
        files = await kb.files.filter(is_deleted=False).all()
        
        export_data = {
            "knowledge_base": {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "knowledge_type": kb.knowledge_type,
                "created_at": kb.created_at.isoformat(),
                "config": kb.config
            },
            "files": []
        }
        
        for file_obj in files:
            file_data = {
                "id": file_obj.id,
                "name": file_obj.name,
                "original_name": file_obj.original_name,
                "file_size": file_obj.file_size,
                "file_type": file_obj.file_type,
                "embedding_status": file_obj.embedding_status,
                "chunk_count": file_obj.chunk_count,
                "created_at": file_obj.created_at.isoformat()
            }
            
            # 如果需要，可以包含文件内容
            if format == "full":
                try:
                    file_content = file_storage.read_file(file_obj.file_path)
                    file_data["content"] = file_content.decode('utf-8', errors='ignore')
                except:
                    file_data["content"] = None
            
            export_data["files"].append(file_data)
        
        return export_data


# 全局批量操作服务实例
batch_operation_service = BatchOperationService()
