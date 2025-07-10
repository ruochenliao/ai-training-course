"""
知识库控制器
提供知识库的CRUD操作和权限管理
"""
import logging
from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist, IntegrityError

from ..models.knowledge import KnowledgeBase, KnowledgeFile
from ..models.enums import KnowledgeType, EmbeddingStatus
from ..utils.response import Success, Fail
from ..schemas.base import SuccessExtra

logger = logging.getLogger(__name__)


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
            return Success(data=kb_dict, msg="知识库创建成功")
            
        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
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
            query = Q(is_deleted=False)
            
            # 权限过滤：只能看到自己的或公开的
            query &= Q(Q(owner_id=user_id) | Q(is_public=True))
            
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
            logger.error(f"获取知识库列表失败: {e}")
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
            knowledge_base = await KnowledgeBase.get(id=kb_id)
            
            # 检查访问权限
            if not await knowledge_base.can_access(user_id):
                return Fail(msg="无权限访问此知识库")
            
            # 获取详细信息
            kb_dict = await knowledge_base.to_dict()
            
            # 添加统计信息
            files = await knowledge_base.files.all()
            kb_dict["file_count"] = len(files)
            kb_dict["total_size"] = sum(f.file_size for f in files if f.file_size)
            
            # 按状态统计文件
            status_stats = {}
            for status in EmbeddingStatus:
                status_stats[status.value] = len([
                    f for f in files if f.embedding_status == status
                ])
            kb_dict["status_stats"] = status_stats
            
            return Success(data=kb_dict)
            
        except DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"获取知识库失败: {e}")
            return Fail(msg=f"获取知识库失败: {str(e)}")
    
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
            knowledge_base = await KnowledgeBase.get(id=kb_id)
            
            # 检查修改权限
            if not await knowledge_base.can_modify(user_id):
                return Fail(msg="无权限修改此知识库")
            
            # 过滤允许更新的字段
            allowed_fields = [
                "name", "description", "is_public", "knowledge_type",
                "max_file_size", "allowed_file_types", "embedding_model",
                "chunk_size", "chunk_overlap"
            ]
            
            update_fields = []
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(knowledge_base, field):
                    setattr(knowledge_base, field, value)
                    update_fields.append(field)
            
            if update_fields:
                knowledge_base.last_updated_by = user_id
                update_fields.extend(["last_updated_by", "updated_at"])
                await knowledge_base.save(update_fields=update_fields)
            
            kb_dict = await knowledge_base.to_dict()
            return Success(data=kb_dict, msg="知识库更新成功")
            
        except DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
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
            knowledge_base = await KnowledgeBase.get(id=kb_id)
            
            # 检查修改权限
            if not await knowledge_base.can_modify(user_id):
                return Fail(msg="无权限删除此知识库")
            
            # 软删除
            knowledge_base.is_deleted = True
            knowledge_base.last_updated_by = user_id
            await knowledge_base.save(update_fields=["is_deleted", "last_updated_by", "updated_at"])
            
            return Success(msg="知识库删除成功")
            
        except DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"删除知识库失败: {e}")
            return Fail(msg=f"删除知识库失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_types() -> Dict[str, Any]:
        """
        获取知识库类型列表
        
        Returns:
            知识库类型列表
        """
        try:
            types = [
                {"label": "通用", "value": "general"},
                {"label": "技术文档", "value": "technical"},
                {"label": "FAQ", "value": "faq"},
                {"label": "政策制度", "value": "policy"},
                {"label": "产品说明", "value": "product"}
            ]
            return Success(data=types)
        except Exception as e:
            logger.error(f"获取知识库类型失败: {e}")
            return Fail(msg=f"获取知识库类型失败: {str(e)}")
    
    @staticmethod
    async def get_user_statistics(user_id: int) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            # 统计用户的知识库
            total_kb = await KnowledgeBase.filter(owner_id=user_id, is_deleted=False).count()
            public_kb = await KnowledgeBase.filter(owner_id=user_id, is_public=True, is_deleted=False).count()
            private_kb = total_kb - public_kb
            
            # 统计文件
            total_files = await KnowledgeFile.filter(
                knowledge_base__owner_id=user_id,
                knowledge_base__is_deleted=False,
                is_deleted=False
            ).count()
            
            # 统计总大小
            files = await KnowledgeFile.filter(
                knowledge_base__owner_id=user_id,
                knowledge_base__is_deleted=False,
                is_deleted=False
            ).all()
            total_size = sum(f.file_size for f in files if f.file_size)
            
            stats = {
                "total_knowledge_bases": total_kb,
                "public_knowledge_bases": public_kb,
                "private_knowledge_bases": private_kb,
                "total_files": total_files,
                "total_size": total_size
            }
            
            return Success(data=stats)
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return Fail(msg=f"获取用户统计信息失败: {str(e)}")
