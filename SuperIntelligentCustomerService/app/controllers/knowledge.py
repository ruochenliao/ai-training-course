"""
知识库管理控制器
参考006项目的设计架构，实现知识库和文件的CRUD操作
"""
import os
from datetime import datetime

from fastapi import UploadFile
from tortoise.expressions import Q

from app.core.knowledge_exceptions import *
from app.log import logger
from app.models.enums import KnowledgeType, EmbeddingStatus
from app.models.knowledge import KnowledgeBase, KnowledgeFile
from app.schemas.base import Success, Fail, SuccessExtra
from app.services.file_processor import start_file_processing
from app.services.file_storage import file_storage
from app.services.unified_vector_service import delete_knowledge_base_file


class KnowledgeBaseController:
    """知识库控制器"""

    @staticmethod
    async def create_knowledge_base(
        name: str,
        description: str,
        knowledge_type: str,
        is_public: bool,
        owner_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            description: 描述
            knowledge_type: 知识库类型
            is_public: 是否公开
            owner_id: 所有者ID
            **kwargs: 其他配置参数
            
        Returns:
            创建结果
        """
        try:
            # 检查名称是否重复
            existing = await KnowledgeBase.filter(
                name=name, 
                owner_id=owner_id,
                is_deleted=False
            ).first()
            
            if existing:
                return Fail(msg="知识库名称已存在")
            
            # 创建知识库
            knowledge_base = await KnowledgeBase.create(
                name=name,
                description=description,
                knowledge_type=knowledge_type,
                is_public=is_public,
                owner_id=owner_id,
                **kwargs
            )
            
            kb_dict = await knowledge_base.to_dict()
            logger.info(f"知识库创建成功: {name}, ID: {knowledge_base.id}")
            return Success(data=kb_dict, msg="知识库创建成功")
            
        except Exception as e:
            logger.error(f"创建知识库失败: {str(e)}")
            return Fail(msg=f"创建知识库失败: {str(e)}")

    @staticmethod
    async def list_knowledge_bases(
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        knowledge_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识库列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            knowledge_type: 知识库类型过滤
            is_public: 公开状态过滤
            search: 搜索关键词
            
        Returns:
            知识库列表
        """
        try:
            # 构建查询条件
            query = await KnowledgeBase.get_accessible_query(user_id)
            
            # 类型过滤
            if knowledge_type:
                query &= Q(knowledge_type=knowledge_type)
            
            # 公开状态过滤
            if is_public is not None:
                query &= Q(is_public=is_public)
            
            # 搜索过滤
            if search:
                query &= Q(Q(name__icontains=search) | Q(description__icontains=search))
            
            # 计算总数
            total = await KnowledgeBase.filter(query).count()
            
            # 分页查询
            offset = (page - 1) * page_size
            knowledge_bases = await KnowledgeBase.filter(query).offset(offset).limit(page_size).order_by('-created_at')
            
            # 转换为字典格式
            kb_list = []
            for kb in knowledge_bases:
                kb_dict = await kb.to_dict()
                kb_list.append(kb_dict)

            return SuccessExtra(
                data=kb_list,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {str(e)}")
            return Fail(msg=f"获取知识库列表失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_base(kb_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取知识库详情
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            知识库信息
        """
        try:
            knowledge_base = await KnowledgeBase.get(id=kb_id, is_deleted=False)
            
            # 检查访问权限
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")
            
            # 获取详细信息
            kb_dict = await knowledge_base.to_dict()
            
            # 添加统计信息
            files = await knowledge_base.files.filter(is_deleted=False).all()
            kb_dict["file_count"] = len(files)
            kb_dict["total_size"] = sum(f.file_size for f in files if f.file_size)
            
            # 按状态统计文件
            status_stats = await KnowledgeFile.get_processing_stats(kb_id)
            kb_dict["status_stats"] = status_stats
            
            return Success(data=kb_dict)
            
        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"获取知识库详情失败: {str(e)}")
            return Fail(msg=f"获取知识库详情失败: {str(e)}")

    @staticmethod
    async def update_knowledge_base(
        kb_id: int,
        user_id: int,
        **update_data
    ) -> Dict[str, Any]:
        """
        更新知识库
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            **update_data: 更新数据
            
        Returns:
            更新结果
        """
        try:
            knowledge_base = await KnowledgeBase.get(id=kb_id, is_deleted=False)
            
            # 检查编辑权限
            if not await knowledge_base.can_edit(user_id):
                return Fail(msg="无权限编辑此知识库")
            
            # 如果更新名称，检查重复
            if 'name' in update_data:
                existing = await KnowledgeBase.filter(
                    name=update_data['name'],
                    owner_id=user_id,
                    is_deleted=False
                ).exclude(id=kb_id).first()
                
                if existing:
                    return Fail(msg="知识库名称已存在")
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(knowledge_base, field):
                    setattr(knowledge_base, field, value)
            
            knowledge_base.last_updated_at = datetime.now()
            await knowledge_base.save()
            
            kb_dict = await knowledge_base.to_dict()
            logger.info(f"知识库更新成功: {kb_id}")
            return Success(data=kb_dict, msg="知识库更新成功")
            
        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"更新知识库失败: {str(e)}")
            return Fail(msg=f"更新知识库失败: {str(e)}")

    @staticmethod
    async def delete_knowledge_base(kb_id: int, user_id: int) -> Dict[str, Any]:
        """
        删除知识库（软删除）
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            knowledge_base = await KnowledgeBase.get(id=kb_id, is_deleted=False)
            
            # 检查编辑权限
            if not await knowledge_base.can_edit(user_id):
                return Fail(msg="无权限删除此知识库")
            
            # 从向量数据库中删除 - 使用新的统一向量服务
            try:
                # 使用统一向量服务删除知识库
                from app.services.unified_vector_service import get_unified_vector_service, VectorCollectionType
                unified_service = get_unified_vector_service()
                await unified_service.delete_collection(
                    collection_type=VectorCollectionType.KNOWLEDGE_BASE,
                    identifier=str(kb_id),
                    is_public=knowledge_base.is_public,
                    owner_id=knowledge_base.owner_id
                )
            except Exception as e:
                logger.error(f"使用统一向量服务删除失败: {e}")
                # 删除失败，但继续删除数据库记录
                logger.info(f"成功从向量数据库删除知识库: {kb_id}")
            except Exception as e:
                logger.warning(f"从向量数据库删除知识库失败: {e}")

            # 软删除
            await knowledge_base.soft_delete()

            logger.info(f"知识库删除成功: {kb_id}")
            return Success(msg="知识库删除成功")
            
        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"删除知识库失败: {str(e)}")
            return Fail(msg=f"删除知识库失败: {str(e)}")

    @staticmethod
    async def get_knowledge_types() -> Dict[str, Any]:
        """
        获取所有可用的知识库类型
        
        Returns:
            知识库类型列表
        """
        try:
            types = [
                {"value": KnowledgeType.CUSTOMER_SERVICE, "label": "智能客服知识库"},
                {"value": KnowledgeType.TEXT_SQL, "label": "TextSQL知识库"},
                {"value": KnowledgeType.RAG, "label": "RAG知识库"},
                {"value": KnowledgeType.CONTENT_CREATION, "label": "文案创作知识库"},
                {"value": KnowledgeType.GENERAL, "label": "通用知识库"},
                {"value": KnowledgeType.TECHNICAL, "label": "技术文档"},
                {"value": KnowledgeType.FAQ, "label": "常见问题"},
                {"value": KnowledgeType.POLICY, "label": "政策文档"},
                {"value": KnowledgeType.PRODUCT, "label": "产品文档"},
            ]
            
            return Success(data=types)
            
        except Exception as e:
            logger.error(f"获取知识库类型失败: {str(e)}")
            return Fail(msg=f"获取知识库类型失败: {str(e)}")


class KnowledgeFileController:
    """知识文件控制器"""

    @staticmethod
    async def upload_file(
        knowledge_base_id: int,
        file: UploadFile,
        user_id: int
    ) -> Dict[str, Any]:
        """
        上传文件到知识库

        Args:
            knowledge_base_id: 知识库ID
            file: 上传的文件
            user_id: 用户ID

        Returns:
            上传结果
        """
        try:
            # 检查知识库是否存在和权限
            knowledge_base = await KnowledgeBase.get(id=knowledge_base_id, is_deleted=False)
            if not await knowledge_base.can_edit(user_id):
                return Fail(msg="无权限上传文件到此知识库")

            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)

            # 检查文件大小
            if file_size > knowledge_base.max_file_size:
                return Fail(msg=f"文件大小超过限制({knowledge_base.max_file_size} 字节)")

            # 检查文件类型
            file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            if file_ext not in knowledge_base.allowed_file_types:
                return Fail(msg=f"不支持的文件类型: {file_ext}")

            # 计算文件哈希
            file_hash = KnowledgeFile.calculate_file_hash(file_content)

            # 检查重复文件
            existing_file = await KnowledgeFile.check_duplicate(knowledge_base_id, file_hash)
            if existing_file:
                return Fail(msg="文件已存在")

            # 重置文件指针到开头
            await file.seek(0)

            # 保存文件到存储服务
            file_path = await file_storage.save_file(file, knowledge_base_id)

            # 创建文件记录
            knowledge_file = await KnowledgeFile.create(
                name=file.filename,
                original_name=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file.content_type or f"application/{file_ext}",
                file_hash=file_hash,
                knowledge_base_id=knowledge_base_id,
                embedding_status=EmbeddingStatus.PENDING
            )

            # 更新知识库统计
            await knowledge_base.update_stats()

            file_dict = await knowledge_file.to_dict()
            logger.info(f"文件上传成功: {file.filename}, ID: {knowledge_file.id}")

            # 启动后台文件处理任务
            start_file_processing(knowledge_file.id)

            return Success(data=file_dict, msg="文件上传成功")

        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return Fail(msg=f"文件上传失败: {str(e)}")

    @staticmethod
    async def list_files(
        knowledge_base_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识库文件列表

        Args:
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            status: 状态过滤

        Returns:
            文件列表
        """
        try:
            # 检查知识库访问权限
            knowledge_base = await KnowledgeBase.get(id=knowledge_base_id, is_deleted=False)
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")

            # 构建查询条件
            query = Q(knowledge_base_id=knowledge_base_id, is_deleted=False)

            # 状态过滤
            if status:
                query &= Q(embedding_status=status)

            # 计算总数
            total = await KnowledgeFile.filter(query).count()

            # 分页查询
            offset = (page - 1) * page_size
            files = await KnowledgeFile.filter(query).offset(offset).limit(page_size).order_by('-created_at')

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

        except KnowledgeBase.DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"获取文件列表失败: {str(e)}")
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
            knowledge_file = await KnowledgeFile.get(id=file_id, is_deleted=False)
            knowledge_base = await knowledge_file.knowledge_base

            # 检查编辑权限
            if not await knowledge_base.can_edit(user_id):
                return Fail(msg="无权限删除此文件")

            # 从向量数据库中删除
            try:
                await delete_knowledge_base_file(
                    knowledge_base_id=knowledge_base.id,
                    file_id=file_id
                )
                logger.info(f"成功从向量数据库删除文件: {file_id}")
            except Exception as e:
                logger.warning(f"从向量数据库删除文件失败: {e}")

            # 软删除文件
            await knowledge_file.soft_delete()

            logger.info(f"文件删除成功: {file_id}")
            return Success(msg="文件删除成功")

        except KnowledgeFile.DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return Fail(msg=f"删除文件失败: {str(e)}")

    @staticmethod
    async def get_file_info(file_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_id: 文件ID
            user_id: 用户ID

        Returns:
            文件信息
        """
        try:
            knowledge_file = await KnowledgeFile.get(id=file_id, is_deleted=False)
            knowledge_base = await knowledge_file.knowledge_base

            # 检查访问权限
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此文件")

            file_dict = await knowledge_file.to_dict()
            return Success(data=file_dict)

        except KnowledgeFile.DoesNotExist:
            return Fail(msg="文件不存在")
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return Fail(msg=f"获取文件信息失败: {str(e)}")


# 全局控制器实例
knowledge_base_controller = KnowledgeBaseController()
knowledge_file_controller = KnowledgeFileController()
