"""
电商系统 Agent 工具集
基于 autogen HTTP 工具规范，为电商智能客服提供完整的API工具集
参考: https://microsoft.github.io/autogen/stable/reference/python/autogen_ext.tools.http.html
"""

from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from autogen_ext.tools.http import HttpTool


class EcommerceAgentTools:
    """电商系统 Agent 工具集"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/shop/api/v1"
        self._tools = []
        self._init_tools()
    
    def _init_tools(self):
        """初始化所有工具"""
        # 商品相关工具
        self._tools.extend(self._create_product_tools())
        # 订单相关工具
        self._tools.extend(self._create_order_tools())
        # 客户相关工具
        self._tools.extend(self._create_customer_tools())
        # 促销相关工具
        self._tools.extend(self._create_promotion_tools())
        # 购物车相关工具
        self._tools.extend(self._create_cart_tools())
    
    def _parse_url(self, url: str) -> dict:
        """解析URL为HttpTool需要的参数形式"""
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        host = parsed_url.netloc
        # 处理可能包含端口号的主机名
        if ':' in host:
            host, port_str = host.split(':', 1)
            port = int(port_str)
        else:
            # 默认端口
            port = 443 if scheme == 'https' else 80
        
        path = parsed_url.path or '/'
        
        return {
            "scheme": scheme,
            "host": host,
            "port": port,
            "path": path
        }
    
    def _create_product_tools(self) -> List[HttpTool]:
        """创建商品相关工具"""
        return [
            # 获取商品列表
            HttpTool(
                name="get_products",
                description="获取商品列表，支持分页、分类筛选、关键词搜索、推荐商品筛选",
                **self._parse_url(f"{self.api_base}/products/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "category_id": {"type": ["integer", "null"], "description": "分类ID，可选，只能是整数或不传，不能是空字符串"},
                        "keyword": {"type": "string", "description": "搜索关键词，可选"},
                        "is_featured": {"type": "boolean", "description": "是否推荐商品，可选"}
                    }
                }
            ),
            
            # 获取商品详情
            HttpTool(
                name="get_product_detail",
                description="根据商品ID获取商品详细信息，包括价格、库存、规格、评价等",
                **self._parse_url(f"{self.api_base}/products/{{product_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer", "description": "商品ID"},
                    },
                    "required": ["product_id"]
                }
            ),
            
            # 获取商品分类
            HttpTool(
                name="get_product_categories",
                description="获取所有商品分类列表",
                **self._parse_url(f"{self.api_base}/products/categories/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            
            # 搜索商品
            HttpTool(
                name="search_products",
                description="根据关键词搜索商品，支持分页",
                **self._parse_url(f"{self.api_base}/products/search/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "搜索关键词"},
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10}
                    },
                    "required": ["keyword"]
                }
            )
        ]
    
    def _create_order_tools(self) -> List[HttpTool]:
        """创建订单相关工具"""
        return [
            # 获取订单列表
            HttpTool(
                name="get_orders",
                description="获取订单列表，支持按客户ID和订单状态筛选",
                **self._parse_url(f"{self.api_base}/orders/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "customer_id": {"type": "integer", "description": "客户ID，可选"},
                        "status": {"type": "string", "description": "订单状态：pending(待付款)、paid(已付款)、shipped(已发货)、delivered(已送达)、cancelled(已取消)", "enum": ["pending", "paid", "shipped", "delivered", "cancelled"]}
                    }
                }
            ),
            
            # 获取订单详情
            HttpTool(
                name="get_order_detail",
                description="根据订单ID获取订单详细信息，包括商品明细、收货地址、物流信息等",
                **self._parse_url(f"{self.api_base}/orders/{{order_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "integer", "description": "订单ID"}
                    },
                    "required": ["order_id"]
                }
            ),
            
            # 根据订单号查询订单
            HttpTool(
                name="get_order_by_number",
                description="根据订单号查询订单信息，常用于客户查询订单状态",
                **self._parse_url(f"{self.api_base}/orders/number/{{order_number}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "order_number": {"type": "string", "description": "订单号，如ORD202401001"}
                    },
                    "required": ["order_number"]
                }
            )
        ]
    
    def _create_customer_tools(self) -> List[HttpTool]:
        """创建客户相关工具"""
        return [
            # 获取客户列表
            HttpTool(
                name="get_customers",
                description="获取客户列表，支持关键词搜索",
                **self._parse_url(f"{self.api_base}/customers/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "keyword": {"type": "string", "description": "搜索关键词，可选"}
                    }
                }
            ),
            
            # 获取客户详情
            HttpTool(
                name="get_customer_detail",
                description="根据客户ID获取客户详细信息，包括个人信息、地址、消费统计等",
                **self._parse_url(f"{self.api_base}/customers/{{customer_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "integer", "description": "客户ID"}
                    },
                    "required": ["customer_id"]
                }
            ),
            
            # 获取客户订单
            HttpTool(
                name="get_customer_orders",
                description="获取指定客户的订单列表",
                **self._parse_url(f"{self.api_base}/customers/{{customer_id}}/orders/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "integer", "description": "客户ID"},
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10}
                    },
                    "required": ["customer_id"]
                }
            )
        ]

    def _create_promotion_tools(self) -> List[HttpTool]:
        """创建促销相关工具"""
        return [
            # 获取促销活动列表
            HttpTool(
                name="get_promotions",
                description="获取促销活动列表，包括折扣、满减、免运费等活动",
                **self._parse_url(f"{self.api_base}/promotions/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "is_active": {"type": "boolean", "description": "是否启用，可选"}
                    }
                }
            ),

            # 获取促销活动详情
            HttpTool(
                name="get_promotion_detail",
                description="根据促销活动ID获取详细信息",
                **self._parse_url(f"{self.api_base}/promotions/{{promotion_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "promotion_id": {"type": "integer", "description": "促销活动ID"}
                    },
                    "required": ["promotion_id"]
                }
            ),

            # 获取优惠券列表
            HttpTool(
                name="get_coupons",
                description="获取优惠券列表，包括新用户券、满减券、折扣券等",
                **self._parse_url(f"{self.api_base}/promotions/coupons/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "is_active": {"type": "boolean", "description": "是否启用，可选"},
                        "code": {"type": "string", "description": "优惠券代码，可选"}
                    }
                }
            ),

            # 根据优惠券代码查询
            HttpTool(
                name="get_coupon_by_code",
                description="根据优惠券代码查询优惠券信息，用于验证优惠券有效性",
                **self._parse_url(f"{self.api_base}/promotions/coupons/{{coupon_code}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "coupon_code": {"type": "string", "description": "优惠券代码，如WELCOME10"}
                    },
                    "required": ["coupon_code"]
                }
            ),

            # 获取当前有效促销
            HttpTool(
                name="get_active_promotions",
                description="获取当前有效的促销活动和优惠券",
                **self._parse_url(f"{self.api_base}/promotions/active/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    def _create_cart_tools(self) -> List[HttpTool]:
        """创建购物车相关工具"""
        return [
            # 获取购物车列表
            HttpTool(
                name="get_carts",
                description="获取购物车列表，支持按客户ID筛选",
                **self._parse_url(f"{self.api_base}/cart/"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "页码，默认1", "default": 1},
                        "size": {"type": "integer", "description": "每页数量，默认10，最大100", "default": 10},
                        "customer_id": {"type": "integer", "description": "客户ID，可选"}
                    }
                }
            ),

            # 获取购物车详情
            HttpTool(
                name="get_cart_detail",
                description="根据购物车ID获取购物车详细信息，包括商品明细、总金额等",
                **self._parse_url(f"{self.api_base}/cart/{{cart_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "cart_id": {"type": "integer", "description": "购物车ID"}
                    },
                    "required": ["cart_id"]
                }
            ),

            # 获取客户购物车
            HttpTool(
                name="get_customer_cart",
                description="获取指定客户的购物车信息",
                **self._parse_url(f"{self.api_base}/cart/customer/{{customer_id}}"),
                method="GET",
                json_schema={
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "integer", "description": "客户ID"}
                    },
                    "required": ["customer_id"]
                }
            )
        ]

    def get_all_tools(self) -> List[HttpTool]:
        """获取所有工具"""
        return self._tools

    def get_tools_by_category(self, category: str) -> List[HttpTool]:
        """根据分类获取工具"""
        category_mapping = {
            "product": ["get_products", "get_product_detail", "get_product_categories", "search_products"],
            "order": ["get_orders", "get_order_detail", "get_order_by_number"],
            "customer": ["get_customers", "get_customer_detail", "get_customer_orders"],
            "promotion": ["get_promotions", "get_promotion_detail", "get_coupons", "get_coupon_by_code", "get_active_promotions"],
            "cart": ["get_carts", "get_cart_detail", "get_customer_cart"]
        }

        tool_names = category_mapping.get(category, [])
        return [tool for tool in self._tools if tool.name in tool_names]

    def get_tool_by_name(self, name: str) -> Optional[HttpTool]:
        """根据名称获取工具"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None

    def list_tools(self) -> Dict[str, Any]:
        """列出所有工具的信息"""
        tools_info = {}
        for tool in self._tools:
            tools_info[tool.name] = {
                "description": tool.description,
                "method": tool.method,
                "parameters": tool.json_schema if hasattr(tool, 'json_schema') else {}
            }
        return tools_info


# 便捷函数
def create_ecommerce_tools(base_url: str = "http://localhost:8001") -> List[HttpTool]:
    """创建电商工具集的便捷函数"""
    tools = EcommerceAgentTools(base_url)
    return tools.get_all_tools()


def get_ecommerce_tools_by_scenario(scenario: str, base_url: str = "http://localhost:8001") -> List[HttpTool]:
    """根据客服场景获取相关工具"""
    tools = EcommerceAgentTools(base_url)

    scenario_mapping = {
        "product_inquiry": tools.get_tools_by_category("product"),
        "order_tracking": tools.get_tools_by_category("order"),
        "customer_service": tools.get_tools_by_category("customer"),
        "promotion_inquiry": tools.get_tools_by_category("promotion"),
        "cart_management": tools.get_tools_by_category("cart"),
        "comprehensive": tools.get_all_tools()  # 综合场景使用所有工具
    }

    return scenario_mapping.get(scenario, tools.get_all_tools())
