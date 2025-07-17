import os
import uuid
import tempfile
from typing import List, Optional, Tuple
from pathlib import Path

from fastapi import HTTPException, UploadFile
from tortoise.expressions import Q

from a_app.core.crud import CRUDBase
from a_app.log import logger
from a_app.models.knowledge import KnowledgeBase, KnowledgeFile
from a_app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeFileCreate, KnowledgeFileUpdate
from a_app.utils.minio import file_storage
from a_app.chromadb.customer_vector import customer_vector_db

# Import marker for document conversion
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    logger.warning("Marker library not available. Document to markdown conversion will be disabled.")
    MARKER_AVAILABLE = False


class KnowledgeBaseController(CRUDBase[KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate]):
    """Controller for knowledge base operations"""

    def __init__(self):
        super().__init__(model=KnowledgeBase)

    async def get_knowledge_bases(
        self, page: int, page_size: int, name: Optional[str] = None, user_id: Optional[int] = None
    ) -> Tuple[int, List[KnowledgeBase]]:
        """
        Get knowledge bases with filtering

        Args:
            page: Page number
            page_size: Page size
            name: Filter by name
            user_id: Filter by user ID

        Returns:
            Tuple of (total, knowledge_bases)
        """
        q = Q()

        # Filter by name if provided
        if name:
            q &= Q(name__contains=name)

        # If user_id is provided, get public knowledge bases and user's private knowledge bases
        if user_id:
            q &= (Q(is_public=True) | Q(owner_id=user_id))

        return await self.list(page=page, page_size=page_size, search=q)

    async def create_knowledge_base(self, obj_in: KnowledgeBaseCreate, user_id: int) -> KnowledgeBase:
        """
        Create a new knowledge base

        Args:
            obj_in: Knowledge base creation data
            user_id: User ID of the creator

        Returns:
            The created knowledge base
        """
        # Create a dict from obj_in and add owner_id
        obj_dict = obj_in.model_dump()
        obj_dict["owner_id"] = user_id

        # Create the knowledge base
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def check_knowledge_base_access(self, knowledge_base_id: int, user_id: int) -> bool:
        """
        Check if a user has access to a knowledge base

        Args:
            knowledge_base_id: Knowledge base ID
            user_id: User ID

        Returns:
            True if the user has access, False otherwise
        """
        kb = await self.get(id=knowledge_base_id)
        return kb.is_public or kb.owner_id == user_id


class KnowledgeFileController(CRUDBase[KnowledgeFile, KnowledgeFileCreate, KnowledgeFileUpdate]):
    """Controller for knowledge file operations"""

    def __init__(self):
        super().__init__(model=KnowledgeFile)

    async def upload_file(
        self, file: UploadFile, knowledge_base_id: int, user_id: int
    ) -> KnowledgeFile:
        """
        Upload a file to a knowledge base

        Args:
            file: The file to upload
            knowledge_base_id: Knowledge base ID
            user_id: User ID

        Returns:
            The created knowledge file
        """
        # Check if the user has access to the knowledge base
        kb_controller = knowledge_base_controller
        kb = await kb_controller.get(id=knowledge_base_id)

        # Only the owner can upload files
        if kb.owner_id != user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to upload files to this knowledge base")

        # Check file size (limit to 50MB)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        file_size = 0
        file_data = await file.read()
        file_size = len(file_data)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds the limit of 50MB")

        # 不需要重置文件位置，因为我们已经读取了文件数据
        # 并且将传递给 upload_file 方法

        # Check file extension
        ALLOWED_EXTENSIONS = {
            ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".md", ".bmp"
        }
        file_extension = os.path.splitext(file.filename)[1].lower() if "." in file.filename else ""

        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Generate a unique file path
        file_uuid = str(uuid.uuid4())
        object_name = f"{knowledge_base_id}/{file_uuid}{file_extension}"

        # 使用已经读取的文件数据上传文件
        # Upload the file to local storage
        success, message = await file_storage.upload_file(
            file=file,
            object_name=object_name,
            content_type=file.content_type,
            file_data=file_data,  # 传递已经读取的文件数据
        )

        if not success:
            raise HTTPException(status_code=500, detail=message)

        # Get file size
        file_path = file_storage.storage_dir / object_name
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # 知识库信息存入数据库
        file_obj = await self.create(
            KnowledgeFileCreate(
                name=file.filename,
                file_path=object_name,
                file_size=file_size,
                file_type=file.content_type or "application/octet-stream",
                knowledge_base_id=knowledge_base_id,
            )
        )

        # 在后台处理文件，不阻塞当前请求
        import asyncio

        async def process_file_in_background():
            try:
                from a_app.tasks.file_processor import file_processor

                # Only queue supported file types
                if file_extension.lower() in [".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".md", ".bmp"]:
                    # Start the file processor if not already running
                    if not file_processor._is_running:
                        await file_processor.start()

                    # Queue the file for processing
                    await file_processor.queue_file(file_obj.id)
                    logger.info(f"File {file_obj.id} queued for background processing")
                else:
                    # Mark unsupported files as failed
                    file_obj.embedding_status = "failed"
                    file_obj.embedding_error = f"Unsupported file type: {file_extension}"
                    await file_obj.save()
                    logger.warning(f"Skipping markdown conversion for file {file_obj.name} (unsupported type)")
            except Exception as e:
                logger.error(f"Error processing file in background: {e}")
                import traceback
                traceback.print_exc()

        # 启动后台任务处理文件
        asyncio.create_task(process_file_in_background())

        return file_obj

    async def get_file_with_url(self, file_id: int) -> dict:
        """
        Get a file with its download URL

        Args:
            file_id: File ID

        Returns:
            The file with its download URL
        """
        file_obj = await self.get(id=file_id)
        file_dict = await file_obj.to_dict()

        # Generate a URL for the file
        try:
            file_dict["download_url"] = file_storage.get_file_url(file_obj.file_path)
        except Exception as e:
            logger.error(f"Error generating file URL: {e}")
            file_dict["download_url"] = None

        return file_dict

    async def delete_file(self, file_id: int, user_id: int) -> None:
        """
        Delete a file

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            None
        """
        file_obj = await self.get(id=file_id)
        kb = await file_obj.knowledge_base

        # Only the owner can delete files
        if kb.owner_id != user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this file")

        # Delete the file from local storage
        success, message = file_storage.delete_file(file_obj.file_path)
        if not success:
            logger.error(f"Error deleting file from storage: {message}")

        # Delete the file from vector database
        try:
            if hasattr(customer_vector_db, 'chroma_client') and customer_vector_db.chroma_client is not None:
                await customer_vector_db.delete_file(
                    knowledge_base_id=kb.id,
                    file_id=file_id,
                    knowledge_type=kb.knowledge_type,
                    is_public=kb.is_public,
                    owner_id=kb.owner_id
                )
                logger.info(f"Deleted file {file_id} from vector database")
            else:
                logger.warning("ChromaDB not available. Skipping vector database deletion.")
        except Exception as e:
            logger.error(f"Error deleting file from vector database: {e}")

        # Delete the file record
        await file_obj.delete()


# Create singleton instances
knowledge_base_controller = KnowledgeBaseController()
knowledge_file_controller = KnowledgeFileController()
