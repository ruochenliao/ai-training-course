# -*- coding: utf-8 -*-
"""
MCP API端点
提供MCP工具的HTTP API接口
"""
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.autogen_workbench import mcp_workbench
from app.core.dependency import DependAuth
from app.core.mcp_tools import list_mcp_tools, execute_mcp_tool
from app.models.admin import User
from app.schemas.base import Success

router = APIRouter()


class MCPToolRequest(BaseModel):
    """MCP工具请求模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class MCPToolResponse(BaseModel):
    """MCP工具响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    error: Optional[str] = Field(None, description="错误信息")
    tool_name: str = Field(..., description="工具名称")


class MCPChatRequest(BaseModel):
    """MCP聊天请求模型"""
    message: str = Field(..., description="用户消息")
    tools: Optional[List[str]] = Field(None, description="启用的工具列表")
    system_message: Optional[str] = Field(None, description="系统消息")


@router.get("/tools", summary="获取可用的MCP工具列表")
async def get_mcp_tools() -> Success:
    """获取所有可用的MCP工具"""
    try:
        tools = list_mcp_tools()
        return Success(
            data={
                "tools": tools,
                "total": len(tools)
            },
            message="成功获取MCP工具列表"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@router.post("/tools/execute", summary="执行MCP工具")
async def execute_mcp_tool_api(
        request: MCPToolRequest
) -> MCPToolResponse:
    """执行指定的MCP工具"""
    try:
        result = await execute_mcp_tool(request.tool_name, **request.parameters)

        return MCPToolResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            tool_name=request.tool_name
        )
    except Exception as e:
        return MCPToolResponse(
            success=False,
            error=f"工具执行异常: {str(e)}",
            tool_name=request.tool_name
        )


@router.get("/workbench/agents", summary="获取MCP工作台代理列表")
async def get_workbench_agents() -> Success:
    """获取MCP工作台中的所有代理"""
    try:
        agents = mcp_workbench.list_agents()
        return Success(
            data={
                "agents": agents,
                "total": len(agents)
            },
            message="成功获取代理列表"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取代理列表失败: {str(e)}")


@router.post("/workbench/chat", summary="使用MCP工作台进行对话")
async def chat_with_workbench(
        request: MCPChatRequest,
        current_user: User = DependAuth
) -> Success:
    """使用MCP工作台创建临时代理进行对话"""
    try:
        # 创建临时代理
        agent_name = f"temp_agent_{current_user.id}"

        agent = mcp_workbench.create_agent(
            agent_name=agent_name,
            model_name="deepseek-chat",
            system_message=request.system_message,
            tools=request.tools,
            buffer_size=1
        )

        # 执行对话
        result = await agent.run(task=request.message)

        # 提取响应内容
        response_content = ""
        if hasattr(result, 'messages') and result.messages:
            for message in result.messages:
                if hasattr(message, 'content'):
                    response_content += str(message.content)

        return Success(
            data={
                "response": response_content,
                "agent_name": agent_name,
                "tools_used": request.tools or [],
                "task_result": str(result) if result else None
            },
            message="对话完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.get("/status", summary="获取MCP服务状态")
async def get_mcp_status(current_user: User = DependAuth) -> Success:
    """获取MCP服务的状态信息"""
    try:
        tools = list_mcp_tools()
        agents = mcp_workbench.list_agents()

        return Success(
            data={
                "mcp_enabled": True,
                "tools_count": len(tools),
                "agents_count": len(agents),
                "available_tools": [tool["name"] for tool in tools],
                "active_agents": agents,
                "shop_service_url": "http://localhost:8002",
                "version": "1.0.0"
            },
            message="MCP服务运行正常"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/tools/{tool_name}/schema", summary="获取工具的参数模式")
async def get_tool_schema(
        tool_name: str
) -> Success:
    """获取指定工具的参数模式"""
    try:
        # 这里可以根据工具名称返回对应的参数模式
        schemas = {
            "get_products": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                    "size": {"type": "integer", "description": "每页数量，默认10", "default": 10},
                    "category_id": {"type": "integer", "description": "分类ID，可选"},
                    "keyword": {"type": "string", "description": "搜索关键词，可选"},
                    "is_featured": {"type": "boolean", "description": "是否推荐商品，可选"}
                },
                "required": []
            },
            "get_orders": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                    "size": {"type": "integer", "description": "每页数量，默认10", "default": 10},
                    "customer_id": {"type": "integer", "description": "客户ID，可选"},
                    "status": {"type": "string", "description": "订单状态，可选"}
                },
                "required": []
            },
            "get_customers": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                    "size": {"type": "integer", "description": "每页数量，默认10", "default": 10},
                    "keyword": {"type": "string", "description": "搜索关键词，可选"}
                },
                "required": []
            },
            "get_promotions": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                    "size": {"type": "integer", "description": "每页数量，默认10", "default": 10},
                    "is_active": {"type": "boolean", "description": "是否启用，可选"}
                },
                "required": []
            },
            "get_carts": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                    "size": {"type": "integer", "description": "每页数量，默认10", "default": 10},
                    "customer_id": {"type": "integer", "description": "客户ID，可选"}
                },
                "required": []
            }
        }

        if tool_name not in schemas:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")

        return Success(
            data={
                "tool_name": tool_name,
                "schema": schemas[tool_name]
            },
            message=f"成功获取工具 {tool_name} 的参数模式"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具模式失败: {str(e)}")


@router.get("/health", summary="MCP健康检查")
async def mcp_health_check() -> Dict[str, Any]:
    """MCP服务健康检查，无需认证"""
    try:
        tools_count = len(list_mcp_tools())
        return {
            "status": "healthy",
            "mcp_enabled": True,
            "tools_available": tools_count,
            "timestamp": "2025-01-27T12:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-01-27T12:00:00Z"
        }
