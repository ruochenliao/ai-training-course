"""
数据权限相关的Pydantic模型
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class DataPermissionType(str, Enum):
    """数据权限类型"""
    ALL = "all"
    SELF = "self"
    DEPARTMENT = "department"
    DEPARTMENT_AND_SUB = "department_and_sub"
    CUSTOM = "custom"


class DataPermissionScope(str, Enum):
    """数据权限范围"""
    USER = "user"
    DEPARTMENT = "department"
    ROLE = "role"
    CUSTOM = "custom"


class DataPermissionBase(BaseModel):
    """数据权限基础模型"""
    name: str = Field(..., description="权限名称", max_length=100)
    code: str = Field(..., description="权限代码", max_length=100)
    description: Optional[str] = Field(None, description="权限描述")
    permission_type: DataPermissionType = Field(..., description="权限类型")
    scope: DataPermissionScope = Field(..., description="权限范围")
    resource_type: str = Field(..., description="资源类型", max_length=50)
    custom_conditions: Optional[Dict[str, Any]] = Field(None, description="自定义条件")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")

    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('权限代码不能为空')
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('权限名称不能为空')
        return v.strip()


class DataPermissionCreate(DataPermissionBase):
    """创建数据权限"""
    pass


class DataPermissionUpdate(BaseModel):
    """更新数据权限"""
    name: Optional[str] = Field(None, description="权限名称", max_length=100)
    code: Optional[str] = Field(None, description="权限代码", max_length=100)
    description: Optional[str] = Field(None, description="权限描述")
    permission_type: Optional[DataPermissionType] = Field(None, description="权限类型")
    scope: Optional[DataPermissionScope] = Field(None, description="权限范围")
    resource_type: Optional[str] = Field(None, description="资源类型", max_length=50)
    custom_conditions: Optional[Dict[str, Any]] = Field(None, description="自定义条件")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class DataPermissionResponse(DataPermissionBase):
    """数据权限响应"""
    id: int = Field(..., description="权限ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class DataPermissionListItem(BaseModel):
    """数据权限列表项"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    permission_type: DataPermissionType = Field(..., description="权限类型")
    scope: DataPermissionScope = Field(..., description="权限范围")
    resource_type: str = Field(..., description="资源类型")
    is_active: bool = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class DataPermissionListResponse(BaseModel):
    """数据权限列表响应"""
    items: List[DataPermissionListItem] = Field(..., description="权限列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class DataPermissionSearchParams(BaseModel):
    """数据权限搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词搜索")
    permission_type: Optional[DataPermissionType] = Field(None, description="权限类型")
    scope: Optional[DataPermissionScope] = Field(None, description="权限范围")
    resource_type: Optional[str] = Field(None, description="资源类型")
    is_active: Optional[bool] = Field(None, description="是否启用")


class DataPermissionAssignRequest(BaseModel):
    """数据权限分配请求"""
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")


class DataPermissionAssignResponse(BaseModel):
    """数据权限分配响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class DataPermissionCheckRequest(BaseModel):
    """数据权限检查请求"""
    user_id: int = Field(..., description="用户ID")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    action: str = Field(..., description="操作类型")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class DataPermissionCheckResponse(BaseModel):
    """数据权限检查响应"""
    has_permission: bool = Field(..., description="是否有权限")
    permission_type: Optional[DataPermissionType] = Field(None, description="权限类型")
    reason: Optional[str] = Field(None, description="原因说明")


class UserDataPermissionItem(BaseModel):
    """用户数据权限项"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    permission_type: DataPermissionType = Field(..., description="权限类型")
    scope: DataPermissionScope = Field(..., description="权限范围")
    granted_at: datetime = Field(..., description="授权时间")
    granted_by: Optional[str] = Field(None, description="授权人")

    class Config:
        from_attributes = True


class RoleDataPermissionItem(BaseModel):
    """角色数据权限项"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    permission_type: DataPermissionType = Field(..., description="权限类型")
    scope: DataPermissionScope = Field(..., description="权限范围")
    granted_at: datetime = Field(..., description="授权时间")
    granted_by: Optional[str] = Field(None, description="授权人")

    class Config:
        from_attributes = True


class DataPermissionSelectOption(BaseModel):
    """数据权限选择选项"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    permission_type: DataPermissionType = Field(..., description="权限类型")
    scope: DataPermissionScope = Field(..., description="权限范围")

    class Config:
        from_attributes = True


class BulkOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[int] = Field(..., description="ID列表")
    action: str = Field(..., description="操作类型")


class BulkOperationResponse(BaseModel):
    """批量操作响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class DataPermissionStatistics(BaseModel):
    """数据权限统计"""
    total_permissions: int = Field(..., description="总权限数")
    active_permissions: int = Field(..., description="活跃权限数")
    inactive_permissions: int = Field(..., description="非活跃权限数")
    permissions_by_type: Dict[str, int] = Field(..., description="按类型统计")
    permissions_by_scope: Dict[str, int] = Field(..., description="按范围统计")
    top_used_permissions: List[Dict[str, Any]] = Field(..., description="使用最多的权限")


class CustomConditionTemplate(BaseModel):
    """自定义条件模板"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    conditions: Dict[str, Any] = Field(..., description="条件配置")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="示例")


class DataPermissionImportItem(BaseModel):
    """数据权限导入项"""
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    permission_type: str = Field(..., description="权限类型")
    scope: str = Field(..., description="权限范围")
    resource_type: str = Field(..., description="资源类型")
    custom_conditions: Optional[str] = Field(None, description="自定义条件(JSON字符串)")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")


class DataPermissionImportResponse(BaseModel):
    """数据权限导入响应"""
    total_count: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数")
    failed_count: int = Field(..., description="失败数")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目")
    created_permissions: List[DataPermissionResponse] = Field(default_factory=list, description="创建的权限")
