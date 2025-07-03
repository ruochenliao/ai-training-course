"""
部门模型
定义部门表结构和相关方法
"""

from typing import List, Optional, Dict, Any
from tortoise import fields
from tortoise.queryset import QuerySet

from .base import BaseModel


class Department(BaseModel):
    """部门模型"""
    
    name = fields.CharField(max_length=100, description="部门名称")
    code = fields.CharField(max_length=50, unique=True, description="部门编码")
    description = fields.TextField(null=True, description="部门描述")
    
    # 树形结构
    parent_id = fields.IntField(null=True, description="父部门ID")
    level = fields.IntField(default=0, description="部门层级")
    sort_order = fields.IntField(default=0, description="排序")
    
    # 部门负责人
    manager_id = fields.IntField(null=True, description="部门负责人ID")
    
    # 联系信息
    phone = fields.CharField(max_length=20, null=True, description="联系电话")
    email = fields.CharField(max_length=100, null=True, description="联系邮箱")
    address = fields.CharField(max_length=255, null=True, description="办公地址")
    
    # 状态信息
    is_active = fields.BooleanField(default=True, description="是否启用")
    
    class Meta:
        table = "departments"
        table_description = "部门表"
        ordering = ["sort_order", "id"]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    async def to_dict(self, include_children: bool = False, include_users: bool = False) -> Dict[str, Any]:
        """将部门转换为字典"""
        base_dict = super().to_dict()
        
        result = {
            **base_dict,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "parent_id": self.parent_id,
            "level": self.level,
            "sort_order": self.sort_order,
            "manager_id": self.manager_id,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "is_active": self.is_active
        }
        
        # 包含子部门
        if include_children:
            children = await self.get_children()
            result["children"] = [await child.to_dict(include_children=True) for child in children]
        
        # 包含用户信息
        if include_users:
            users = await self.get_users()
            result["users"] = [await user.to_dict() for user in users]
            result["user_count"] = len(users)
        
        return result
    
    async def get_parent(self) -> Optional["Department"]:
        """获取父部门"""
        if not self.parent_id:
            return None
        return await Department.filter(id=self.parent_id).first()
    
    async def get_children(self, recursive: bool = False) -> List["Department"]:
        """获取子部门"""
        children = await Department.filter(parent_id=self.id, is_deleted=False).order_by("sort_order")
        
        if recursive:
            all_children = list(children)
            for child in children:
                sub_children = await child.get_children(recursive=True)
                all_children.extend(sub_children)
            return all_children
        
        return children
    
    async def get_ancestors(self) -> List["Department"]:
        """获取所有祖先部门"""
        ancestors = []
        current = self
        
        while current.parent_id:
            parent = await current.get_parent()
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    async def get_descendants(self) -> List["Department"]:
        """获取所有后代部门"""
        return await self.get_children(recursive=True)
    
    async def get_users(self) -> List:
        """获取部门用户"""
        from app.models.user import User
        return await User.filter(department_id=self.id, is_deleted=False, is_active=True)
    
    async def get_user_count(self) -> int:
        """获取部门用户数量"""
        from app.models.user import User
        return await User.filter(department_id=self.id, is_deleted=False, is_active=True).count()
    
    async def get_manager(self):
        """获取部门负责人"""
        if not self.manager_id:
            return None
        
        from app.models.user import User
        return await User.filter(id=self.manager_id).first()
    
    async def is_ancestor_of(self, department: "Department") -> bool:
        """检查是否为指定部门的祖先"""
        descendants = await self.get_descendants()
        return department in descendants
    
    async def is_descendant_of(self, department: "Department") -> bool:
        """检查是否为指定部门的后代"""
        ancestors = await self.get_ancestors()
        return department in ancestors
    
    async def get_path(self) -> str:
        """获取部门路径"""
        ancestors = await self.get_ancestors()
        ancestors.reverse()  # 从根部门开始
        ancestors.append(self)
        return " > ".join([dept.name for dept in ancestors])
    
    async def get_full_code(self) -> str:
        """获取完整部门编码"""
        ancestors = await self.get_ancestors()
        ancestors.reverse()  # 从根部门开始
        ancestors.append(self)
        return ".".join([dept.code for dept in ancestors])
    
    @classmethod
    async def get_tree(cls, parent_id: Optional[int] = None, include_inactive: bool = False) -> List["Department"]:
        """获取部门树"""
        query = cls.filter(parent_id=parent_id, is_deleted=False)
        
        if not include_inactive:
            query = query.filter(is_active=True)
        
        departments = await query.order_by("sort_order")
        
        # 递归获取子部门
        for dept in departments:
            dept.children = await cls.get_tree(dept.id, include_inactive)
        
        return departments
    
    @classmethod
    async def get_root_departments(cls, include_inactive: bool = False) -> List["Department"]:
        """获取根部门列表"""
        return await cls.get_tree(parent_id=None, include_inactive=include_inactive)
    
    @classmethod
    async def get_by_code(cls, code: str) -> Optional["Department"]:
        """通过编码获取部门"""
        return await cls.filter(code=code, is_deleted=False).first()
    
    @classmethod
    async def get_by_manager(cls, manager_id: int) -> List["Department"]:
        """获取指定负责人管理的部门"""
        return await cls.filter(manager_id=manager_id, is_deleted=False)
    
    @classmethod
    async def search(cls, keyword: str, include_inactive: bool = False) -> List["Department"]:
        """搜索部门"""
        query = cls.filter(is_deleted=False)
        
        if not include_inactive:
            query = query.filter(is_active=True)
        
        # 搜索名称、编码、描述
        query = query.filter(
            fields.Q(name__icontains=keyword) |
            fields.Q(code__icontains=keyword) |
            fields.Q(description__icontains=keyword)
        )
        
        return await query.order_by("sort_order")
    
    async def can_delete(self) -> tuple[bool, str]:
        """检查是否可以删除"""
        # 检查是否有子部门
        children_count = await Department.filter(parent_id=self.id, is_deleted=False).count()
        if children_count > 0:
            return False, f"部门下还有 {children_count} 个子部门，无法删除"
        
        # 检查是否有用户
        user_count = await self.get_user_count()
        if user_count > 0:
            return False, f"部门下还有 {user_count} 个用户，无法删除"
        
        return True, "可以删除"
    
    async def move_to(self, new_parent_id: Optional[int]) -> bool:
        """移动部门到新的父部门"""
        # 检查是否会形成循环引用
        if new_parent_id:
            new_parent = await Department.filter(id=new_parent_id).first()
            if not new_parent:
                return False
            
            # 检查新父部门是否为当前部门的后代
            if await new_parent.is_descendant_of(self):
                return False
        
        # 更新父部门和层级
        old_level = self.level
        self.parent_id = new_parent_id
        
        if new_parent_id:
            new_parent = await Department.filter(id=new_parent_id).first()
            self.level = new_parent.level + 1
        else:
            self.level = 0
        
        await self.save()
        
        # 更新所有后代部门的层级
        level_diff = self.level - old_level
        if level_diff != 0:
            await self._update_descendants_level(level_diff)
        
        return True
    
    async def _update_descendants_level(self, level_diff: int):
        """更新后代部门的层级"""
        descendants = await self.get_descendants()
        for dept in descendants:
            dept.level += level_diff
            await dept.save()
    
    async def update_sort_order(self, new_sort_order: int):
        """更新排序"""
        self.sort_order = new_sort_order
        await self.save()
    
    async def activate(self):
        """激活部门"""
        self.is_active = True
        await self.save()
    
    async def deactivate(self):
        """停用部门"""
        self.is_active = False
        await self.save()
