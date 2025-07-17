from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from tortoise.expressions import Q

from a_app.controllers.knowledge import knowledge_base_controller, knowledge_file_controller
from a_app.utils.minio import file_storage
from a_app.core.dependency import AuthControl
from a_app.models.admin import User
from a_app.models.knowledge import KnowledgeFile
from a_app.schemas.base import Fail, Success, SuccessExtra
from a_app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from a_app.log import logger

router = APIRouter()


@router.get("/list", summary="查看知识库列表")
async def list_knowledge_base(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query(None, description="知识库名称"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    List knowledge bases

    Args:
        page: Page number
        page_size: Page size
        name: Filter by name
        user_id: Current user ID

    Returns:
        List of knowledge bases
    """
    total, kb_objs = await knowledge_base_controller.get_knowledge_bases(
        page=page, page_size=page_size, name=name, user_id=current_user.id
    )

    # Convert to response format with file counts
    data = []
    for kb in kb_objs:
        kb_dict = await kb.to_dict()
        # Count files in this knowledge base
        files_count = await kb.files.all().count()
        kb_dict["files_count"] = files_count
        data.append(kb_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看知识库详情")
async def get_knowledge_base(
    id: int = Query(..., description="知识库ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Get knowledge base details

    Args:
        id: Knowledge base ID
        user_id: Current user ID

    Returns:
        Knowledge base details
    """
    kb_obj = await knowledge_base_controller.get(id=id)

    # Check if the user has access to this knowledge base
    if not kb_obj.is_public and kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to access this knowledge base")

    kb_dict = await kb_obj.to_dict()

    # Count files in this knowledge base
    files_count = await kb_obj.files.all().count()
    kb_dict["files_count"] = files_count

    return Success(data=kb_dict)


@router.post("/create", summary="创建知识库")
async def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Create a new knowledge base

    Args:
        kb_in: Knowledge base creation data
        user_id: Current user ID

    Returns:
        Success message
    """
    # Check if the user is an admin for creating public knowledge bases
    if kb_in.is_public and not current_user.is_superuser:
        return Fail(code=403, msg="Only administrators can create public knowledge bases")

    await knowledge_base_controller.create_knowledge_base(obj_in=kb_in, user_id=current_user.id)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新知识库")
async def update_knowledge_base(
    kb_in: KnowledgeBaseUpdate,
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Update a knowledge base

    Args:
        kb_in: Knowledge base update data
        user_id: Current user ID

    Returns:
        Success message
    """
    kb_obj = await knowledge_base_controller.get(id=kb_in.id)

    # Only the owner can update the knowledge base
    if kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to update this knowledge base")

    # Check if the user is an admin for updating to public knowledge base
    if kb_in.is_public and not kb_obj.is_public:
        if not current_user.is_superuser:
            return Fail(code=403, msg="Only administrators can make knowledge bases public")

    await knowledge_base_controller.update(id=kb_in.id, obj_in=kb_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除知识库")
async def delete_knowledge_base(
    id: int = Query(..., description="知识库ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Delete a knowledge base

    Args:
        id: Knowledge base ID
        user_id: Current user ID

    Returns:
        Success message
    """
    kb_obj = await knowledge_base_controller.get(id=id)

    # Only the owner can delete the knowledge base
    if kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to delete this knowledge base")

    # Get all files in this knowledge base
    files = await kb_obj.files.all()

    # Delete all files from MinIO
    from a_app.utils.minio import file_storage as minio_client

    if files:
        file_paths = [file.file_path for file in files]
        minio_client.delete_files(file_paths)

    # Delete the knowledge base from vector database
    from a_app.chromadb.customer_vector import customer_vector_db
    try:
        if hasattr(customer_vector_db, 'chroma_client') and customer_vector_db.chroma_client is not None:
            await customer_vector_db.delete_knowledge_base(
                knowledge_base_id=id,
                knowledge_type=kb_obj.knowledge_type,
                is_public=kb_obj.is_public,
                owner_id=kb_obj.owner_id
            )
            logger.info(f"Deleted knowledge base {id} from vector database with type {kb_obj.knowledge_type}")
        else:
            logger.warning("ChromaDB not available. Skipping vector database deletion.")
    except Exception as e:
        logger.error(f"Error deleting knowledge base from vector database: {e}")

    # Delete the knowledge base (cascade delete will remove file records)
    await knowledge_base_controller.remove(id=id)

    return Success(msg="Deleted Successfully")


@router.get("/files", summary="查看知识库文件列表")
async def list_knowledge_files(
    knowledge_base_id: int = Query(..., description="知识库ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query(None, description="文件名称"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    List files in a knowledge base

    Args:
        knowledge_base_id: Knowledge base ID
        page: Page number
        page_size: Page size
        name: Filter by name
        user_id: Current user ID

    Returns:
        List of files
    """
    # Check if the user has access to this knowledge base
    kb_obj = await knowledge_base_controller.get(id=knowledge_base_id)
    if not kb_obj.is_public and kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to access this knowledge base")

    # Build query
    q = Q(knowledge_base_id=knowledge_base_id)
    if name:
        q &= Q(name__contains=name)

    # Get files
    total, file_objs = await knowledge_file_controller.list(
        page=page, page_size=page_size, search=q, order=["-created_at"]
    )

    # Convert to response format with download URLs
    data = []
    for file_obj in file_objs:
        file_dict = await file_obj.to_dict()

        # Generate a presigned URL for the file
        try:
            from a_app.utils.minio import minio_client
            file_dict["download_url"] = minio_client.get_presigned_url(file_obj.file_path)
        except Exception as e:
            file_dict["download_url"] = None

        data.append(file_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/file", summary="查看文件详情")
async def get_knowledge_file(
    id: int = Query(..., description="文件ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Get file details

    Args:
        id: File ID
        user_id: Current user ID

    Returns:
        File details
    """
    file_obj = await knowledge_file_controller.get(id=id)
    kb_obj = await file_obj.knowledge_base

    # Check if the user has access to this knowledge base
    if not kb_obj.is_public and kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to access this file")

    file_dict = await knowledge_file_controller.get_file_with_url(file_id=id)
    return Success(data=file_dict)


@router.delete("/file/delete", summary="删除文件")
async def delete_knowledge_file(
    id: int = Query(..., description="文件ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Delete a file

    Args:
        id: File ID
        user_id: Current user ID

    Returns:
        Success message
    """
    file_obj = await knowledge_file_controller.get(id=id)
    kb_obj = await file_obj.knowledge_base

    # Only the owner can delete files
    if kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to delete this file")

    await knowledge_file_controller.delete_file(file_id=id, user_id=current_user.id)
    return Success(msg="Deleted Successfully")


@router.post("/upload", summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    knowledge_base_id: int = Form(...),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Upload a file to a knowledge base

    Args:
        file: The file to upload
        knowledge_base_id: Knowledge base ID
        user_id: Current user ID

    Returns:
        Success message
    """
    # 直接处理文件上传，但不等待文件处理完成
    # 这样可以确保文件已经上传到服务器，但不需要等待处理完成
    file_obj = await knowledge_file_controller.upload_file(
        file=file, knowledge_base_id=knowledge_base_id, user_id=current_user.id
    )

    # 立即返回成功响应，不等待文件处理完成
    return Success(msg="Uploaded Successfully")


@router.get("/download", summary="下载文件")
async def download_file(
    path: str = Query(..., description="文件路径"),
    current_user: User = Depends(AuthControl.is_authed),
):
    """
    Download a file

    Args:
        path: File path
        user_id: Current user ID

    Returns:
        File response
    """
    # Find the file in the database by path
    file_obj = await KnowledgeFile.filter(file_path=path).first()
    if not file_obj:
        return Fail(code=404, msg="File not found")

    # Check if the user has access to the knowledge base
    kb_obj = await file_obj.knowledge_base
    if not kb_obj.is_public and kb_obj.owner_id != current_user.id:
        return Fail(code=403, msg="You don't have permission to access this file")

    # Get the file from storage
    file_path = file_storage.get_file(path)
    if not file_path:
        return Fail(code=404, msg="File not found in storage")

    # Get file metadata for content type
    try:
        metadata = file_storage.get_file_metadata(path)
        content_type = metadata.get('content_type', 'application/octet-stream')
    except Exception:
        content_type = 'application/octet-stream'

    # Return the file as a response
    return FileResponse(
        path=str(file_path),
        filename=file_obj.name,
        media_type=content_type,
    )
