"""
部门相关数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """部门基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=50, description="部门代码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: int = Field(0, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")


class DepartmentCreate(DepartmentBase):
    """创建部门模式"""
    pass


class DepartmentUpdate(BaseModel):
    """更新部门模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: Optional[int] = Field(None, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")
    status: Optional[str] = Field(None, description="状态")


class DepartmentResponse(DepartmentBase):
    """部门响应模式"""
    id: int
    level: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    children: Optional[List["DepartmentResponse"]] = None
    parent: Optional["DepartmentResponse"] = None
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# 解决前向引用问题
DepartmentResponse.model_rebuild()
