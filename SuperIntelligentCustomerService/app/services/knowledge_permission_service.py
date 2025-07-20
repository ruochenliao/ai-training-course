"""
知识库权限控制服务
实现知识库的访问权限控制、用户权限验证等功能
"""
from enum import Enum
from typing import List, Dict, Any

from app.log import logger
from app.models.admin import User
from app.models.knowledge import KnowledgeBase, KnowledgeFile


class PermissionLevel(Enum):
    """权限级别"""
    NONE = "none"           # 无权限
    READ = "read"           # 只读权限
    WRITE = "write"         # 读写权限
    ADMIN = "admin"         # 管理员权限
    OWNER = "owner"         # 所有者权限


class KnowledgePermissionService:
    """知识库权限控制服务"""
    
    def __init__(self):
        self.logger = logger
    
    async def check_knowledge_base_permission(
        self, 
        knowledge_base_id: int, 
        user_id: int, 
        required_permission: PermissionLevel = PermissionLevel.READ
    ) -> bool:
        """
        检查用户对知识库的权限
        
        Args:
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            required_permission: 需要的权限级别
            
        Returns:
            是否有权限
        """
        try:
            # 获取知识库信息
            kb = await KnowledgeBase.get_or_none(id=knowledge_base_id)
            if not kb:
                self.logger.warning(f"知识库不存在: {knowledge_base_id}")
                return False
            
            # 检查知识库是否已删除
            if kb.is_deleted:
                self.logger.warning(f"知识库已删除: {knowledge_base_id}")
                return False
            
            # 获取用户权限级别
            user_permission = await self.get_user_permission_level(kb, user_id)
            
            # 检查权限级别是否满足要求
            return self._is_permission_sufficient(user_permission, required_permission)
            
        except Exception as e:
            self.logger.error(f"检查知识库权限失败: {e}")
            return False
    
    async def check_file_permission(
        self, 
        file_id: int, 
        user_id: int, 
        required_permission: PermissionLevel = PermissionLevel.READ
    ) -> bool:
        """
        检查用户对文件的权限
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            required_permission: 需要的权限级别
            
        Returns:
            是否有权限
        """
        try:
            # 获取文件信息
            file_obj = await KnowledgeFile.get_or_none(id=file_id)
            if not file_obj:
                self.logger.warning(f"文件不存在: {file_id}")
                return False
            
            # 检查文件是否已删除
            if file_obj.is_deleted:
                self.logger.warning(f"文件已删除: {file_id}")
                return False
            
            # 检查对应知识库的权限
            return await self.check_knowledge_base_permission(
                file_obj.knowledge_base_id, 
                user_id, 
                required_permission
            )
            
        except Exception as e:
            self.logger.error(f"检查文件权限失败: {e}")
            return False
    
    async def get_user_permission_level(
        self, 
        knowledge_base: KnowledgeBase, 
        user_id: int
    ) -> PermissionLevel:
        """
        获取用户对知识库的权限级别
        
        Args:
            knowledge_base: 知识库对象
            user_id: 用户ID
            
        Returns:
            权限级别
        """
        try:
            # 检查是否为所有者
            if knowledge_base.owner_id == user_id:
                return PermissionLevel.OWNER
            
            # 检查是否为超级管理员
            user = await User.get_or_none(id=user_id)
            if user and user.is_superuser:
                return PermissionLevel.ADMIN
            
            # 检查是否为公开知识库
            if knowledge_base.is_public:
                return PermissionLevel.READ
            
            # 其他情况无权限
            return PermissionLevel.NONE
            
        except Exception as e:
            self.logger.error(f"获取用户权限级别失败: {e}")
            return PermissionLevel.NONE
    
    async def get_accessible_knowledge_bases(
        self, 
        user_id: int, 
        permission_level: PermissionLevel = PermissionLevel.READ
    ) -> List[KnowledgeBase]:
        """
        获取用户可访问的知识库列表
        
        Args:
            user_id: 用户ID
            permission_level: 最低权限级别
            
        Returns:
            知识库列表
        """
        try:
            accessible_kbs = []
            
            # 获取用户信息
            user = await User.get_or_none(id=user_id)
            if not user:
                return []
            
            # 获取所有未删除的知识库
            all_kbs = await KnowledgeBase.filter(is_deleted=False).all()
            
            for kb in all_kbs:
                user_permission = await self.get_user_permission_level(kb, user_id)
                if self._is_permission_sufficient(user_permission, permission_level):
                    accessible_kbs.append(kb)
            
            return accessible_kbs
            
        except Exception as e:
            self.logger.error(f"获取可访问知识库失败: {e}")
            return []
    
    async def get_user_owned_knowledge_bases(self, user_id: int) -> List[KnowledgeBase]:
        """
        获取用户拥有的知识库列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            知识库列表
        """
        try:
            return await KnowledgeBase.filter(
                owner_id=user_id,
                is_deleted=False
            ).all()
            
        except Exception as e:
            self.logger.error(f"获取用户拥有的知识库失败: {e}")
            return []
    
    async def get_public_knowledge_bases(self) -> List[KnowledgeBase]:
        """
        获取公开知识库列表
        
        Returns:
            公开知识库列表
        """
        try:
            return await KnowledgeBase.filter(
                is_public=True,
                is_deleted=False,
                status="active"
            ).all()
            
        except Exception as e:
            self.logger.error(f"获取公开知识库失败: {e}")
            return []
    
    async def can_create_knowledge_base(self, user_id: int) -> bool:
        """
        检查用户是否可以创建知识库
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否可以创建
        """
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                return False
            
            # 检查用户状态
            if not user.is_active:
                return False
            
            # 这里可以添加更多的限制逻辑，比如：
            # - 用户等级限制
            # - 知识库数量限制
            # - 存储空间限制等
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查创建权限失败: {e}")
            return False
    
    async def can_upload_file(
        self, 
        knowledge_base_id: int, 
        user_id: int, 
        file_size: int = 0
    ) -> tuple[bool, str]:
        """
        检查用户是否可以上传文件到知识库
        
        Args:
            knowledge_base_id: 知识库ID
            user_id: 用户ID
            file_size: 文件大小
            
        Returns:
            (是否可以上传, 错误信息)
        """
        try:
            # 检查知识库权限
            if not await self.check_knowledge_base_permission(
                knowledge_base_id, user_id, PermissionLevel.WRITE
            ):
                return False, "没有上传权限"
            
            # 获取知识库信息
            kb = await KnowledgeBase.get_or_none(id=knowledge_base_id)
            if not kb:
                return False, "知识库不存在"
            
            # 检查文件大小限制
            if file_size > kb.max_file_size:
                return False, f"文件大小超过限制({kb.max_file_size} 字节)"
            
            # 检查知识库状态
            if kb.status != "active":
                return False, "知识库状态异常"
            
            # 这里可以添加更多的限制逻辑，比如：
            # - 文件数量限制
            # - 存储空间限制
            # - 上传频率限制等
            
            return True, ""
            
        except Exception as e:
            self.logger.error(f"检查上传权限失败: {e}")
            return False, "权限检查失败"
    
    def _is_permission_sufficient(
        self, 
        user_permission: PermissionLevel, 
        required_permission: PermissionLevel
    ) -> bool:
        """
        检查用户权限是否满足要求
        
        Args:
            user_permission: 用户权限级别
            required_permission: 需要的权限级别
            
        Returns:
            是否满足要求
        """
        permission_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.ADMIN: 3,
            PermissionLevel.OWNER: 4
        }
        
        user_level = permission_hierarchy.get(user_permission, 0)
        required_level = permission_hierarchy.get(required_permission, 0)
        
        return user_level >= required_level
    
    async def get_permission_summary(
        self, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取用户权限摘要
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限摘要信息
        """
        try:
            # 获取用户信息
            user = await User.get_or_none(id=user_id)
            if not user:
                return {}
            
            # 获取各类知识库数量
            owned_kbs = await self.get_user_owned_knowledge_bases(user_id)
            accessible_kbs = await self.get_accessible_knowledge_bases(user_id)
            public_kbs = await self.get_public_knowledge_bases()
            
            # 计算统计信息
            owned_count = len(owned_kbs)
            accessible_count = len(accessible_kbs)
            public_count = len(public_kbs)
            
            # 计算文件统计
            total_files = 0
            total_size = 0
            for kb in owned_kbs:
                total_files += kb.file_count
                total_size += kb.total_size
            
            return {
                "user_id": user_id,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "owned_knowledge_bases": owned_count,
                "accessible_knowledge_bases": accessible_count,
                "public_knowledge_bases": public_count,
                "total_files": total_files,
                "total_size": total_size,
                "can_create_knowledge_base": await self.can_create_knowledge_base(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"获取权限摘要失败: {e}")
            return {}


# 全局权限服务实例
knowledge_permission_service = KnowledgePermissionService()


async def check_knowledge_base_access(
    knowledge_base_id: int, 
    user_id: int, 
    required_permission: str = "read"
) -> bool:
    """
    便捷函数：检查知识库访问权限
    
    Args:
        knowledge_base_id: 知识库ID
        user_id: 用户ID
        required_permission: 需要的权限级别字符串
        
    Returns:
        是否有权限
    """
    permission_map = {
        "read": PermissionLevel.READ,
        "write": PermissionLevel.WRITE,
        "admin": PermissionLevel.ADMIN,
        "owner": PermissionLevel.OWNER
    }
    
    permission_level = permission_map.get(required_permission, PermissionLevel.READ)
    
    return await knowledge_permission_service.check_knowledge_base_permission(
        knowledge_base_id, user_id, permission_level
    )


async def check_file_access(
    file_id: int, 
    user_id: int, 
    required_permission: str = "read"
) -> bool:
    """
    便捷函数：检查文件访问权限
    
    Args:
        file_id: 文件ID
        user_id: 用户ID
        required_permission: 需要的权限级别字符串
        
    Returns:
        是否有权限
    """
    permission_map = {
        "read": PermissionLevel.READ,
        "write": PermissionLevel.WRITE,
        "admin": PermissionLevel.ADMIN,
        "owner": PermissionLevel.OWNER
    }
    
    permission_level = permission_map.get(required_permission, PermissionLevel.READ)
    
    return await knowledge_permission_service.check_file_permission(
        file_id, user_id, permission_level
    )
