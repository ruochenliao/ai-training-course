"""
通用Pydantic模式
定义通用的请求和响应模式
"""

from typing import Any, Optional, List, Generic, TypeVar, Dict, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import time
import os
from app.utils.error_codes import ErrorCode


T = TypeVar('T')


class ResponseMetadata(BaseModel):
    """响应元数据"""
    api_version: str = Field("v1.0.0", description="API版本")
    server_time: int = Field(default_factory=lambda: int(time.time() * 1000), description="服务器时间戳(毫秒)")
    execution_time: Optional[float] = Field(None, description="执行时间(毫秒)")
    server_id: Optional[str] = Field(default_factory=lambda: os.getenv("SERVER_ID", "server-001"), description="服务器ID")


class BaseResponse(BaseModel, Generic[T]):
    """企业级基础响应模式"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="请求ID")
    trace_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="链路追踪ID")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse):
    """成功响应模式"""
    code: int = 200
    message: str = "操作成功"


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")
    value: Optional[Any] = Field(None, description="错误值")


class ErrorResponse(BaseResponse):
    """企业级错误响应模式"""
    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    data: Optional[Any] = None
    errors: Optional[List[ErrorDetail]] = Field(None, description="详细错误信息")
    error_type: Optional[str] = Field(None, description="错误类型")
    detail: Optional[str] = Field(None, description="错误详情")
    help_url: Optional[str] = Field(None, description="帮助文档链接")


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应模式"""
    code: int = 400
    message: str = "请求参数验证失败"


class UnauthorizedResponse(ErrorResponse):
    """未授权响应模式"""
    code: int = 401
    message: str = "未授权访问"


class ForbiddenResponse(ErrorResponse):
    """禁止访问响应模式"""
    code: int = 403
    message: str = "权限不足"


class NotFoundResponse(ErrorResponse):
    """资源未找到响应模式"""
    code: int = 404
    message: str = "资源未找到"


class InternalServerErrorResponse(ErrorResponse):
    """服务器内部错误响应模式"""
    code: int = 500
    message: str = "服务器内部错误"


class PaginationParams(BaseModel):
    """分页参数模式"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")

    class Config:
        extra = "forbid"


class PaginationInfo(BaseModel):
    """分页信息"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    start_index: int = Field(..., description="起始索引")
    end_index: int = Field(..., description="结束索引")


class PaginationResponse(BaseModel, Generic[T]):
    """企业级分页响应模式"""
    items: List[T] = Field(..., description="数据列表")
    pagination: PaginationInfo = Field(..., description="分页信息")

    # 兼容旧版本字段
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class IDResponse(BaseModel):
    """ID响应模式"""
    id: int = Field(..., description="资源ID")


class StatusResponse(BaseModel):
    """状态响应模式"""
    success: bool = Field(..., description="操作是否成功")
    affected_rows: Optional[int] = Field(None, description="影响的行数")


class BulkOperationRequest(BaseModel):
    """批量操作请求模式"""
    ids: List[int] = Field(..., min_items=1, description="ID列表")
    action: str = Field(..., description="操作类型")


class BulkOperationResponse(BaseModel):
    """批量操作响应模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_ids: List[int] = Field(default_factory=list, description="失败的ID列表")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


class TreeNode(BaseModel):
    """树形节点模式"""
    id: int = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    children: List["TreeNode"] = Field(default_factory=list, description="子节点")
    parent_id: Optional[int] = Field(None, description="父节点ID")
    level: int = Field(0, description="节点层级")
    sort_order: int = Field(0, description="排序")
    is_leaf: bool = Field(True, description="是否叶子节点")
    metadata: Optional[Dict[str, Any]] = Field(None, description="节点元数据")


class ApiResponse(BaseResponse):
    """标准API响应"""

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "操作成功",
        request_id: str = None,
        trace_id: str = None
    ):
        """创建成功响应"""
        return cls(
            code=200,
            message=message,
            data=data,
            request_id=request_id or str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4())
        )

    @classmethod
    def error(
        cls,
        code: int,
        message: str,
        data: Any = None,
        errors: List[ErrorDetail] = None,
        request_id: str = None,
        trace_id: str = None
    ):
        """创建错误响应"""
        return cls(
            code=code,
            message=message,
            data=data,
            request_id=request_id or str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4())
        )


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间(秒)")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="依赖服务状态")


# 更新前向引用
TreeNode.model_rebuild()
