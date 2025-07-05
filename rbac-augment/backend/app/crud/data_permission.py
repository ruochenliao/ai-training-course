"""
数据权限CRUD操作
"""

from typing import List, Dict, Any, Optional, Tuple
from tortoise.transactions import in_transaction
from tortoise.expressions import Q

from ..models.data_permission import DataPermission, UserDataPermission, RoleDataPermission
from ..models.user import User
from ..models.role import Role
from ..schemas.data_permission import (
    DataPermissionCreate, DataPermissionUpdate, DataPermissionSearchParams,
    DataPermissionImportItem
)
from .base import CRUDBase


class CRUDDataPermission(CRUDBase[DataPermission, DataPermissionCreate, DataPermissionUpdate]):
    """数据权限CRUD操作类"""

    async def get_by_code(self, code: str) -> Optional[DataPermission]:
        """根据代码获取数据权限"""
        return await DataPermission.get_or_none(code=code)

    async def search(
        self,
        params: DataPermissionSearchParams,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[DataPermission], int]:
        """搜索数据权限"""
        query = DataPermission.all()

        # 关键词搜索
        if params.keyword:
            query = query.filter(
                Q(name__icontains=params.keyword) |
                Q(code__icontains=params.keyword) |
                Q(description__icontains=params.keyword)
            )

        # 权限类型筛选
        if params.permission_type:
            query = query.filter(permission_type=params.permission_type)

        # 权限范围筛选
        if params.scope:
            query = query.filter(scope=params.scope)

        # 资源类型筛选
        if params.resource_type:
            query = query.filter(resource_type__icontains=params.resource_type)

        # 状态筛选
        if params.is_active is not None:
            query = query.filter(is_active=params.is_active)

        # 排序
        query = query.order_by("sort_order", "created_at")

        # 分页
        total = await query.count()
        offset = (page - 1) * size
        items = await query.offset(offset).limit(size).all()

        return items, total

    async def create_with_validation(self, obj_in: DataPermissionCreate) -> DataPermission:
        """创建数据权限（带验证）"""
        # 检查代码是否已存在
        existing = await self.get_by_code(obj_in.code)
        if existing:
            raise ValueError(f"权限代码 {obj_in.code} 已存在")

        # 验证自定义条件格式
        if obj_in.custom_conditions:
            self._validate_custom_conditions(obj_in.custom_conditions)

        return await self.create(obj_in.model_dump())

    async def update_with_validation(
        self,
        db_obj: DataPermission,
        obj_in: DataPermissionUpdate
    ) -> DataPermission:
        """更新数据权限（带验证）"""
        update_data = obj_in.model_dump(exclude_unset=True)

        # 检查代码是否已存在（排除自己）
        if "code" in update_data:
            existing = await self.get_by_code(update_data["code"])
            if existing and existing.id != db_obj.id:
                raise ValueError(f"权限代码 {update_data['code']} 已存在")

        # 验证自定义条件格式
        if "custom_conditions" in update_data and update_data["custom_conditions"]:
            self._validate_custom_conditions(update_data["custom_conditions"])

        return await self.update(db_obj, update_data)

    def _validate_custom_conditions(self, conditions: Dict[str, Any]) -> None:
        """验证自定义条件格式"""
        if not isinstance(conditions, dict):
            raise ValueError("自定义条件必须是字典格式")

        # 验证支持的条件类型
        supported_conditions = {
            "user_level", "time_range", "ip_range", "location",
            "user_attributes", "resource_attributes"
        }

        for key in conditions.keys():
            if key not in supported_conditions:
                raise ValueError(f"不支持的条件类型: {key}")

        # 验证时间范围格式
        if "time_range" in conditions:
            time_range = conditions["time_range"]
            if not isinstance(time_range, dict) or "start" not in time_range or "end" not in time_range:
                raise ValueError("时间范围格式错误，需要包含start和end字段")

    async def assign_to_users(
        self,
        permission_id: int,
        user_ids: List[int],
        granted_by_id: int
    ) -> Dict[str, Any]:
        """将数据权限分配给用户"""
        permission = await self.get(permission_id)
        if not permission:
            raise ValueError("数据权限不存在")

        success_count = 0
        failed_users = []

        async with in_transaction():
            for user_id in user_ids:
                try:
                    user = await User.get_or_none(id=user_id)
                    if not user:
                        failed_users.append({
                            "id": user_id,
                            "error": "用户不存在"
                        })
                        continue

                    # 检查是否已经分配
                    existing = await UserDataPermission.get_or_none(
                        user_id=user_id,
                        data_permission_id=permission_id
                    )
                    if existing:
                        failed_users.append({
                            "id": user_id,
                            "error": "权限已分配"
                        })
                        continue

                    # 创建分配记录
                    await UserDataPermission.create(
                        user_id=user_id,
                        data_permission_id=permission_id,
                        granted_by_id=granted_by_id
                    )
                    success_count += 1

                except Exception as e:
                    failed_users.append({
                        "id": user_id,
                        "error": str(e)
                    })

        return {
            "success_count": success_count,
            "failed_count": len(failed_users),
            "failed_users": failed_users
        }

    async def assign_to_roles(
        self,
        permission_id: int,
        role_ids: List[int],
        granted_by_id: int
    ) -> Dict[str, Any]:
        """将数据权限分配给角色"""
        permission = await self.get(permission_id)
        if not permission:
            raise ValueError("数据权限不存在")

        success_count = 0
        failed_roles = []

        async with in_transaction():
            for role_id in role_ids:
                try:
                    role = await Role.get_or_none(id=role_id)
                    if not role:
                        failed_roles.append({
                            "id": role_id,
                            "error": "角色不存在"
                        })
                        continue

                    # 检查是否已经分配
                    existing = await RoleDataPermission.get_or_none(
                        role_id=role_id,
                        data_permission_id=permission_id
                    )
                    if existing:
                        failed_roles.append({
                            "id": role_id,
                            "error": "权限已分配"
                        })
                        continue

                    # 创建分配记录
                    await RoleDataPermission.create(
                        role_id=role_id,
                        data_permission_id=permission_id,
                        granted_by_id=granted_by_id
                    )
                    success_count += 1

                except Exception as e:
                    failed_roles.append({
                        "id": role_id,
                        "error": str(e)
                    })

        return {
            "success_count": success_count,
            "failed_count": len(failed_roles),
            "failed_roles": failed_roles
        }

    async def remove_from_users(self, permission_id: int, user_ids: List[int]) -> Dict[str, Any]:
        """从用户移除数据权限"""
        success_count = 0
        failed_users = []

        async with in_transaction():
            for user_id in user_ids:
                try:
                    deleted_count = await UserDataPermission.filter(
                        user_id=user_id,
                        data_permission_id=permission_id
                    ).delete()

                    if deleted_count > 0:
                        success_count += 1
                    else:
                        failed_users.append({
                            "id": user_id,
                            "error": "权限未分配"
                        })

                except Exception as e:
                    failed_users.append({
                        "id": user_id,
                        "error": str(e)
                    })

        return {
            "success_count": success_count,
            "failed_count": len(failed_users),
            "failed_users": failed_users
        }

    async def remove_from_roles(self, permission_id: int, role_ids: List[int]) -> Dict[str, Any]:
        """从角色移除数据权限"""
        success_count = 0
        failed_roles = []

        async with in_transaction():
            for role_id in role_ids:
                try:
                    deleted_count = await RoleDataPermission.filter(
                        role_id=role_id,
                        data_permission_id=permission_id
                    ).delete()

                    if deleted_count > 0:
                        success_count += 1
                    else:
                        failed_roles.append({
                            "id": role_id,
                            "error": "权限未分配"
                        })

                except Exception as e:
                    failed_roles.append({
                        "id": role_id,
                        "error": str(e)
                    })

        return {
            "success_count": success_count,
            "failed_count": len(failed_roles),
            "failed_roles": failed_roles
        }

    async def get_user_permissions(self, user_id: int) -> List[DataPermission]:
        """获取用户的数据权限"""
        # 直接分配的权限
        direct_permissions = await DataPermission.filter(
            users__id=user_id,
            is_active=True
        ).all()

        # 通过角色获得的权限
        role_permissions = await DataPermission.filter(
            roles__users__id=user_id,
            is_active=True
        ).all()

        # 去重
        all_permissions = list({p.id: p for p in direct_permissions + role_permissions}.values())
        return all_permissions

    async def check_user_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int = None,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """检查用户数据权限"""
        user = await User.get_or_none(id=user_id)
        if not user:
            return False, "用户不存在"

        # 获取用户的数据权限
        permissions = await self.get_user_permissions(user_id)

        # 筛选相关的权限
        relevant_permissions = [
            p for p in permissions
            if p.resource_type == resource_type or p.resource_type == "all"
        ]

        if not relevant_permissions:
            return False, "无相关数据权限"

        # 检查权限
        for permission in relevant_permissions:
            has_access = await permission.check_data_access(user, resource_id, **kwargs)
            if has_access:
                return True, f"通过权限: {permission.name}"

        return False, "数据权限检查失败"

    async def get_select_options(self) -> List[Dict[str, Any]]:
        """获取数据权限选择选项"""
        permissions = await DataPermission.filter(is_active=True).order_by("sort_order").all()
        return [
            {
                "id": permission.id,
                "name": permission.name,
                "code": permission.code,
                "permission_type": permission.permission_type,
                "scope": permission.scope
            }
            for permission in permissions
        ]


# 创建CRUD实例
crud_data_permission = CRUDDataPermission(DataPermission)
