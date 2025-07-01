"""
用户角色业务逻辑服务
"""

from typing import List, Dict, Any

from loguru import logger

from app.models.rbac import UserRole, UserPermission, Role, Permission
from app.models import User
from app.schemas.rbac import UserRoleAssign, UserPermissionAssign


class UserRoleService:
    """用户角色服务类"""
    
    @staticmethod
    async def assign_user_roles(assign_data: UserRoleAssign, current_user: User) -> List[Dict[str, Any]]:
        """分配用户角色"""
        try:
            user = await User.get_or_none(id=assign_data.user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 删除现有角色
            await UserRole.filter(user_id=assign_data.user_id).delete()
            
            # 分配新角色
            user_roles = []
            for role_id in assign_data.role_ids:
                role = await Role.get_or_none(id=role_id)
                if not role:
                    raise ValueError(f"角色ID {role_id} 不存在")
                
                user_role = await UserRole.create(
                    user_id=assign_data.user_id,
                    role_id=role_id,
                    granted_by=current_user.id,
                    expires_at=assign_data.expires_at,
                    dept_ids=assign_data.dept_ids or []
                )
                
                # 获取完整信息
                user_role_dict = await user_role.to_dict()
                user_role_dict["user_name"] = user.username
                user_role_dict["role_name"] = role.name
                user_role_dict["role_code"] = role.code
                user_role_dict["granted_by_name"] = current_user.username
                user_roles.append(user_role_dict)
            
            return user_roles
        except Exception as e:
            logger.error(f"分配用户角色失败: {e}")
            raise
    
    @staticmethod
    async def get_user_roles(user_id: int) -> List[Dict[str, Any]]:
        """获取用户角色"""
        try:
            user_roles = await UserRole.filter(user_id=user_id).prefetch_related("role", "user")
            
            user_role_responses = []
            for user_role in user_roles:
                if user_role.is_expired():
                    continue
                
                user_role_dict = await user_role.to_dict()
                user_role_dict["user_name"] = user_role.user.username
                user_role_dict["role_name"] = user_role.role.name
                user_role_dict["role_code"] = user_role.role.code
                
                # 获取授权人信息
                granted_by_user = await User.get_or_none(id=user_role.granted_by)
                if granted_by_user:
                    user_role_dict["granted_by_name"] = granted_by_user.username
                
                user_role_responses.append(user_role_dict)
            
            return user_role_responses
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            raise
    
    @staticmethod
    async def assign_user_permissions(assign_data: UserPermissionAssign, current_user: User) -> List[Dict[str, Any]]:
        """分配用户权限"""
        try:
            user = await User.get_or_none(id=assign_data.user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 删除现有权限（相同类型）
            await UserPermission.filter(
                user_id=assign_data.user_id,
                permission_type=assign_data.permission_type
            ).delete()
            
            # 分配新权限
            user_permissions = []
            for perm_id in assign_data.permission_ids:
                permission = await Permission.get_or_none(id=perm_id)
                if not permission:
                    raise ValueError(f"权限ID {perm_id} 不存在")
                
                user_permission = await UserPermission.create(
                    user_id=assign_data.user_id,
                    permission_id=perm_id,
                    granted_by=current_user.id,
                    expires_at=assign_data.expires_at,
                    permission_type=assign_data.permission_type
                )
                
                # 获取完整信息
                user_perm_dict = await user_permission.to_dict()
                user_perm_dict["user_name"] = user.username
                user_perm_dict["permission_name"] = permission.name
                user_perm_dict["permission_code"] = permission.code
                user_perm_dict["granted_by_name"] = current_user.username
                user_permissions.append(user_perm_dict)
            
            return user_permissions
        except Exception as e:
            logger.error(f"分配用户权限失败: {e}")
            raise
    
    @staticmethod
    async def get_user_permissions(user_id: int) -> List[Dict[str, Any]]:
        """获取用户权限"""
        try:
            user_permissions = await UserPermission.filter(user_id=user_id).prefetch_related("permission", "user")
            
            user_perm_responses = []
            for user_perm in user_permissions:
                if user_perm.is_expired():
                    continue
                
                user_perm_dict = await user_perm.to_dict()
                user_perm_dict["user_name"] = user_perm.user.username
                user_perm_dict["permission_name"] = user_perm.permission.name
                user_perm_dict["permission_code"] = user_perm.permission.code
                
                # 获取授权人信息
                granted_by_user = await User.get_or_none(id=user_perm.granted_by)
                if granted_by_user:
                    user_perm_dict["granted_by_name"] = granted_by_user.username
                
                user_perm_responses.append(user_perm_dict)
            
            return user_perm_responses
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            raise
