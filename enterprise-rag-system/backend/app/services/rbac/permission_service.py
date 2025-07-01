"""
权限业务逻辑服务
"""

from typing import List, Dict, Any, Tuple

from loguru import logger

from app.models.rbac import Permission, RolePermission, UserPermission
from app.models import User
from app.schemas.rbac import PermissionCreate, PermissionUpdate, PermissionCheck, MenuTree


class PermissionService:
    """权限服务类"""
    
    @staticmethod
    async def get_permissions_with_pagination(
        page: int = 1,
        size: int = 20,
        search: str = None,
        group: str = None,
        permission_type: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取权限列表（分页）"""
        try:
            query = Permission.filter(status="active")
            
            if search:
                query = query.filter(name__icontains=search)
            
            if group:
                query = query.filter(group=group)
            
            if permission_type:
                query = query.filter(permission_type=permission_type)
            
            total = await query.count()
            permissions = await query.offset((page - 1) * size).limit(size).all()
            
            # 转换为字典格式
            permission_responses = []
            for perm in permissions:
                perm_dict = await perm.to_dict()
                permission_responses.append(perm_dict)
            
            return permission_responses, total
        except Exception as e:
            logger.error(f"获取权限列表失败: {e}")
            raise
    
    @staticmethod
    async def create_permission(perm_data: PermissionCreate, current_user: User) -> Dict[str, Any]:
        """创建权限"""
        try:
            # 检查权限代码是否已存在
            existing_perm = await Permission.get_or_none(code=perm_data.code)
            if existing_perm:
                raise ValueError("权限代码已存在")
            
            # 创建权限
            perm = await Permission.create(
                **perm_data.model_dump(),
                created_by=current_user.id
            )
            
            return await perm.to_dict()
        except Exception as e:
            logger.error(f"创建权限失败: {e}")
            raise
    
    @staticmethod
    async def update_permission(perm_id: int, perm_data: PermissionUpdate, current_user: User) -> Dict[str, Any]:
        """更新权限"""
        try:
            perm = await Permission.get_or_none(id=perm_id)
            if not perm:
                raise ValueError("权限不存在")
            
            # 更新权限信息
            update_data = perm_data.model_dump(exclude_unset=True)
            if update_data:
                update_data["updated_by"] = current_user.id
                await perm.update_from_dict(update_data)
                await perm.save()
            
            return await perm.to_dict()
        except Exception as e:
            logger.error(f"更新权限失败: {e}")
            raise
    
    @staticmethod
    async def delete_permission(perm_id: int) -> bool:
        """删除权限"""
        try:
            perm = await Permission.get_or_none(id=perm_id)
            if not perm:
                raise ValueError("权限不存在")
            
            # 检查是否有角色使用该权限
            role_permissions = await RolePermission.filter(permission_id=perm_id)
            if role_permissions:
                raise ValueError("权限正在使用中，无法删除")
            
            # 检查是否有用户直接分配该权限
            user_permissions = await UserPermission.filter(permission_id=perm_id)
            if user_permissions:
                raise ValueError("权限正在使用中，无法删除")
            
            await perm.delete()
            return True
        except Exception as e:
            logger.error(f"删除权限失败: {e}")
            raise
    
    @staticmethod
    async def check_user_permissions(check_data: PermissionCheck) -> Dict[str, bool]:
        """检查用户权限"""
        try:
            user = await User.get_or_none(id=check_data.user_id)
            if not user:
                raise ValueError("用户不存在")
            
            permissions = {}
            for perm_code in check_data.permission_codes:
                permissions[perm_code] = await user.has_permission(perm_code)
            
            return permissions
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            raise
    
    @staticmethod
    async def get_user_menu_tree(user: User) -> List[MenuTree]:
        """获取用户菜单树"""
        try:
            # 获取用户权限
            user_permissions = await user.get_permissions()
            menu_permissions = [p for p in user_permissions if p.permission_type == "menu"]
            
            # 构建菜单树
            menu_dict = {}
            for perm in menu_permissions:
                menu_dict[perm.id] = MenuTree(
                    id=perm.id,
                    name=perm.name,
                    code=perm.code,
                    path=perm.menu_path,
                    component=perm.menu_component,
                    icon=perm.menu_icon,
                    sort_order=perm.sort_order,
                    children=[]
                )
            
            # 构建树形结构
            root_menus = []
            for perm in menu_permissions:
                menu = menu_dict[perm.id]
                if not perm.parent_id or perm.parent_id not in menu_dict:
                    root_menus.append(menu)
                else:
                    parent_menu = menu_dict[menu.parent_id]
                    parent_menu.children.append(menu)
            
            # 排序
            def sort_menus(menus):
                menus.sort(key=lambda x: x.sort_order)
                for menu in menus:
                    sort_menus(menu.children)
            
            sort_menus(root_menus)
            return root_menus
        except Exception as e:
            logger.error(f"获取用户菜单树失败: {e}")
            raise
