"""
菜单相关Pydantic模式
定义菜单相关的请求和响应模式
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class MenuBase(BaseModel):
    """菜单基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="菜单名称")
    title: str = Field(..., min_length=1, max_length=100, description="菜单标题")
    path: Optional[str] = Field(None, max_length=255, description="路由路径")
    component: Optional[str] = Field(None, max_length=255, description="组件路径")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: int = Field(0, description="排序")
    is_visible: bool = Field(True, description="是否可见")
    is_external: bool = Field(False, description="是否外链")
    cache: bool = Field(False, description="是否缓存")
    redirect: Optional[str] = Field(None, max_length=255, description="重定向路径")
    
    @validator('path')
    def validate_path(cls, v):
        """验证路由路径"""
        if v and not v.startswith('/'):
            raise ValueError('路由路径必须以 / 开头')
        return v


class MenuCreate(MenuBase):
    """菜单创建模式"""
    pass


class MenuUpdate(BaseModel):
    """菜单更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="菜单名称")
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="菜单标题")
    path: Optional[str] = Field(None, max_length=255, description="路由路径")
    component: Optional[str] = Field(None, max_length=255, description="组件路径")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_visible: Optional[bool] = Field(None, description="是否可见")
    is_external: Optional[bool] = Field(None, description="是否外链")
    cache: Optional[bool] = Field(None, description="是否缓存")
    redirect: Optional[str] = Field(None, max_length=255, description="重定向路径")


class MenuResponse(BaseModel):
    """菜单响应模式"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    sort_order: int = Field(..., description="排序")
    is_visible: bool = Field(..., description="是否可见")
    is_external: bool = Field(..., description="是否外链")
    cache: bool = Field(..., description="是否缓存")
    redirect: Optional[str] = Field(None, description="重定向路径")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class MenuTreeResponse(BaseModel):
    """菜单树形响应模式"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    sort_order: int = Field(..., description="排序")
    is_visible: bool = Field(..., description="是否可见")
    is_external: bool = Field(..., description="是否外链")
    cache: bool = Field(..., description="是否缓存")
    redirect: Optional[str] = Field(None, description="重定向路径")
    children: List["MenuTreeResponse"] = Field(default_factory=list, description="子菜单")
    
    class Config:
        from_attributes = True


class MenuListResponse(BaseModel):
    """菜单列表响应模式"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    parent_name: Optional[str] = Field(None, description="父菜单名称")
    sort_order: int = Field(..., description="排序")
    is_visible: bool = Field(..., description="是否可见")
    is_external: bool = Field(..., description="是否外链")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class MenuSelectOption(BaseModel):
    """菜单选择选项模式"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    
    class Config:
        from_attributes = True


class MenuRouteResponse(BaseModel):
    """菜单路由响应模式（前端路由使用）"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="路由名称")
    path: str = Field(..., description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    redirect: Optional[str] = Field(None, description="重定向路径")
    meta: dict = Field(..., description="路由元信息")
    children: List["MenuRouteResponse"] = Field(default_factory=list, description="子路由")
    
    class Config:
        from_attributes = True


class BreadcrumbItem(BaseModel):
    """面包屑项模式"""
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    path: Optional[str] = Field(None, description="路由路径")


class BreadcrumbResponse(BaseModel):
    """面包屑响应模式"""
    items: List[BreadcrumbItem] = Field(..., description="面包屑项列表")


# 更新前向引用
MenuTreeResponse.model_rebuild()
MenuRouteResponse.model_rebuild()
