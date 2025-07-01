"""
部门业务逻辑服务
"""

from typing import List, Optional, Dict, Any

from loguru import logger

from app.models.rbac import Department
from app.models import User
from app.schemas.rbac import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    """部门服务类"""
    
    @staticmethod
    async def get_departments_tree(user: User) -> List[Dict[str, Any]]:
        """获取部门树形结构"""
        try:
            # 获取用户有权限访问的部门
            accessible_depts = await user.get_data_scope_departments()
            
            # 构建树形结构
            dept_dict = {dept.id: dept for dept in accessible_depts}
            tree_depts = []
            
            for dept in accessible_depts:
                if dept.parent_id is None or dept.parent_id not in dept_dict:
                    # 根部门
                    dept_dict_data = await dept.to_dict()
                    dept_dict_data["children"] = await DepartmentService._build_dept_tree(dept, dept_dict)
                    tree_depts.append(dept_dict_data)
            
            return tree_depts
        except Exception as e:
            logger.error(f"获取部门树形结构失败: {e}")
            raise
    
    @staticmethod
    async def _build_dept_tree(parent_dept: Department, dept_dict: Dict[int, Department]) -> List[Dict[str, Any]]:
        """构建部门树"""
        children = []
        for dept in dept_dict.values():
            if dept.parent_id == parent_dept.id:
                dept_data = await dept.to_dict()
                dept_data["children"] = await DepartmentService._build_dept_tree(dept, dept_dict)
                children.append(dept_data)
        return children
    
    @staticmethod
    async def create_department(dept_data: DepartmentCreate, current_user: User) -> Department:
        """创建部门"""
        try:
            # 检查部门代码是否已存在
            existing_dept = await Department.get_or_none(code=dept_data.code)
            if existing_dept:
                raise ValueError("部门代码已存在")
            
            # 创建部门
            dept = await Department.create(
                **dept_data.dict(),
                created_by=current_user.id
            )
            
            return dept
        except Exception as e:
            logger.error(f"创建部门失败: {e}")
            raise
    
    @staticmethod
    async def update_department(dept_id: int, dept_data: DepartmentUpdate, current_user: User) -> Department:
        """更新部门"""
        try:
            dept = await Department.get_or_none(id=dept_id)
            if not dept:
                raise ValueError("部门不存在")
            
            # 更新部门信息
            update_data = dept_data.dict(exclude_unset=True)
            if update_data:
                update_data["updated_by"] = current_user.id
                await dept.update_from_dict(update_data)
                await dept.save()
            
            return dept
        except Exception as e:
            logger.error(f"更新部门失败: {e}")
            raise
    
    @staticmethod
    async def delete_department(dept_id: int) -> bool:
        """删除部门"""
        try:
            dept = await Department.get_or_none(id=dept_id)
            if not dept:
                raise ValueError("部门不存在")
            
            # 检查是否有子部门
            children = await dept.get_children()
            if children:
                raise ValueError("请先删除子部门")
            
            # 检查是否有用户
            users = await User.filter(department_id=dept_id)
            if users:
                raise ValueError("部门下还有用户，无法删除")
            
            await dept.delete()
            return True
        except Exception as e:
            logger.error(f"删除部门失败: {e}")
            raise
