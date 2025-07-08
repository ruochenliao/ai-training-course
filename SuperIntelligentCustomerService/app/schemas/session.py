from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class GetSessionListParams(BaseModel):
    create_by: Optional[int] = Field(None, description="创建者")
    create_dept: Optional[int] = Field(None, description="创建部门")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    id: Optional[int] = Field(None, description="主键")
    is_asc: Optional[str] = Field("desc", description="排序方向")
    order_by_column: Optional[str] = Field("create_time", description="排序列")
    page_num: Optional[int] = Field(1, description="当前页数")
    page_size: Optional[int] = Field(10, description="分页大小")
    params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    remark: Optional[str] = Field(None, description="备注")
    session_content: Optional[str] = Field(None, description="会话内容")
    session_title: Optional[str] = Field(None, description="会话标题")
    update_by: Optional[int] = Field(None, description="更新者")
    update_time: Optional[datetime] = Field(None, description="更新时间")
    user_id: int = Field(..., description="用户ID")


class ChatSessionVo(BaseModel):
    id: Optional[str] = Field(None, description="主键")
    remark: Optional[str] = Field(None, description="备注")
    session_content: Optional[str] = Field(None, description="会话内容")
    session_title: Optional[str] = Field(None, description="会话标题")
    user_id: Optional[int] = Field(None, description="用户ID")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class CreateSessionDTO(BaseModel):
    create_by: Optional[int] = Field(None, description="创建者")
    create_dept: Optional[int] = Field(None, description="创建部门")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    id: Optional[str] = Field(None, description="主键")
    params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    remark: Optional[str] = Field(None, description="备注")
    session_content: Optional[str] = Field(None, description="会话内容")
    session_title: str = Field(..., description="会话标题")
    update_by: Optional[int] = Field(None, description="更新者")
    update_time: Optional[datetime] = Field(None, description="更新时间")
    user_id: int = Field(..., description="用户ID")


class SessionCreate(BaseModel):
    session_title: str = Field(..., description="会话标题")
    session_content: Optional[str] = Field(None, description="会话内容")
    user_id: int = Field(..., description="用户ID")
    remark: Optional[str] = Field(None, description="备注")


class SessionUpdate(BaseModel):
    id: int = Field(..., description="主键")
    session_title: Optional[str] = Field(None, description="会话标题")
    session_content: Optional[str] = Field(None, description="会话内容")
    remark: Optional[str] = Field(None, description="备注")
