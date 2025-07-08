from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Message(BaseModel):
    content: Optional[str] = Field(None, description="消息内容")
    name: Optional[str] = Field(None, description="名称")
    reasoning_content: Optional[str] = Field(None, description="推理内容")
    role: Optional[str] = Field(None, description="角色", pattern="^(system|user|assistant|function|tool)$")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用")


class SendDTO(BaseModel):
    app_id: Optional[str] = Field(None, description="应用ID")
    content_number: Optional[int] = Field(None, description="上下文条数")
    is_mcp: Optional[bool] = Field(False, description="是否开启MCP")
    kid: Optional[str] = Field(None, description="知识库ID")
    messages: List[Message] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型名称")
    prompt: Optional[str] = Field(None, description="提示词")
    search: Optional[bool] = Field(False, description="是否开启联网搜索")
    session_id: Optional[str] = Field(None, description="会话ID", alias="sessionId")
    stream: Optional[bool] = Field(False, description="是否开启流式对话")
    sys_prompt: Optional[str] = Field(None, description="系统提示词")
    user_id: Optional[int] = Field(None, description="用户ID")
    using_context: Optional[bool] = Field(True, description="是否携带上下文")


class GetChatListParams(BaseModel):
    content: Optional[str] = Field(None, description="消息内容")
    create_by: Optional[int] = Field(None, description="创建者")
    create_dept: Optional[int] = Field(None, description="创建部门")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    deduct_cost: Optional[float] = Field(None, description="扣除金额")
    id: Optional[int] = Field(None, description="主键")
    is_asc: Optional[str] = Field("desc", description="排序方向")
    model_name: Optional[str] = Field(None, description="模型名称")
    order_by_column: Optional[str] = Field("created_at", description="排序列")
    page_num: Optional[int] = Field(1, description="当前页数")
    page_size: Optional[int] = Field(10, description="分页大小")
    params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    remark: Optional[str] = Field(None, description="备注")
    role: Optional[str] = Field(None, description="对话角色")
    session_id: Optional[str] = Field(None, description="会话ID")
    total_tokens: Optional[int] = Field(None, description="累计Tokens")
    update_by: Optional[int] = Field(None, description="更新者")
    update_time: Optional[datetime] = Field(None, description="更新时间")
    user_id: Optional[int] = Field(None, description="用户ID")


class ChatMessageVo(BaseModel):
    id: Optional[int] = Field(None, description="主键")
    content: Optional[str] = Field(None, description="消息内容")
    deduct_cost: Optional[float] = Field(None, description="扣除金额")
    model_name: Optional[str] = Field(None, description="模型名称")
    remark: Optional[str] = Field(None, description="备注")
    role: Optional[str] = Field(None, description="对话角色")
    session_id: Optional[int] = Field(None, description="会话ID")
    total_tokens: Optional[int] = Field(None, description="累计Tokens")
    user_id: Optional[int] = Field(None, description="用户ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class ChatMessageCreate(BaseModel):
    session_id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    role: str = Field(..., description="对话角色")
    content: str = Field(..., description="消息内容")
    model_name: Optional[str] = Field(None, description="模型名称")
    total_tokens: Optional[int] = Field(0, description="累计Tokens")
    deduct_cost: Optional[float] = Field(0, description="扣除金额")
    remark: Optional[str] = Field(None, description="备注")


class ChatMessageUpdate(BaseModel):
    id: int = Field(..., description="主键")
    content: Optional[str] = Field(None, description="消息内容")
    model_name: Optional[str] = Field(None, description="模型名称")
    total_tokens: Optional[int] = Field(None, description="累计Tokens")
    deduct_cost: Optional[float] = Field(None, description="扣除金额")
    remark: Optional[str] = Field(None, description="备注")
