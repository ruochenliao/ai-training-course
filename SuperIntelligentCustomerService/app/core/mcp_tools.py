# -*- coding: utf-8 -*-
"""
MCP工具定义模块
为SuperIntelligentCustomerService系统定义MCP工具
"""
from typing import List, Dict, Any, Optional

import httpx
from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    """MCP工具基类"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        raise NotImplementedError


class ShopAPITool(MCPTool):
    """电商API工具基类"""
    shop_base_url: str = "http://localhost:8002"  # shop服务地址
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发起HTTP请求到shop服务"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.shop_base_url}{endpoint}",
                    params=params or {},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}


class GetProductsTool(ShopAPITool):
    """获取商品列表工具"""
    
    def __init__(self):
        super().__init__(
            name="get_products",
            description="查询商品列表，支持分页、分类筛选、关键词搜索等功能"
        )
    
    async def execute(self, 
                     page: int = 1, 
                     size: int = 10, 
                     category_id: Optional[int] = None,
                     keyword: Optional[str] = None,
                     is_featured: Optional[bool] = None) -> Dict[str, Any]:
        """
        执行商品查询
        
        Args:
            page: 页码，默认1
            size: 每页数量，默认10
            category_id: 分类ID，可选
            keyword: 搜索关键词，可选
            is_featured: 是否推荐商品，可选
        """
        params = {
            "page": page,
            "size": size
        }
        
        if category_id is not None:
            params["category_id"] = category_id
        if keyword:
            params["keyword"] = keyword
        if is_featured is not None:
            params["is_featured"] = is_featured
        
        result = await self._make_request("/shop/api/v1/products/", params)
        
        # 格式化返回结果
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {result.get('total', 0)} 个商品"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "获取商品列表失败"
            }


class GetOrdersTool(ShopAPITool):
    """获取订单列表工具"""
    
    def __init__(self):
        super().__init__(
            name="get_orders",
            description="查询订单列表，支持按客户ID、订单状态等条件筛选"
        )
    
    async def execute(self,
                     page: int = 1,
                     size: int = 10,
                     customer_id: Optional[int] = None,
                     status: Optional[str] = None) -> Dict[str, Any]:
        """
        执行订单查询
        
        Args:
            page: 页码，默认1
            size: 每页数量，默认10
            customer_id: 客户ID，可选
            status: 订单状态，可选
        """
        params = {
            "page": page,
            "size": size
        }
        
        if customer_id is not None:
            params["customer_id"] = customer_id
        if status:
            params["status"] = status
        
        result = await self._make_request("/shop/api/v1/orders/", params)
        
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {result.get('total', 0)} 个订单"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "获取订单列表失败"
            }


class GetCustomersTool(ShopAPITool):
    """获取客户列表工具"""
    
    def __init__(self):
        super().__init__(
            name="get_customers",
            description="查询客户列表，支持关键词搜索客户信息"
        )
    
    async def execute(self,
                     page: int = 1,
                     size: int = 10,
                     keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        执行客户查询
        
        Args:
            page: 页码，默认1
            size: 每页数量，默认10
            keyword: 搜索关键词，可选
        """
        params = {
            "page": page,
            "size": size
        }
        
        if keyword:
            params["keyword"] = keyword
        
        result = await self._make_request("/shop/api/v1/customers/", params)
        
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {result.get('total', 0)} 个客户"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "获取客户列表失败"
            }


class GetPromotionsTool(ShopAPITool):
    """获取促销活动工具"""
    
    def __init__(self):
        super().__init__(
            name="get_promotions",
            description="查询促销活动列表，支持按活动状态筛选"
        )
    
    async def execute(self,
                     page: int = 1,
                     size: int = 10,
                     is_active: Optional[bool] = None) -> Dict[str, Any]:
        """
        执行促销活动查询
        
        Args:
            page: 页码，默认1
            size: 每页数量，默认10
            is_active: 是否启用，可选
        """
        params = {
            "page": page,
            "size": size
        }
        
        if is_active is not None:
            params["is_active"] = is_active
        
        result = await self._make_request("/shop/api/v1/promotions/", params)
        
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {result.get('total', 0)} 个促销活动"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "获取促销活动失败"
            }


class GetCartsTool(ShopAPITool):
    """获取购物车工具"""
    
    def __init__(self):
        super().__init__(
            name="get_carts",
            description="查询购物车列表，支持按客户ID筛选"
        )
    
    async def execute(self,
                     page: int = 1,
                     size: int = 10,
                     customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行购物车查询
        
        Args:
            page: 页码，默认1
            size: 每页数量，默认10
            customer_id: 客户ID，可选
        """
        params = {
            "page": page,
            "size": size
        }
        
        if customer_id is not None:
            params["customer_id"] = customer_id
        
        result = await self._make_request("/shop/api/v1/cart/", params)
        
        if "error" not in result:
            return {
                "success": True,
                "data": result,
                "message": f"成功获取 {result.get('total', 0)} 个购物车"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "获取购物车失败"
            }


# 工具注册表
MCP_TOOLS_REGISTRY = {
    "get_products": GetProductsTool(),
    "get_orders": GetOrdersTool(),
    "get_customers": GetCustomersTool(),
    "get_promotions": GetPromotionsTool(),
    "get_carts": GetCartsTool(),
}


def get_mcp_tool(tool_name: str) -> Optional[MCPTool]:
    """获取MCP工具实例"""
    return MCP_TOOLS_REGISTRY.get(tool_name)


def list_mcp_tools() -> List[Dict[str, str]]:
    """列出所有可用的MCP工具"""
    return [
        {
            "name": tool.name,
            "description": tool.description
        }
        for tool in MCP_TOOLS_REGISTRY.values()
    ]


async def execute_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """执行MCP工具"""
    tool = get_mcp_tool(tool_name)
    if not tool:
        return {
            "success": False,
            "error": f"未找到工具: {tool_name}",
            "available_tools": list(MCP_TOOLS_REGISTRY.keys())
        }
    
    try:
        result = await tool.execute(**kwargs)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"工具执行失败: {str(e)}",
            "tool_name": tool_name
        }
