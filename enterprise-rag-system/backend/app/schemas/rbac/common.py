"""
统一响应格式标准
"""

from typing import Any, List, Optional, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式 {code, msg, data}"""
    code: int = Field(200, description="响应状态码")
    msg: str = Field("OK", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class PaginationData(BaseModel, Generic[T]):
    """分页数据格式"""
    items: List[T] = Field([], description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")


class PaginationResponse(StandardResponse[PaginationData[T]]):
    """分页响应格式"""
    pass


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(..., description="错误状态码")
    msg: str = Field(..., description="错误消息")
    data: Optional[Any] = Field(None, description="错误详情")


class SuccessResponse(StandardResponse[None]):
    """成功响应格式"""
    pass


# 常用响应类型别名
DepartmentListResponse = PaginationResponse
RoleListResponse = PaginationResponse
PermissionListResponse = PaginationResponse
UserRoleListResponse = PaginationResponse
