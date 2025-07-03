"""
部门CRUD操作
处理部门的数据库操作
"""

from typing import List, Optional, Dict, Any, Tuple
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction

from .base import CRUDBase
from ..models.department import Department
from ..models.user import User
from ..schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentSearchParams,
    DepartmentBatchOperation, DepartmentImportData
)


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    """部门CRUD操作类"""
    
    async def get_by_code(self, code: str) -> Optional[Department]:
        """通过编码获取部门"""
        return await Department.get_by_code(code)
    
    async def get_tree(self, parent_id: Optional[int] = None, include_inactive: bool = False) -> List[Department]:
        """获取部门树"""
        return await Department.get_tree(parent_id, include_inactive)
    
    async def get_root_departments(self, include_inactive: bool = False) -> List[Department]:
        """获取根部门列表"""
        return await Department.get_root_departments(include_inactive)
    
    async def search(
        self, 
        params: DepartmentSearchParams,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Department], int]:
        """搜索部门"""
        query = Department.filter(is_deleted=False)
        
        # 关键词搜索
        if params.keyword:
            query = query.filter(
                Department.Q(name__icontains=params.keyword) |
                Department.Q(code__icontains=params.keyword) |
                Department.Q(description__icontains=params.keyword)
            )
        
        # 父部门过滤
        if params.parent_id is not None:
            query = query.filter(parent_id=params.parent_id)
        
        # 层级过滤
        if params.level is not None:
            query = query.filter(level=params.level)
        
        # 状态过滤
        if params.is_active is not None:
            query = query.filter(is_active=params.is_active)
        
        # 负责人过滤
        if params.manager_id is not None:
            query = query.filter(manager_id=params.manager_id)
        
        # 获取总数
        total = await query.count()
        
        # 分页查询
        departments = await query.order_by("sort_order", "id").offset(skip).limit(limit)
        
        return departments, total
    
    async def create_with_validation(self, obj_in: DepartmentCreate) -> Department:
        """创建部门（带验证）"""
        # 检查编码是否已存在
        existing = await self.get_by_code(obj_in.code)
        if existing:
            raise ValueError(f"部门编码 {obj_in.code} 已存在")
        
        # 检查父部门是否存在
        if obj_in.parent_id:
            parent = await self.get(obj_in.parent_id)
            if not parent:
                raise ValueError(f"父部门 {obj_in.parent_id} 不存在")
            
            # 设置层级
            level = parent.level + 1
        else:
            level = 0
        
        # 检查负责人是否存在
        if obj_in.manager_id:
            manager = await User.filter(id=obj_in.manager_id, is_deleted=False).first()
            if not manager:
                raise ValueError(f"负责人 {obj_in.manager_id} 不存在")
        
        # 创建部门
        department_data = obj_in.dict()
        department_data["level"] = level
        
        return await self.create(department_data)
    
    async def update_with_validation(self, db_obj: Department, obj_in: DepartmentUpdate) -> Department:
        """更新部门（带验证）"""
        update_data = obj_in.dict(exclude_unset=True)
        
        # 检查负责人是否存在
        if "manager_id" in update_data and update_data["manager_id"]:
            manager = await User.filter(id=update_data["manager_id"], is_deleted=False).first()
            if not manager:
                raise ValueError(f"负责人 {update_data['manager_id']} 不存在")
        
        return await self.update(db_obj, update_data)
    
    async def move_department(self, department_id: int, new_parent_id: Optional[int]) -> bool:
        """移动部门"""
        department = await self.get(department_id)
        if not department:
            raise ValueError(f"部门 {department_id} 不存在")
        
        return await department.move_to(new_parent_id)
    
    async def get_department_users(self, department_id: int, include_descendants: bool = False) -> List[User]:
        """获取部门用户"""
        department = await self.get(department_id)
        if not department:
            raise ValueError(f"部门 {department_id} 不存在")
        
        if include_descendants:
            # 获取部门及其所有子部门的用户
            descendants = await department.get_descendants()
            department_ids = [department.id] + [d.id for d in descendants]
            return await User.filter(department_id__in=department_ids, is_deleted=False)
        else:
            return await department.get_users()
    
    async def assign_users_to_department(self, department_id: int, user_ids: List[int]) -> Dict[str, Any]:
        """将用户分配到部门"""
        department = await self.get(department_id)
        if not department:
            raise ValueError(f"部门 {department_id} 不存在")
        
        success_count = 0
        failed_users = []
        
        async with in_transaction():
            for user_id in user_ids:
                try:
                    user = await User.filter(id=user_id, is_deleted=False).first()
                    if user:
                        user.department_id = department_id
                        await user.save()
                        success_count += 1
                    else:
                        failed_users.append({"id": user_id, "error": "用户不存在"})
                except Exception as e:
                    failed_users.append({"id": user_id, "error": str(e)})
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_users),
            "failed_users": failed_users
        }
    
    async def batch_operation(self, operation: DepartmentBatchOperation) -> Dict[str, Any]:
        """批量操作部门"""
        success_count = 0
        failed_departments = []
        
        async with in_transaction():
            for dept_id in operation.department_ids:
                try:
                    department = await self.get(dept_id)
                    if not department:
                        failed_departments.append({
                            "id": dept_id,
                            "name": "未知",
                            "error": "部门不存在"
                        })
                        continue
                    
                    if operation.operation == "activate":
                        await department.activate()
                    elif operation.operation == "deactivate":
                        await department.deactivate()
                    elif operation.operation == "delete":
                        can_delete, reason = await department.can_delete()
                        if can_delete:
                            await self.remove(dept_id)
                        else:
                            failed_departments.append({
                                "id": dept_id,
                                "name": department.name,
                                "error": reason
                            })
                            continue
                    
                    success_count += 1
                    
                except Exception as e:
                    failed_departments.append({
                        "id": dept_id,
                        "name": getattr(department, 'name', '未知') if 'department' in locals() else "未知",
                        "error": str(e)
                    })
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_departments),
            "failed_departments": failed_departments,
            "errors": [item["error"] for item in failed_departments]
        }
    
    async def import_departments(self, import_data: List[DepartmentImportData]) -> Dict[str, Any]:
        """批量导入部门"""
        success_count = 0
        failed_items = []
        created_departments = []
        
        # 按层级排序，确保父部门先创建
        sorted_data = sorted(import_data, key=lambda x: 0 if not x.parent_code else 1)
        
        async with in_transaction():
            for item in sorted_data:
                try:
                    # 检查编码是否已存在
                    existing = await self.get_by_code(item.code)
                    if existing:
                        failed_items.append({
                            "data": item.dict(),
                            "error": f"部门编码 {item.code} 已存在"
                        })
                        continue
                    
                    # 查找父部门
                    parent_id = None
                    if item.parent_code:
                        parent = await self.get_by_code(item.parent_code)
                        if not parent:
                            failed_items.append({
                                "data": item.dict(),
                                "error": f"父部门编码 {item.parent_code} 不存在"
                            })
                            continue
                        parent_id = parent.id
                    
                    # 查找负责人
                    manager_id = None
                    if item.manager_username:
                        manager = await User.filter(username=item.manager_username, is_deleted=False).first()
                        if not manager:
                            failed_items.append({
                                "data": item.dict(),
                                "error": f"负责人用户名 {item.manager_username} 不存在"
                            })
                            continue
                        manager_id = manager.id
                    
                    # 创建部门
                    create_data = DepartmentCreate(
                        name=item.name,
                        code=item.code,
                        description=item.description,
                        parent_id=parent_id,
                        manager_id=manager_id,
                        phone=item.phone,
                        email=item.email,
                        address=item.address,
                        sort_order=item.sort_order
                    )
                    
                    department = await self.create_with_validation(create_data)
                    created_departments.append(department)
                    success_count += 1
                    
                except Exception as e:
                    failed_items.append({
                        "data": item.dict(),
                        "error": str(e)
                    })
        
        return {
            "total_count": len(import_data),
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
            "created_departments": created_departments
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取部门统计信息"""
        total_departments = await Department.filter(is_deleted=False).count()
        active_departments = await Department.filter(is_deleted=False, is_active=True).count()
        inactive_departments = total_departments - active_departments
        
        # 统计各层级部门数量
        departments_by_level = {}
        for level in range(6):  # 假设最多6级
            count = await Department.filter(is_deleted=False, level=level).count()
            if count > 0:
                departments_by_level[level] = count
        
        # 统计用户数最多的部门（前10个）
        departments = await Department.filter(is_deleted=False)
        dept_user_counts = []
        
        for dept in departments:
            user_count = await dept.get_user_count()
            if user_count > 0:
                dept_user_counts.append({
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "user_count": user_count
                })
        
        # 按用户数排序，取前10
        top_departments_by_users = sorted(
            dept_user_counts, 
            key=lambda x: x["user_count"], 
            reverse=True
        )[:10]
        
        # 统计总用户数
        total_users = await User.filter(is_deleted=False, department_id__isnull=False).count()
        
        return {
            "total_departments": total_departments,
            "active_departments": active_departments,
            "inactive_departments": inactive_departments,
            "total_users": total_users,
            "departments_by_level": departments_by_level,
            "top_departments_by_users": top_departments_by_users
        }


# 创建CRUD实例
crud_department = CRUDDepartment(Department)
