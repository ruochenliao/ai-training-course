"""
MCP (Model Context Protocol) API端点
提供标准化的MCP协议接口
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.mcp_service import mcp_service, MCPMessage, MCPMessageType
from app.models.user import User

mcp_router = APIRouter(tags=["MCP协议"])


class MCPRequest(BaseModel):
    """MCP请求模型"""
    method: str = Field(..., description="MCP方法名")
    params: Dict[str, Any] = Field(default_factory=dict, description="方法参数")
    id: Optional[str] = Field(None, description="请求ID")


class MCPResponse(BaseModel):
    """MCP响应模型"""
    id: str
    type: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: str


class MCPToolCall(BaseModel):
    """MCP工具调用模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class MCPSessionCreate(BaseModel):
    """MCP会话创建模型"""
    conversation_id: str = Field(..., description="对话ID")


@mcp_router.post("/initialize")
async def initialize_mcp(
    current_user: User = Depends(get_current_user)
):
    """
    初始化MCP连接
    """
    try:
        # 确保MCP服务已初始化
        await mcp_service.initialize()
        
        # 创建初始化消息
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="initialize",
            params={
                "clientInfo": {
                    "name": "智能客服客户端",
                    "version": "1.0.0"
                }
            },
            timestamp=datetime.now()
        )
        
        # 处理消息
        response = await mcp_service.server.process_message(message)
        
        return MCPResponse(
            id=response["id"],
            type=response["type"],
            result=response.get("result"),
            error=response.get("error"),
            timestamp=response["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP初始化失败: {str(e)}")


@mcp_router.post("/session", response_model=Dict[str, str])
async def create_mcp_session(
    request: MCPSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建MCP会话
    """
    try:
        session_id = await mcp_service.create_session(
            user_id=str(current_user.id),
            conversation_id=request.conversation_id
        )
        
        return {
            "session_id": session_id,
            "user_id": str(current_user.id),
            "conversation_id": request.conversation_id,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建MCP会话失败: {str(e)}")


@mcp_router.post("/request", response_model=MCPResponse)
async def handle_mcp_request(
    request: MCPRequest,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    处理MCP请求
    """
    try:
        # 创建MCP消息
        message = MCPMessage(
            id=request.id or str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method=request.method,
            params=request.params,
            timestamp=datetime.now()
        )
        
        # 处理消息
        response = await mcp_service.server.process_message(message, session_id)
        
        return MCPResponse(
            id=response["id"],
            type=response["type"],
            result=response.get("result"),
            error=response.get("error"),
            timestamp=response["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP请求处理失败: {str(e)}")


@mcp_router.post("/tools/call", response_model=Dict[str, Any])
async def call_mcp_tool(
    request: MCPToolCall,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    调用MCP工具
    """
    try:
        result = await mcp_service.call_tool(
            tool_name=request.tool_name,
            parameters=request.parameters,
            context_id=session_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@mcp_router.get("/tools", response_model=List[Dict[str, Any]])
async def list_mcp_tools(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的MCP工具列表
    """
    try:
        tools = await mcp_service.get_tools()
        return tools
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")


@mcp_router.get("/resources", response_model=List[Dict[str, Any]])
async def list_mcp_resources(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的MCP资源列表
    """
    try:
        resources = await mcp_service.get_resources()
        return resources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源列表失败: {str(e)}")


@mcp_router.get("/tools/{tool_name}")
async def get_tool_info(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取特定工具的详细信息
    """
    try:
        tools = await mcp_service.get_tools()
        tool_info = next((tool for tool in tools if tool["name"] == tool_name), None)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
        
        return tool_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具信息失败: {str(e)}")


@mcp_router.post("/tools/{tool_name}/test")
async def test_mcp_tool(
    tool_name: str,
    parameters: Dict[str, Any] = {},
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    测试MCP工具
    """
    try:
        # 检查工具是否存在
        tools = await mcp_service.get_tools()
        tool_exists = any(tool["name"] == tool_name for tool in tools)
        
        if not tool_exists:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
        
        # 调用工具
        result = await mcp_service.call_tool(
            tool_name=tool_name,
            parameters=parameters,
            context_id=session_id
        )
        
        return {
            "tool_name": tool_name,
            "test_parameters": parameters,
            "result": result,
            "test_time": datetime.now().isoformat(),
            "success": result.get("type") != "error"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具测试失败: {str(e)}")


@mcp_router.get("/status")
async def get_mcp_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取MCP服务状态
    """
    try:
        # 获取工具和资源数量
        tools = await mcp_service.get_tools()
        resources = await mcp_service.get_resources()
        
        return {
            "status": "running",
            "initialized": mcp_service._initialized,
            "tools_count": len(tools),
            "resources_count": len(resources),
            "server_info": {
                "name": "智能客服MCP服务器",
                "version": "1.0.0",
                "protocol_version": "1.0.0"
            },
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
                "context": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP状态失败: {str(e)}")


@mcp_router.post("/ping")
async def ping_mcp_server(
    current_user: User = Depends(get_current_user)
):
    """
    Ping MCP服务器
    """
    try:
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="ping",
            params={},
            timestamp=datetime.now()
        )
        
        response = await mcp_service.server.process_message(message)
        
        return {
            "ping": "sent",
            "pong": response.get("result", {}).get("pong", False),
            "latency_ms": 0,  # 这里可以计算实际延迟
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ping失败: {str(e)}")


# 工具分类端点
@mcp_router.get("/tools/category/{category}")
async def get_tools_by_category(
    category: str,
    current_user: User = Depends(get_current_user)
):
    """
    按分类获取工具
    """
    try:
        tools = await mcp_service.get_tools()
        category_tools = [tool for tool in tools if tool.get("category") == category]
        
        return {
            "category": category,
            "tools": category_tools,
            "count": len(category_tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类工具失败: {str(e)}")


@mcp_router.get("/tools/categories")
async def get_tool_categories(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有工具分类
    """
    try:
        tools = await mcp_service.get_tools()
        categories = {}
        
        for tool in tools:
            category = tool.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(tool["name"])
        
        return {
            "categories": categories,
            "total_categories": len(categories),
            "total_tools": len(tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具分类失败: {str(e)}")
