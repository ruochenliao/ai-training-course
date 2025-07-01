"""
角色业务逻辑服务
"""

from typing import List, Dict, Any, Tuple

from loguru import logger

from app.models.rbac import Role, RolePermission, UserRole
from app.models import User
from app.schemas.rbac import RoleCreate, RoleUpdate


class RoleService:
    """角色服务类"""
    
    @staticmethod
    async def get_roles_with_pagination(
        page: int = 1, 
        size: int = 20, 
        search: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取角色列表（分页）"""
        try:
            query = Role.filter(status="active")
            
            if search:
                query = query.filter(name__icontains=search)
            
            total = await query.count()
            roles = await query.offset((page - 1) * size).limit(size).all()
            
            # 获取角色权限信息
            role_responses = []
            for role in roles:
                # 转换为字典格式
                role_dict = await role.to_dict()
                role_dict["permissions"] = await role.get_permissions()
                role_dict["user_count"] = await UserRole.filter(role_id=role.id).count()
                role_responses.append(role_dict)
            
            return role_responses, total
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}")
            raise
    
    @staticmethod
    async def create_role(role_data: RoleCreate, current_user: User) -> Dict[str, Any]:
        """创建角色"""
        try:
            # 检查角色代码是否已存在
            existing_role = await Role.get_or_none(code=role_data.code)
            if existing_role:
                raise ValueError("角色代码已存在")
            
            # 创建角色
            permission_ids = role_data.permission_ids
            role_dict = role_data.dict(exclude={"permission_ids"})
            role = await Role.create(
                **role_dict,
                created_by=current_user.id
            )
            
            # 分配权限
            if permission_ids:
                for perm_id in permission_ids:
                    await RolePermission.create(role_id=role.id, permission_id=perm_id)
            
            # 获取完整信息
            role_dict = await role.to_dict()
            role_dict["permissions"] = await role.get_permissions()
            
            return role_dict
        except Exception as e:
            logger.error(f"创建角色失败: {e}")
            raise
    
    @staticmethod
    async def update_role(role_id: int, role_data: RoleUpdate, current_user: User) -> Dict[str, Any]:
        """更新角色"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                raise ValueError("角色不存在")
            
            # 更新角色信息
            permission_ids = role_data.permission_ids
            update_data = role_data.dict(exclude_unset=True, exclude={"permission_ids"})
            if update_data:
                update_data["updated_by"] = current_user.id
                await role.update_from_dict(update_data)
                await role.save()
            
            # 更新权限
            if permission_ids is not None:
                # 删除现有权限
                await RolePermission.filter(role_id=role.id).delete()
                # 添加新权限
                for perm_id in permission_ids:
                    await RolePermission.create(role_id=role.id, permission_id=perm_id)
            
            # 获取完整信息
            role_dict = await role.to_dict()
            role_dict["permissions"] = await role.get_permissions()
            
            return role_dict
        except Exception as e:
            logger.error(f"更新角色失败: {e}")
            raise
    
    @staticmethod
    async def delete_role(role_id: int) -> bool:
        """删除角色"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                raise ValueError("角色不存在")
            
            # 检查是否有用户使用该角色
            user_roles = await UserRole.filter(role_id=role_id)
            if user_roles:
                raise ValueError("角色正在使用中，无法删除")
            
            # 删除角色权限关联
            await RolePermission.filter(role_id=role_id).delete()
            
            # 删除角色
            await role.delete()
            return True
        except Exception as e:
            logger.error(f"删除角色失败: {e}")
            raise
