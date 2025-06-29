# 电商系统 Agent 工具集

基于 [autogen HTTP 工具规范](https://microsoft.github.io/autogen/stable//reference/python/autogen_ext.tools.http.html) 构建的电商系统 Agent 工具集，为智能客服提供完整的API工具支持。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install autogen-ext[http]
```

### 2. 启动电商系统

```bash
cd shop
python run.py
```

### 3. 使用工具

```python
from agent_tools import create_ecommerce_tools

# 创建所有电商工具
tools = create_ecommerce_tools(base_url="http://localhost:8001")

# 在 autogen 中使用
from autogen import ConversableAgent

agent = ConversableAgent(
    name="CustomerServiceAgent",
    tools=tools,
    # ... 其他配置
)
```

## 🛠️ 工具分类

### 📦 商品相关工具 (4个)

| 工具名称 | 描述 | 主要用途 |
|---------|------|----------|
| `get_products` | 获取商品列表 | 商品浏览、分类筛选 |
| `get_product_detail` | 获取商品详情 | 查看具体商品信息 |
| `get_product_categories` | 获取商品分类 | 分类导航 |
| `search_products` | 搜索商品 | 关键词搜索 |

### 📋 订单相关工具 (3个)

| 工具名称 | 描述 | 主要用途 |
|---------|------|----------|
| `get_orders` | 获取订单列表 | 订单管理、筛选 |
| `get_order_detail` | 获取订单详情 | 查看订单详细信息 |
| `get_order_by_number` | 根据订单号查询 | 客户订单查询 |

### 👥 客户相关工具 (3个)

| 工具名称 | 描述 | 主要用途 |
|---------|------|----------|
| `get_customers` | 获取客户列表 | 客户管理 |
| `get_customer_detail` | 获取客户详情 | 查看客户信息 |
| `get_customer_orders` | 获取客户订单 | 客户订单历史 |

### 🎉 促销相关工具 (5个)

| 工具名称 | 描述 | 主要用途 |
|---------|------|----------|
| `get_promotions` | 获取促销活动 | 活动查询 |
| `get_promotion_detail` | 获取促销详情 | 活动详细信息 |
| `get_coupons` | 获取优惠券列表 | 优惠券管理 |
| `get_coupon_by_code` | 根据代码查询优惠券 | 优惠券验证 |
| `get_active_promotions` | 获取有效促销 | 当前可用优惠 |

### 🛒 购物车相关工具 (3个)

| 工具名称 | 描述 | 主要用途 |
|---------|------|----------|
| `get_carts` | 获取购物车列表 | 购物车管理 |
| `get_cart_detail` | 获取购物车详情 | 购物车详细信息 |
| `get_customer_cart` | 获取客户购物车 | 客户购物车查询 |

## 🎯 场景化使用

### 根据客服场景选择工具

```python
from agent_tools import get_ecommerce_tools_by_scenario

# 产品咨询场景
product_tools = get_ecommerce_tools_by_scenario("product_inquiry")

# 订单追踪场景
order_tools = get_ecommerce_tools_by_scenario("order_tracking")

# 促销咨询场景
promotion_tools = get_ecommerce_tools_by_scenario("promotion_inquiry")

# 综合客服场景
all_tools = get_ecommerce_tools_by_scenario("comprehensive")
```

### 支持的场景类型

- `product_inquiry`: 产品咨询 (商品相关工具)
- `order_tracking`: 订单追踪 (订单相关工具)
- `customer_service`: 客户服务 (客户相关工具)
- `promotion_inquiry`: 促销咨询 (促销相关工具)
- `cart_management`: 购物车管理 (购物车相关工具)
- `comprehensive`: 综合场景 (所有工具)

## 💬 客服对话示例

### 场景1: 商品咨询

**用户**: "我想买一个手机，有什么推荐的吗？"

**Agent 工作流程**:
1. 使用 `search_products(keyword="手机")` 搜索手机
2. 使用 `get_products(is_featured=true)` 获取推荐商品
3. 使用 `get_product_detail(product_id=1)` 获取具体商品详情

### 场景2: 订单查询

**用户**: "我的订单ORD202401001现在什么状态？"

**Agent 工作流程**:
1. 使用 `get_order_by_number(order_number="ORD202401001")` 查询订单
2. 返回订单状态、物流信息、预计送达时间

### 场景3: 优惠券验证

**用户**: "我有一个优惠券WELCOME10，能用吗？"

**Agent 工作流程**:
1. 使用 `get_coupon_by_code(coupon_code="WELCOME10")` 查询优惠券
2. 检查优惠券有效性、使用条件、折扣金额

## 🔧 高级用法

### 自定义工具集

```python
from agent_tools import EcommerceAgentTools

# 创建工具集实例
tools = EcommerceAgentTools(base_url="http://localhost:8001")

# 按分类获取工具
product_tools = tools.get_tools_by_category("product")
order_tools = tools.get_tools_by_category("order")

# 获取特定工具
search_tool = tools.get_tool_by_name("search_products")

# 列出所有工具信息
tools_info = tools.list_tools()
```

### 工具参数说明

每个工具都支持标准的HTTP参数：

- **分页参数**: `page` (页码), `size` (每页数量)
- **筛选参数**: `category_id`, `customer_id`, `status` 等
- **搜索参数**: `keyword` (关键词搜索)
- **状态参数**: `is_active`, `is_featured` 等

## 📝 完整示例

```python
from autogen import ConversableAgent
from agent_tools import create_ecommerce_tools

# 创建电商工具
tools = create_ecommerce_tools()

# 创建客服 Agent
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
    tools=tools,
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
```

## 🚨 注意事项

1. **服务依赖**: 确保电商系统已启动 (`python shop/run.py`)
2. **网络连接**: 工具需要访问电商系统API (默认: http://localhost:8001)
3. **数据格式**: 所有API返回标准JSON格式数据
4. **错误处理**: 工具会自动处理HTTP错误和数据验证

## 📚 相关文档

- [电商系统README](README.md)
- [API接口文档](http://localhost:8001/shop/docs)
- [Autogen HTTP工具文档](https://microsoft.github.io/autogen/stable//reference/python/autogen_ext.tools.http.html)
- [客服提示词系统](app/customer_service/ecommerce_prompts.py)

## 🔄 更新日志

- **v1.0.0**: 初始版本，包含18个核心工具
- 支持商品、订单、客户、促销、购物车全场景
- 基于autogen HTTP工具规范构建
- 提供场景化工具选择功能

## API 工具使用注意事项

### 参数类型约束

在使用电商系统API工具时，需要特别注意参数类型的正确使用：

1. **整数类型参数**：如`page`、`size`、`category_id`、`product_id`等
   - 必须传递整数值或null/None
   - 不能传递空字符串`""`
   - 例如：`category_id=1`或完全不传递该参数，而不是`category_id=""`

2. **布尔类型参数**：如`is_featured`、`is_active`等
   - 必须传递`true`或`false`
   - 不能传递字符串形式的"true"或"false"

3. **可选参数**：
   - 当不需要使用某个可选参数时，应完全省略该参数
   - 不要传递空字符串或null值

### 常见错误处理

- **422 Unprocessable Entity**：通常是参数类型不匹配导致，例如:
  - 为整数类型参数传递了空字符串
  - 为布尔类型参数传递了字符串形式的值

## 示例

### 正确的请求：

```
/shop/api/v1/products/?page=1&size=10&keyword=手机&is_featured=true
```

### 错误的请求：

```
/shop/api/v1/products/?page=1&size=10&category_id=&keyword=手机&is_featured=true
```

在上面的错误示例中，`category_id=`传递了空字符串而不是整数，这会导致422错误。

## 工具详细说明
