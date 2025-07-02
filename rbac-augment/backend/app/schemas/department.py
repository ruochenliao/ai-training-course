"""
部门数据模式
定义部门相关的请求和响应模式
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DepartmentBase(BaseModel):
    """部门基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=50, description="部门编码")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: int = Field(0, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    address: Optional[str] = Field(None, max_length=255, description="办公地址")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('code')
    def validate_code(cls, v):
        """验证部门编码格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('部门编码只能包含字母、数字、下划线和连字符')
        return v.upper()
    
    @validator('email')
    def validate_email(cls, v):
        """验证邮箱格式"""
        if v and '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


class DepartmentCreate(DepartmentBase):
    """部门创建模式"""
    pass


class DepartmentUpdate(BaseModel):
    """部门更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    description: Optional[str] = Field(None, description="部门描述")
    sort_order: Optional[int] = Field(None, description="排序")
    manager_id: Optional[int] = Field(None, description="部门负责人ID")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[str] = Field(None, max_length=100, description="联系邮箱")
    address: Optional[str] = Field(None, max_length=255, description="办公地址")
    is_active: Optional[bool] = Field(None, description="是否启用")
    
    @validator('email')
    def validate_email(cls, v):
        """验证邮箱格式"""
        if v and '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


class DepartmentMove(BaseModel):
    """部门移动模式"""
    new_parent_id: Optional[int] = Field(None, description="新父部门ID")


class DepartmentResponse(DepartmentBase):
    """部门响应模式"""
    id: int = Field(..., description="部门ID")
    level: int = Field(..., description="部门层级")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DepartmentDetailResponse(DepartmentResponse):
    """部门详情响应模式"""
    parent: Optional["DepartmentResponse"] = Field(None, description="父部门")
    children: List["DepartmentResponse"] = Field(default_factory=list, description="子部门")
    manager: Optional[Dict[str, Any]] = Field(None, description="部门负责人")
    user_count: int = Field(0, description="用户数量")
    path: str = Field("", description="部门路径")
    full_code: str = Field("", description="完整部门编码")


class DepartmentTreeNode(BaseModel):
    """部门树节点模式"""
    id: int = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    code: str = Field(..., description="部门编码")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    level: int = Field(..., description="部门层级")
    sort_order: int = Field(..., description="排序")
    is_active: bool = Field(..., description="是否启用")
    user_count: int = Field(0, description="用户数量")
    children: List["DepartmentTreeNode"] = Field(default_factory=list, description="子部门")
    
    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    """部门列表响应模式"""
    departments: List[DepartmentResponse] = Field(..., description="部门列表")
    total: int = Field(..., description="总数量")


class DepartmentTreeResponse(BaseModel):
    """部门树响应模式"""
    tree: List[DepartmentTreeNode] = Field(..., description="部门树")
    total: int = Field(..., description="总部门数量")


class DepartmentSelectOption(BaseModel):
    """部门选择选项模式"""
    id: int = Field(..., description="部门ID")
    name: str = Field(..., description="部门名称")
    code: str = Field(..., description="部门编码")
    level: int = Field(..., description="部门层级")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    is_active: bool = Field(..., description="是否启用")
    disabled: bool = Field(False, description="是否禁用选择")


class DepartmentUserAssign(BaseModel):
    """部门用户分配模式"""
    user_ids: List[int] = Field(..., min_items=1, description="用户ID列表")
    department_id: int = Field(..., description="部门ID")


class DepartmentUserResponse(BaseModel):
    """部门用户响应模式"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="姓名")
    email: str = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, description="电话")
    is_active: bool = Field(..., description="是否激活")
    is_manager: bool = Field(False, description="是否为部门负责人")


class DepartmentStatistics(BaseModel):
    """部门统计模式"""
    total_departments: int = Field(..., description="总部门数")
    active_departments: int = Field(..., description="活跃部门数")
    inactive_departments: int = Field(..., description="非活跃部门数")
    total_users: int = Field(..., description="总用户数")
    departments_by_level: Dict[int, int] = Field(..., description="各层级部门数量")
    top_departments_by_users: List[Dict[str, Any]] = Field(..., description="用户数最多的部门")


class DepartmentSearchParams(BaseModel):
    """部门搜索参数模式"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    level: Optional[int] = Field(None, description="部门层级")
    is_active: Optional[bool] = Field(None, description="是否启用")
    manager_id: Optional[int] = Field(None, description="负责人ID")
    include_children: bool = Field(False, description="是否包含子部门")


class DepartmentBatchOperation(BaseModel):
    """部门批量操作模式"""
    department_ids: List[int] = Field(..., min_items=1, description="部门ID列表")
    operation: str = Field(..., description="操作类型：activate/deactivate/delete")


class DepartmentBatchOperationResponse(BaseModel):
    """部门批量操作响应模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_departments: List[Dict[str, Any]] = Field(default_factory=list, description="失败的部门信息")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


class DepartmentImportData(BaseModel):
    """部门导入数据模式"""
    name: str = Field(..., description="部门名称")
    code: str = Field(..., description="部门编码")
    parent_code: Optional[str] = Field(None, description="父部门编码")
    description: Optional[str] = Field(None, description="部门描述")
    manager_username: Optional[str] = Field(None, description="负责人用户名")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="联系邮箱")
    address: Optional[str] = Field(None, description="办公地址")
    sort_order: int = Field(0, description="排序")


class DepartmentImportResponse(BaseModel):
    """部门导入响应模式"""
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败的项目")
    created_departments: List[DepartmentResponse] = Field(default_factory=list, description="创建的部门")


class DepartmentExportParams(BaseModel):
    """部门导出参数模式"""
    include_inactive: bool = Field(False, description="是否包含非活跃部门")
    include_users: bool = Field(False, description="是否包含用户信息")
    format: str = Field("excel", description="导出格式：excel/csv")
    parent_id: Optional[int] = Field(None, description="指定父部门ID")


# 更新前向引用
DepartmentDetailResponse.model_rebuild()
DepartmentTreeNode.model_rebuild()
