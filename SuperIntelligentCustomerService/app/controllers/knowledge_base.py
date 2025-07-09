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
            # 验证知识库类型
            valid_types = [kt.value for kt in KnowledgeType]
            if knowledge_type not in valid_types:
                return Fail(msg=f"无效的知识库类型: {knowledge_type}")
            
            # 检查名称是否重复（同一用户下）
            existing = await KnowledgeBase.filter(
                name=name, 
                owner_id=owner_id
            ).first()
            
            if existing:
                return Fail(msg="知识库名称已存在")
            
            # 创建知识库
            kb_data = {
                "name": name,
                "description": description,
                "knowledge_type": knowledge_type,
                "is_public": is_public,
                "owner_id": owner_id,
                "last_updated_by": owner_id,
            }
            
            # 添加可选配置
            if "max_file_size" in kwargs:
                kb_data["max_file_size"] = kwargs["max_file_size"]
            if "allowed_file_types" in kwargs:
                kb_data["allowed_file_types"] = kwargs["allowed_file_types"]
            if "embedding_model" in kwargs:
                kb_data["embedding_model"] = kwargs["embedding_model"]
            if "chunk_size" in kwargs:
                kb_data["chunk_size"] = kwargs["chunk_size"]
            if "chunk_overlap" in kwargs:
                kb_data["chunk_overlap"] = kwargs["chunk_overlap"]
            
            knowledge_base = await KnowledgeBase.create(**kb_data)
            
            logger.info(f"创建知识库成功: {knowledge_base.id} - {name}")
            
            return Success(
                data=await knowledge_base.to_dict(),
                msg="知识库创建成功"
            )
            
        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            return Fail(msg=f"创建知识库失败: {str(e)}")
    
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
            query = Q()
            
            # 权限过滤：公开的或者自己拥有的
            query &= Q(is_public=True) | Q(owner_id=user_id)
            
            # 类型过滤
            if knowledge_type:
                query &= Q(knowledge_type=knowledge_type)
            
            # 公开状态过滤
            if is_public is not None:
                query &= Q(is_public=is_public)
            
            # 搜索过滤
            if search:
                query &= Q(name__icontains=search) | Q(description__icontains=search)
            
            # 只显示激活的知识库
            query &= Q(is_active=True)
            
            # 计算总数
            total = await KnowledgeBase.filter(query).count()
            
            # 分页查询
            offset = (page - 1) * page_size
            knowledge_bases = await KnowledgeBase.filter(query).offset(offset).limit(page_size).order_by("-created_at")
            
            # 转换为字典并添加统计信息
            kb_list = []
            for kb in knowledge_bases:
                kb_dict = await kb.to_dict()
                
                # 添加文件统计
                files = await kb.files.all()
                kb_dict["file_count"] = len(files)
                kb_dict["total_size"] = sum(f.file_size for f in files if f.file_size)
                
                # 添加权限信息
                kb_dict["can_modify"] = await kb.can_modify(user_id)
                
                kb_list.append(kb_dict)
            
            return Success(data={
                "items": kb_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return Fail(msg=f"获取知识库列表失败: {str(e)}")
    
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
            
            logger.info(f"更新知识库成功: {kb_id}")
            
            return Success(
                data=await knowledge_base.to_dict(),
                msg="知识库更新成功"
            )
            
        except DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            return Fail(msg=f"更新知识库失败: {str(e)}")
    
    @staticmethod
    async def delete_knowledge_base(kb_id: int, user_id: int) -> Dict[str, Any]:
        """
        删除知识库
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            knowledge_base = await KnowledgeBase.get(id=kb_id)
            
            # 检查删除权限
            if not await knowledge_base.can_modify(user_id):
                return Fail(msg="无权限删除此知识库")
            
            # 软删除：标记为非激活状态
            knowledge_base.is_active = False
            knowledge_base.last_updated_by = user_id
            await knowledge_base.save(update_fields=["is_active", "last_updated_by", "updated_at"])
            
            logger.info(f"删除知识库成功: {kb_id}")
            
            return Success(msg="知识库删除成功")
            
        except DoesNotExist:
            return Fail(msg="知识库不存在")
        except Exception as e:
            logger.error(f"删除知识库失败: {e}")
            return Fail(msg=f"删除知识库失败: {str(e)}")
    
    @staticmethod
    async def get_knowledge_types() -> Dict[str, Any]:
        """获取所有知识库类型"""
        try:
            types = [
                {"value": kt.value, "label": kt.value.title()}
                for kt in KnowledgeType
            ]
            return Success(data=types)
        except Exception as e:
            logger.error(f"获取知识库类型失败: {e}")
            return Fail(msg=f"获取知识库类型失败: {str(e)}")
    
    @staticmethod
    async def get_user_statistics(user_id: int) -> Dict[str, Any]:
        """获取用户知识库统计信息"""
        try:
            # 用户拥有的知识库
            owned_kbs = await KnowledgeBase.filter(owner_id=user_id, is_active=True)
            
            # 可访问的公共知识库
            public_kbs = await KnowledgeBase.filter(is_public=True, is_active=True)
            
            # 统计信息
            stats = {
                "owned_count": len(owned_kbs),
                "accessible_count": len(public_kbs),
                "total_files": 0,
                "total_size": 0,
                "by_type": {}
            }
            
            # 按类型统计
            for kb in owned_kbs:
                kb_type = kb.knowledge_type
                if kb_type not in stats["by_type"]:
                    stats["by_type"][kb_type] = {"count": 0, "files": 0, "size": 0}
                
                stats["by_type"][kb_type]["count"] += 1
                stats["total_files"] += kb.file_count
                stats["total_size"] += kb.total_size
                stats["by_type"][kb_type]["files"] += kb.file_count
                stats["by_type"][kb_type]["size"] += kb.total_size
            
            return Success(data=stats)
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return Fail(msg=f"获取用户统计信息失败: {str(e)}")
