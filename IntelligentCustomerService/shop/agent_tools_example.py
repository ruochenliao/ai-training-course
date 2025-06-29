"""
电商系统 Agent 工具使用示例
展示如何在 autogen 中使用电商系统的 HTTP 工具
"""

import asyncio

from app.core.agent_tools import EcommerceAgentTools, get_ecommerce_tools_by_scenario


async def basic_usage_example():
    """基础使用示例"""
    print("=" * 60)
    print("🛍️ 电商系统 Agent 工具基础使用示例")
    print("=" * 60)
    
    # 创建工具集
    tools = EcommerceAgentTools()
    
    # 获取所有工具
    all_tools = tools.get_all_tools()
    print(f"📦 总共有 {len(all_tools)} 个工具可用")
    
    # 按分类获取工具
    product_tools = tools.get_tools_by_category("product")
    print(f"🛒 商品相关工具: {len(product_tools)} 个")
    for tool in product_tools:
        print(f"  • {tool.name}: {tool.description}")
    
    order_tools = tools.get_tools_by_category("order")
    print(f"📋 订单相关工具: {len(order_tools)} 个")
    for tool in order_tools:
        print(f"  • {tool.name}: {tool.description}")
    
    promotion_tools = tools.get_tools_by_category("promotion")
    print(f"🎉 促销相关工具: {len(promotion_tools)} 个")
    for tool in promotion_tools:
        print(f"  • {tool.name}: {tool.description}")


def scenario_based_example():
    """基于场景的工具选择示例"""
    print("\n" + "=" * 60)
    print("🎯 基于客服场景的工具选择示例")
    print("=" * 60)
    
    scenarios = {
        "product_inquiry": "产品咨询场景",
        "order_tracking": "订单追踪场景", 
        "customer_service": "客户服务场景",
        "promotion_inquiry": "促销咨询场景",
        "cart_management": "购物车管理场景",
        "comprehensive": "综合客服场景"
    }
    
    for scenario, description in scenarios.items():
        tools = get_ecommerce_tools_by_scenario(scenario)
        print(f"\n📌 {description} ({scenario})")
        print(f"   可用工具: {len(tools)} 个")
        for tool in tools:
            print(f"   • {tool.name}")


def autogen_integration_example():
    """autogen 集成示例"""
    print("\n" + "=" * 60)
    print("🤖 Autogen 集成示例代码")
    print("=" * 60)
    
    example_code = '''
# 在 autogen 中使用电商工具的示例代码

from autogen import ConversableAgent
from agent_tools import create_ecommerce_tools, get_ecommerce_tools_by_scenario

# 方式1: 使用所有工具
all_tools = create_ecommerce_tools(base_url="http://localhost:8001")

# 方式2: 根据场景选择工具
product_tools = get_ecommerce_tools_by_scenario("product_inquiry")
order_tools = get_ecommerce_tools_by_scenario("order_tracking")

# 创建智能客服 Agent
customer_service_agent = ConversableAgent(
    name="CustomerServiceAgent",
    system_message="""
    你是一个专业的电商客服助手。你可以：
    1. 查询商品信息、价格、库存
    2. 查询订单状态、物流信息
    3. 查询客户信息和订单历史
    4. 查询促销活动和优惠券
    5. 查询购物车信息
    
    请根据用户的问题，使用合适的工具来获取信息并提供帮助。
    """,
    llm_config={
        "model": "deepseek-chat",
        "api_key": "your-api-key",
        "base_url": "https://api.deepseek.com"
    },
    tools=all_tools,  # 注册所有电商工具
    human_input_mode="NEVER"
)

# 创建用户 Agent
user_agent = ConversableAgent(
    name="User",
    llm_config=False,
    human_input_mode="ALWAYS"
)

# 开始对话
user_agent.initiate_chat(
    customer_service_agent,
    message="你好，我想查询一下iPhone 15 Pro的价格和库存情况"
)
'''
    
    print(example_code)


def tool_details_example():
    """工具详情示例"""
    print("\n" + "=" * 60)
    print("🔧 工具详情示例")
    print("=" * 60)
    
    tools = EcommerceAgentTools()
    
    # 展示几个重要工具的详情
    important_tools = [
        "search_products",
        "get_order_by_number", 
        "get_coupon_by_code",
        "get_customer_cart"
    ]
    
    for tool_name in important_tools:
        tool = tools.get_tool_by_name(tool_name)
        if tool:
            print(f"\n🛠️ {tool.name}")
            print(f"   描述: {tool.description}")
            print(f"   URL: {tool.url}")
            print(f"   方法: {tool.method}")
            if hasattr(tool, 'parameters') and tool.parameters:
                print("   参数:")
                for param_name, param_info in tool.parameters.items():
                    required = " (必需)" if param_info.get("required") else " (可选)"
                    default = f" [默认: {param_info.get('default')}]" if param_info.get("default") is not None else ""
                    print(f"     • {param_name}: {param_info.get('description', '')}{required}{default}")


def customer_service_scenarios():
    """客服场景示例"""
    print("\n" + "=" * 60)
    print("💬 客服场景对话示例")
    print("=" * 60)
    
    scenarios = [
        {
            "scenario": "商品咨询",
            "user_query": "我想买一个手机，有什么推荐的吗？",
            "tools_needed": ["search_products", "get_products", "get_product_detail"],
            "workflow": [
                "1. 使用 search_products 搜索 '手机' 关键词",
                "2. 使用 get_products 获取推荐商品列表 (is_featured=true)",
                "3. 使用 get_product_detail 获取具体商品详情"
            ]
        },
        {
            "scenario": "订单查询",
            "user_query": "我的订单ORD202401001现在什么状态？",
            "tools_needed": ["get_order_by_number"],
            "workflow": [
                "1. 使用 get_order_by_number 查询订单号 'ORD202401001'",
                "2. 返回订单状态、物流信息、预计送达时间"
            ]
        },
        {
            "scenario": "优惠券查询",
            "user_query": "我有一个优惠券WELCOME10，能用吗？",
            "tools_needed": ["get_coupon_by_code"],
            "workflow": [
                "1. 使用 get_coupon_by_code 查询优惠券 'WELCOME10'",
                "2. 检查优惠券是否有效、使用条件、折扣金额"
            ]
        },
        {
            "scenario": "购物车查询",
            "user_query": "帮我看看购物车里有什么？",
            "tools_needed": ["get_customer_cart"],
            "workflow": [
                "1. 使用 get_customer_cart 获取客户购物车",
                "2. 显示购物车商品、数量、总金额"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📝 场景 {i}: {scenario['scenario']}")
        print(f"   用户问题: \"{scenario['user_query']}\"")
        print(f"   需要的工具: {', '.join(scenario['tools_needed'])}")
        print("   处理流程:")
        for step in scenario['workflow']:
            print(f"     {step}")


def main():
    """主函数"""
    print("🚀 启动电商系统 Agent 工具示例...")
    
    # 基础使用示例
    asyncio.run(basic_usage_example())
    
    # 场景选择示例
    scenario_based_example()
    
    # 工具详情示例
    tool_details_example()
    
    # autogen 集成示例
    autogen_integration_example()
    
    # 客服场景示例
    customer_service_scenarios()
    
    print("\n" + "=" * 60)
    print("✅ 示例演示完成！")
    print("💡 提示: 确保电商系统已启动 (python shop/run.py)")
    print("📖 更多信息请查看: shop/README.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
