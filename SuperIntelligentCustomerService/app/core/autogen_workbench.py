# -*- coding: utf-8 -*-
"""
AutoGen Workbench集成模块
集成MCP工具到AutoGen AgentChat系统
"""
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from autogen_core.tools import FunctionTool
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_core.model_context import BufferedChatCompletionContext

from app.core.mcp_tools import MCP_TOOLS_REGISTRY, execute_mcp_tool
from app.core.llms import get_model_client


class MCPToolWrapper:
    """MCP工具包装器，将MCP工具转换为AutoGen FunctionTool"""

    def __init__(self, tool_name: str, mcp_tool):
        self.tool_name = tool_name
        self.mcp_tool = mcp_tool
        self.autogen_tool = self._create_function_tool()

    def _create_function_tool(self) -> FunctionTool:
        """创建AutoGen FunctionTool"""
        # 根据工具类型创建不同的函数
        if self.tool_name == "get_products":
            async def get_products_func(
                page: int = 1,
                size: int = 10,
                category_id: Optional[int] = None,
                keyword: Optional[str] = None,
                is_featured: Optional[bool] = None
            ) -> str:
                """查询商品列表，支持分页、分类筛选、关键词搜索等功能"""
                kwargs = {"page": page, "size": size}
                if category_id is not None:
                    kwargs["category_id"] = category_id
                if keyword is not None:
                    kwargs["keyword"] = keyword
                if is_featured is not None:
                    kwargs["is_featured"] = is_featured

                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(get_products_func, description=self.mcp_tool.description)

        elif self.tool_name == "get_orders":
            async def get_orders_func(
                page: int = 1,
                size: int = 10,
                customer_id: Optional[int] = None,
                status: Optional[str] = None
            ) -> str:
                """查询订单列表，支持按客户ID、订单状态等条件筛选"""
                kwargs = {"page": page, "size": size}
                if customer_id is not None:
                    kwargs["customer_id"] = customer_id
                if status is not None:
                    kwargs["status"] = status

                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(get_orders_func, description=self.mcp_tool.description)

        elif self.tool_name == "get_customers":
            async def get_customers_func(
                page: int = 1,
                size: int = 10,
                keyword: Optional[str] = None
            ) -> str:
                """查询客户列表，支持关键词搜索客户信息"""
                kwargs = {"page": page, "size": size}
                if keyword is not None:
                    kwargs["keyword"] = keyword

                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(get_customers_func, description=self.mcp_tool.description)

        elif self.tool_name == "get_promotions":
            async def get_promotions_func(
                page: int = 1,
                size: int = 10,
                is_active: Optional[bool] = None
            ) -> str:
                """查询促销活动列表，支持按活动状态筛选"""
                kwargs = {"page": page, "size": size}
                if is_active is not None:
                    kwargs["is_active"] = is_active

                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(get_promotions_func, description=self.mcp_tool.description)

        elif self.tool_name == "get_carts":
            async def get_carts_func(
                page: int = 1,
                size: int = 10,
                customer_id: Optional[int] = None
            ) -> str:
                """查询购物车列表，支持按客户ID筛选"""
                kwargs = {"page": page, "size": size}
                if customer_id is not None:
                    kwargs["customer_id"] = customer_id

                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(get_carts_func, description=self.mcp_tool.description)

        else:
            # 通用工具函数
            async def generic_tool_func(**kwargs) -> str:
                """通用MCP工具执行函数"""
                result = await execute_mcp_tool(self.tool_name, **kwargs)
                return json.dumps(result, ensure_ascii=False, indent=2)

            return FunctionTool(generic_tool_func, description=self.mcp_tool.description)

    def get_tool(self) -> FunctionTool:
        """获取AutoGen FunctionTool"""
        return self.autogen_tool


class MCPEnabledAssistantAgent:
    """支持MCP的助手代理"""
    
    def __init__(self, 
                 model_client,
                 system_message: str,
                 tools: Optional[List[str]] = None,
                 buffer_size: int = 1):
        """
        初始化MCP助手代理
        
        Args:
            model_client: 模型客户端
            system_message: 系统消息
            tools: 要启用的工具列表，None表示启用所有工具
            buffer_size: 缓冲区大小
        """
        self.model_client = model_client
        self.system_message = system_message
        self.buffer_size = buffer_size
        
        # 准备工具
        self.tools = self._prepare_tools(tools)
        
        # 创建AssistantAgent
        self.agent = self._create_agent()
    
    def _prepare_tools(self, tool_names: Optional[List[str]] = None) -> List[FunctionTool]:
        """准备工具列表"""
        tools = []
        
        # 如果没有指定工具，使用所有可用工具
        if tool_names is None:
            tool_names = list(MCP_TOOLS_REGISTRY.keys())
        
        for tool_name in tool_names:
            if tool_name in MCP_TOOLS_REGISTRY:
                mcp_tool = MCP_TOOLS_REGISTRY[tool_name]
                wrapper = MCPToolWrapper(tool_name, mcp_tool)
                tools.append(wrapper.get_tool())
        
        return tools
    
    def _create_agent(self) -> AssistantAgent:
        """创建AssistantAgent"""
        return AssistantAgent(
            name="mcp_assistant",
            model_client=self.model_client,
            system_message=self.system_message,
            tools=self.tools,
            model_context=BufferedChatCompletionContext(buffer_size=self.buffer_size)
        )
    
    async def run_stream(self, task: str):
        """流式运行任务"""
        async for event in self.agent.run_stream(task=task):
            yield event
    
    async def run(self, task: str) -> TaskResult:
        """运行任务"""
        return await self.agent.run(task=task)


class MCPWorkbench:
    """MCP工作台，管理MCP工具和代理"""
    
    def __init__(self):
        self.tools = MCP_TOOLS_REGISTRY
        self.agents = {}
    
    async def create_agent(self,
                          agent_name: str,
                          model_name: str = "deepseek-chat",
                          system_message: Optional[str] = None,
                          tools: Optional[List[str]] = None,
                          buffer_size: int = 1) -> MCPEnabledAssistantAgent:
        """
        创建MCP助手代理
        
        Args:
            agent_name: 代理名称
            model_name: 模型名称
            system_message: 系统消息
            tools: 工具列表
            buffer_size: 缓冲区大小
        """
        # 获取模型客户端
        model_client = await get_model_client(model_name)
        
        # 默认系统消息
        if system_message is None:
            system_message = """你是一个专业的智能客服助手，具备访问电商系统数据的能力。

你可以使用以下工具来帮助用户：
- get_products: 查询商品信息
- get_orders: 查询订单状态
- get_customers: 查询客户信息
- get_promotions: 查询促销活动
- get_carts: 查询购物车信息

请根据用户的问题，选择合适的工具来获取信息，并以友好、专业的方式回答用户的问题。
始终用中文回复用户。"""
        
        # 创建代理
        agent = MCPEnabledAssistantAgent(
            model_client=model_client,
            system_message=system_message,
            tools=tools,
            buffer_size=buffer_size
        )
        
        # 保存代理
        self.agents[agent_name] = agent
        
        return agent
    
    def get_agent(self, agent_name: str) -> Optional[MCPEnabledAssistantAgent]:
        """获取代理"""
        return self.agents.get(agent_name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
    
    def list_agents(self) -> List[str]:
        """列出所有代理"""
        return list(self.agents.keys())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """直接执行工具"""
        return await execute_mcp_tool(tool_name, **kwargs)


# 全局工作台实例
mcp_workbench = MCPWorkbench()
