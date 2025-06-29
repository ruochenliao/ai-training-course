# 智能电商系统

基于 FastAPI + Tortoise ORM 构建的现代电商平台，专为智能客服场景设计。

## 功能特性

### 🛍️ 电商核心功能
- **商品管理**: 商品分类、商品信息、库存管理
- **购物车**: 添加商品、数量管理、库存验证
- **订单管理**: 订单创建、状态跟踪、物流信息
- **客户管理**: 客户信息、地址管理
- **促销系统**: 促销活动、优惠券管理

### 🤖 智能客服
- **专业提示词系统**: 针对电商场景优化的客服提示词
- **多场景支持**: 产品咨询、订单查询、售后服务等
- **标准化回复**: 预设的回复模板和FAQ

### 📊 数据初始化
- 自动创建测试数据
- 每个类型精确10条初始化数据
- 包含商品、订单、客户、促销等完整数据

## 快速开始

### 1. 安装依赖

```bash
cd shop
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

### 3. 访问服务

- **API 文档**: http://localhost:8001/shop/docs
- **服务状态**: 查看控制台输出

## 📊 数据结构 (每种10条)

### 1. 商品分类 (Categories)
- 电子产品、服装鞋帽、家居用品、图书音像、运动户外
- 美妆护肤、食品饮料、母婴用品、汽车用品、办公用品

### 2. 商品 (Products)
- iPhone 15 Pro、Nike运动鞋、宜家餐桌、AI编程书籍、健身器材
- 护肤套装、有机零食、婴儿奶粉、汽车香水、办公文具套装

### 3. 客户 (Customers)
- 张三、李四、王五、赵六、钱七、孙八、周九、吴十、郑十一、王十二

### 4. 订单 (Orders)
- 包含不同状态：待付款、已付款、已发货、已送达等
- 完整的订单信息：金额、收货地址、物流信息

### 5. 促销活动 (Promotions)
- 新年大促、满减活动、免运费、买一送一等
- 不同类型：折扣、固定金额、免运费

### 6. 优惠券 (Coupons)
- WELCOME10、SAVE20、PERCENT15、FREESHIP等
- 不同类型：固定金额、百分比折扣、免运费

### 7. 购物车 (Carts)
- 每个客户一个购物车
- 随机包含1-3个商品

## API 接口

### 商品相关
- `GET /shop/api/v1/products/` - 获取商品列表
- `GET /shop/api/v1/products/{id}` - 获取商品详情
- `GET /shop/api/v1/products/categories/` - 获取商品分类
- `GET /shop/api/v1/products/search/` - 搜索商品

### 订单相关
- `GET /shop/api/v1/orders/` - 获取订单列表
- `GET /shop/api/v1/orders/{id}` - 获取订单详情
- `GET /shop/api/v1/orders/number/{order_number}` - 根据订单号查询

### 客户相关
- `GET /shop/api/v1/customers/` - 获取客户列表
- `GET /shop/api/v1/customers/{id}` - 获取客户详情
- `GET /shop/api/v1/customers/{id}/orders/` - 获取客户订单

### 促销相关
- `GET /shop/api/v1/promotions/` - 获取促销活动
- `GET /shop/api/v1/promotions/coupons/` - 获取优惠券
- `GET /shop/api/v1/promotions/active/` - 获取当前有效促销

### 购物车相关
- `GET /shop/api/v1/cart/` - 获取购物车列表
- `GET /shop/api/v1/cart/{id}` - 获取购物车详情
- `GET /shop/api/v1/cart/customer/{customer_id}` - 获取客户购物车

## 🎯 客服提示词系统

### 核心系统提示词
- 角色定义：专业、友好的虚拟客服助手
- 知识范围：产品、订单、促销、政策、FAQ
- 行为准则：专业礼貌、积极主动、清晰简洁

### 场景化提示词
- **产品咨询**: 产品信息、库存查询、推荐
- **促销咨询**: 优惠活动、优惠券使用
- **订单追踪**: 订单状态、物流信息
- **售后服务**: 退换货申请、问题处理
- **投诉建议**: 问题反馈、建议收集
- **人工转接**: 转接人工客服

### 使用示例

```python
from app import get_system_prompt, get_scenario_prompt

# 获取系统提示词
system_prompt = get_system_prompt()

# 获取特定场景提示词
product_prompt = get_scenario_prompt("product_inquiry")
order_prompt = get_scenario_prompt("order_tracking")
```

## 📁 项目结构

```
shop/
├── app/
│   ├── api/v1/              # API 路由
│   │   ├── products.py      # 商品接口
│   │   ├── orders.py        # 订单接口
│   │   ├── customers.py     # 客户接口
│   │   ├── promotions.py    # 促销接口
│   │   └── cart.py          # 购物车接口
│   ├── core/                # 核心功能
│   │   └── init_app.py      # 应用初始化
│   ├── customer_service/    # 客服系统
│   │   └── ecommerce_prompts.py  # 提示词系统
│   ├── data/                # 数据初始化
│   │   └── init_data.py     # 初始化数据(每种10条)
│   ├── models/              # 数据模型
│   │   ├── product.py       # 商品模型
│   │   ├── order.py         # 订单模型
│   │   ├── user.py          # 用户模型
│   │   ├── promotion.py     # 促销模型
│   │   └── cart.py          # 购物车模型
│   └── settings/            # 配置
│       └── config.py        # 应用配置
├── requirements.txt         # 依赖包
├── run.py                  # 启动脚本
└── README.md               # 说明文档
```

## 🚨 注意事项

1. 这是一个简化的演示系统，专注于AI客服场景
2. 数据为测试数据，仅用于AI训练和演示
3. 每个数据类型精确包含10条初始化数据
4. 系统设计专注于AI客服场景，不适用于生产电商环境

## 🔧 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite + Tortoise ORM
- **AI集成**: 支持各种AI框架集成
- **数据格式**: JSON标准化返回

## 📚 集成到主系统

这个shop项目是独立的，可以通过修改主系统的run.py文件来集成启动。

## 许可证

MIT License
