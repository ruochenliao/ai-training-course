"""
MCP (Model Context Protocol) 服务
提供标准化的模型上下文协议支持，实现与外部工具和数据源的无缝集成
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime

from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class MCPMessageType(str, Enum):
    """MCP消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPResourceType(str, Enum):
    """MCP资源类型"""
    TOOL = "tool"
    PROMPT = "prompt"
    RESOURCE = "resource"
    CONTEXT = "context"


@dataclass
class MCPMessage:
    """MCP消息基类"""
    id: str
    type: MCPMessageType
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    category: str = "general"
    version: str = "1.0.0"
    enabled: bool = True


@dataclass
class MCPResource:
    """MCP资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class MCPContext:
    """MCP上下文"""
    session_id: str
    user_id: str
    conversation_id: str
    variables: Dict[str, Any]
    tools: List[str]
    resources: List[str]


class MCPServer:
    """MCP服务器实现"""
    
    def __init__(self):
        """初始化MCP服务器"""
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.contexts: Dict[str, MCPContext] = {}
        self.handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        
        # 注册核心处理器
        self._register_core_handlers()
        
        logger.info("MCP服务器初始化完成")
    
    def _register_core_handlers(self):
        """注册核心处理器"""
        self.handlers.update({
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
            "context/get": self._handle_get_context,
            "context/set": self._handle_set_context,
            "ping": self._handle_ping,
            "initialize": self._handle_initialize
        })
    
    async def register_tool(self, tool: MCPTool):
        """注册工具"""
        try:
            self.tools[tool.name] = tool
            logger.info(f"工具注册成功: {tool.name}")
        except Exception as e:
            logger.error(f"工具注册失败 {tool.name}: {e}")
            raise
    
    async def register_resource(self, resource: MCPResource):
        """注册资源"""
        try:
            self.resources[resource.uri] = resource
            logger.info(f"资源注册成功: {resource.uri}")
        except Exception as e:
            logger.error(f"资源注册失败 {resource.uri}: {e}")
            raise
    
    async def create_context(self, user_id: str, conversation_id: str) -> str:
        """创建上下文"""
        session_id = str(uuid.uuid4())
        context = MCPContext(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            variables={},
            tools=list(self.tools.keys()),
            resources=list(self.resources.keys())
        )
        self.contexts[session_id] = context
        logger.info(f"上下文创建成功: {session_id}")
        return session_id
    
    async def process_message(self, message: MCPMessage, context_id: Optional[str] = None) -> Dict[str, Any]:
        """处理MCP消息"""
        try:
            # 应用中间件
            for middleware in self.middleware:
                message = await middleware(message)
            
            # 获取处理器
            handler = self.handlers.get(message.method)
            if not handler:
                raise ValueError(f"未知的方法: {message.method}")
            
            # 获取上下文
            context = None
            if context_id and context_id in self.contexts:
                context = self.contexts[context_id]
            
            # 执行处理器
            result = await handler(message.params, context)
            
            return {
                "id": message.id,
                "type": MCPMessageType.RESPONSE,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"MCP消息处理失败: {e}")
            return {
                "id": message.id,
                "type": MCPMessageType.ERROR,
                "error": {
                    "code": -1,
                    "message": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_list_tools(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理工具列表请求"""
        tools_list = []
        for tool in self.tools.values():
            if tool.enabled:
                tools_list.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "category": tool.category,
                    "version": tool.version
                })
        
        return {
            "tools": tools_list,
            "total": len(tools_list)
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        tool_params = params.get("parameters", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        if not tool.enabled:
            raise ValueError(f"工具已禁用: {tool_name}")
        
        try:
            # 调用工具处理器
            result = await tool.handler(tool_params, context)
            
            return {
                "tool": tool_name,
                "result": result,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"工具调用失败 {tool_name}: {e}")
            return {
                "tool": tool_name,
                "error": str(e),
                "success": False
            }
    
    async def _handle_list_resources(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理资源列表请求"""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type,
                "metadata": resource.metadata
            })
        
        return {
            "resources": resources_list,
            "total": len(resources_list)
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理资源读取请求"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            raise ValueError(f"资源不存在: {uri}")
        
        resource = self.resources[uri]
        
        return {
            "uri": resource.uri,
            "content": resource.content,
            "mime_type": resource.mime_type,
            "metadata": resource.metadata
        }
    
    async def _handle_get_context(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理获取上下文请求"""
        if not context:
            raise ValueError("上下文不存在")
        
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "conversation_id": context.conversation_id,
            "variables": context.variables,
            "tools": context.tools,
            "resources": context.resources
        }
    
    async def _handle_set_context(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理设置上下文请求"""
        if not context:
            raise ValueError("上下文不存在")
        
        # 更新上下文变量
        variables = params.get("variables", {})
        context.variables.update(variables)
        
        return {
            "success": True,
            "updated_variables": variables
        }
    
    async def _handle_ping(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理ping请求"""
        return {
            "pong": True,
            "timestamp": datetime.now().isoformat(),
            "server": "MCP Server v1.0.0"
        }
    
    async def _handle_initialize(self, params: Dict[str, Any], context: Optional[MCPContext]) -> Dict[str, Any]:
        """处理初始化请求"""
        client_info = params.get("clientInfo", {})
        
        return {
            "protocolVersion": "1.0.0",
            "serverInfo": {
                "name": "智能客服MCP服务器",
                "version": "1.0.0",
                "description": "基于MCP协议的智能客服工具和资源服务器"
            },
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
                "context": True
            }
        }
    
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)
    
    async def shutdown(self):
        """关闭服务器"""
        logger.info("MCP服务器正在关闭...")
        self.tools.clear()
        self.resources.clear()
        self.contexts.clear()
        logger.info("MCP服务器已关闭")


class MCPService:
    """MCP服务管理器"""
    
    def __init__(self):
        """初始化MCP服务"""
        self.server = MCPServer()
        self._initialized = False
        
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        try:
            # 注册内置工具
            await self._register_builtin_tools()
            
            # 注册内置资源
            await self._register_builtin_resources()
            
            self._initialized = True
            logger.info("MCP服务初始化完成")
            
        except Exception as e:
            logger.error(f"MCP服务初始化失败: {e}")
            raise
    
    async def _register_builtin_tools(self):
        """注册内置工具"""
        try:
            # 导入工具集
            from app.tools.ecommerce_tools import ecommerce_tools
            from app.tools.search_tools import search_tools
            from app.tools.file_tools import file_tools

            # 注册电商工具
            ecommerce_tool_list = await ecommerce_tools.get_tools()
            for tool in ecommerce_tool_list:
                await self.server.register_tool(tool)

            # 注册搜索工具
            search_tool_list = await search_tools.get_tools()
            for tool in search_tool_list:
                await self.server.register_tool(tool)

            # 注册文件工具
            file_tool_list = await file_tools.get_tools()
            for tool in file_tool_list:
                await self.server.register_tool(tool)

            logger.info(f"内置工具注册完成: {len(self.server.tools)} 个工具")

        except Exception as e:
            logger.error(f"注册内置工具失败: {e}")
            raise

    async def _register_builtin_resources(self):
        """注册内置资源"""
        try:
            # 注册系统信息资源
            system_info_resource = MCPResource(
                uri="system://info",
                name="系统信息",
                description="智能客服系统的基本信息和状态",
                mime_type="application/json",
                content={
                    "name": "智能客服系统",
                    "version": "1.0.0",
                    "description": "基于MCP协议的智能客服系统",
                    "capabilities": ["文档处理", "电商工具", "搜索功能", "文件管理"],
                    "status": "运行中",
                    "timestamp": datetime.now().isoformat()
                },
                metadata={
                    "type": "system_info",
                    "readonly": True
                }
            )
            await self.server.register_resource(system_info_resource)

            # 注册帮助文档资源
            help_resource = MCPResource(
                uri="help://tools",
                name="工具帮助文档",
                description="所有可用工具的使用说明",
                mime_type="text/markdown",
                content="""# MCP工具使用指南

## 电商工具
- `search_products`: 搜索商品信息
- `get_product_details`: 获取商品详情
- `check_order_status`: 查询订单状态
- `get_customer_orders`: 获取客户订单历史

## 搜索工具
- `search_documents`: 搜索文档内容
- `search_knowledge_base`: 搜索知识库
- `search_chat_history`: 搜索聊天历史
- `web_search`: 网络搜索

## 文件工具
- `upload_file`: 上传文件
- `list_files`: 列出文件
- `get_file_info`: 获取文件信息
- `delete_file`: 删除文件
- `read_file_content`: 读取文件内容
- `analyze_file`: 分析文件内容
""",
                metadata={
                    "type": "documentation",
                    "category": "help"
                }
            )
            await self.server.register_resource(help_resource)

            logger.info(f"内置资源注册完成: {len(self.server.resources)} 个资源")

        except Exception as e:
            logger.error(f"注册内置资源失败: {e}")
            raise
    
    async def create_session(self, user_id: str, conversation_id: str) -> str:
        """创建MCP会话"""
        return await self.server.create_context(user_id, conversation_id)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], context_id: Optional[str] = None) -> Dict[str, Any]:
        """调用工具"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="tools/call",
            params={
                "name": tool_name,
                "parameters": parameters
            },
            timestamp=datetime.now()
        )
        
        return await self.server.process_message(message, context_id)
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="tools/list",
            params={},
            timestamp=datetime.now()
        )
        
        response = await self.server.process_message(message)
        return response.get("result", {}).get("tools", [])
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """获取可用资源列表"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="resources/list",
            params={},
            timestamp=datetime.now()
        )
        
        response = await self.server.process_message(message)
        return response.get("result", {}).get("resources", [])


# 全局MCP服务实例
mcp_service = MCPService()
