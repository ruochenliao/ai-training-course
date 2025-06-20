"""
电商工具集
基于MCP协议的电商业务工具实现
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime, timedelta

from loguru import logger
from app.services.mcp_service import MCPTool, MCPContext


class EcommerceTools:
    """电商工具集"""
    
    def __init__(self, shop_base_url: str = "http://localhost:8001"):
        """初始化电商工具"""
        self.shop_base_url = shop_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_tools(self) -> List[MCPTool]:
        """获取所有电商工具"""
        return [
            MCPTool(
                name="search_products",
                description="搜索商品信息，支持按名称、分类、价格范围等条件搜索",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "category": {
                            "type": "string",
                            "description": "商品分类"
                        },
                        "min_price": {
                            "type": "number",
                            "description": "最低价格"
                        },
                        "max_price": {
                            "type": "number",
                            "description": "最高价格"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制",
                            "default": 10
                        }
                    },
                    "required": []
                },
                handler=self.search_products,
                category="ecommerce"
            ),
            
            MCPTool(
                name="get_product_details",
                description="获取商品详细信息，包括价格、库存、描述等",
                parameters={
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "商品ID"
                        }
                    },
                    "required": ["product_id"]
                },
                handler=self.get_product_details,
                category="ecommerce"
            ),
            
            MCPTool(
                name="check_order_status",
                description="查询订单状态和物流信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "订单号"
                        }
                    },
                    "required": ["order_id"]
                },
                handler=self.check_order_status,
                category="ecommerce"
            ),
            
            MCPTool(
                name="get_customer_orders",
                description="获取客户的订单历史",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "integer",
                            "description": "客户ID"
                        },
                        "status": {
                            "type": "string",
                            "description": "订单状态过滤"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制",
                            "default": 10
                        }
                    },
                    "required": ["customer_id"]
                },
                handler=self.get_customer_orders,
                category="ecommerce"
            ),
            
            MCPTool(
                name="get_promotions",
                description="获取当前有效的促销活动信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "active_only": {
                            "type": "boolean",
                            "description": "是否只返回活跃的促销",
                            "default": True
                        }
                    },
                    "required": []
                },
                handler=self.get_promotions,
                category="ecommerce"
            ),
            
            MCPTool(
                name="check_coupon_validity",
                description="检查优惠券的有效性和使用条件",
                parameters={
                    "type": "object",
                    "properties": {
                        "coupon_code": {
                            "type": "string",
                            "description": "优惠券代码"
                        },
                        "customer_id": {
                            "type": "integer",
                            "description": "客户ID"
                        }
                    },
                    "required": ["coupon_code"]
                },
                handler=self.check_coupon_validity,
                category="ecommerce"
            ),
            
            MCPTool(
                name="get_cart_items",
                description="获取购物车中的商品信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "integer",
                            "description": "客户ID"
                        }
                    },
                    "required": ["customer_id"]
                },
                handler=self.get_cart_items,
                category="ecommerce"
            ),
            
            MCPTool(
                name="calculate_shipping",
                description="计算配送费用和预计送达时间",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "integer",
                            "description": "客户ID"
                        },
                        "items": {
                            "type": "array",
                            "description": "商品列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "integer"},
                                    "quantity": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "required": ["customer_id", "items"]
                },
                handler=self.calculate_shipping,
                category="ecommerce"
            )
        ]
    
    async def search_products(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """搜索商品"""
        try:
            query_params = {}
            
            if "query" in params:
                query_params["search"] = params["query"]
            if "category" in params:
                query_params["category"] = params["category"]
            if "min_price" in params:
                query_params["min_price"] = params["min_price"]
            if "max_price" in params:
                query_params["max_price"] = params["max_price"]
            if "limit" in params:
                query_params["limit"] = params["limit"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/products",
                params=query_params
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "products": data.get("products", []),
                "total": data.get("total", 0),
                "search_params": query_params
            }
            
        except Exception as e:
            logger.error(f"搜索商品失败: {e}")
            return {"error": str(e), "products": []}
    
    async def get_product_details(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取商品详情"""
        try:
            product_id = params["product_id"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/products/{product_id}"
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取商品详情失败: {e}")
            return {"error": str(e)}
    
    async def check_order_status(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            order_id = params["order_id"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/orders/{order_id}"
            )
            response.raise_for_status()
            
            order_data = response.json()
            
            # 添加物流信息模拟
            if order_data.get("status") == "shipped":
                order_data["tracking"] = {
                    "tracking_number": f"SF{order_id}001",
                    "carrier": "顺丰快递",
                    "estimated_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
                    "current_location": "配送中心"
                }
            
            return order_data
            
        except Exception as e:
            logger.error(f"查询订单状态失败: {e}")
            return {"error": str(e)}
    
    async def get_customer_orders(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取客户订单"""
        try:
            customer_id = params["customer_id"]
            query_params = {"customer_id": customer_id}
            
            if "status" in params:
                query_params["status"] = params["status"]
            if "limit" in params:
                query_params["limit"] = params["limit"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/orders",
                params=query_params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取客户订单失败: {e}")
            return {"error": str(e), "orders": []}
    
    async def get_promotions(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取促销活动"""
        try:
            query_params = {}
            if "active_only" in params:
                query_params["active_only"] = params["active_only"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/promotions",
                params=query_params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取促销活动失败: {e}")
            return {"error": str(e), "promotions": []}
    
    async def check_coupon_validity(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """检查优惠券有效性"""
        try:
            coupon_code = params["coupon_code"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/coupons/{coupon_code}"
            )
            response.raise_for_status()
            
            coupon_data = response.json()
            
            # 检查有效性
            now = datetime.now()
            valid_from = datetime.fromisoformat(coupon_data.get("valid_from", now.isoformat()))
            valid_until = datetime.fromisoformat(coupon_data.get("valid_until", now.isoformat()))
            
            is_valid = valid_from <= now <= valid_until and coupon_data.get("is_active", False)
            
            return {
                **coupon_data,
                "is_currently_valid": is_valid,
                "validation_message": "优惠券有效" if is_valid else "优惠券无效或已过期"
            }
            
        except Exception as e:
            logger.error(f"检查优惠券有效性失败: {e}")
            return {"error": str(e), "is_currently_valid": False}
    
    async def get_cart_items(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """获取购物车商品"""
        try:
            customer_id = params["customer_id"]
            
            response = await self.client.get(
                f"{self.shop_base_url}/api/v1/cart/{customer_id}"
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取购物车商品失败: {e}")
            return {"error": str(e), "items": []}
    
    async def calculate_shipping(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """计算配送费用"""
        try:
            customer_id = params["customer_id"]
            items = params["items"]
            
            # 获取客户信息
            customer_response = await self.client.get(
                f"{self.shop_base_url}/api/v1/customers/{customer_id}"
            )
            customer_response.raise_for_status()
            customer_data = customer_response.json()
            
            # 简单的配送费计算逻辑
            total_weight = 0
            total_value = 0
            
            for item in items:
                product_response = await self.client.get(
                    f"{self.shop_base_url}/api/v1/products/{item['product_id']}"
                )
                if product_response.status_code == 200:
                    product = product_response.json()
                    total_weight += product.get("weight", 0.5) * item["quantity"]
                    total_value += product.get("price", 0) * item["quantity"]
            
            # 配送费计算
            base_fee = 10.0  # 基础配送费
            weight_fee = max(0, (total_weight - 1.0) * 5.0)  # 超重费
            
            # 免邮条件
            if total_value >= 99:
                shipping_fee = 0
                free_shipping = True
            else:
                shipping_fee = base_fee + weight_fee
                free_shipping = False
            
            # 预计送达时间
            estimated_delivery = datetime.now() + timedelta(days=3)
            
            return {
                "shipping_fee": shipping_fee,
                "free_shipping": free_shipping,
                "total_weight": total_weight,
                "total_value": total_value,
                "estimated_delivery": estimated_delivery.isoformat(),
                "delivery_options": [
                    {
                        "name": "标准配送",
                        "fee": shipping_fee,
                        "days": 3,
                        "description": "3个工作日内送达"
                    },
                    {
                        "name": "快速配送",
                        "fee": shipping_fee + 15,
                        "days": 1,
                        "description": "次日送达"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"计算配送费用失败: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局电商工具实例
ecommerce_tools = EcommerceTools()
