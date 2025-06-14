import hashlib
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    Category, Product, ProductImage, Customer, CustomerAddress,
    Order, OrderItem, OrderStatus, Promotion, PromotionType,
    Coupon, CouponType, CouponUsage, Cart, CartItem
)


async def init_shop_data():
    """初始化电商数据 - 每个类型10条数据"""
    
    # 检查是否已经初始化
    if await Category.exists():
        print("数据已存在，跳过初始化")
        return
    
    print("开始初始化电商数据...")
    
    # 1. 初始化商品分类 (10条)
    categories_data = [
        {"name": "电子产品", "description": "手机、电脑、数码产品等", "sort_order": 1},
        {"name": "服装鞋帽", "description": "男装、女装、鞋子、配饰等", "sort_order": 2},
        {"name": "家居用品", "description": "家具、装饰、生活用品等", "sort_order": 3},
        {"name": "图书音像", "description": "图书、音乐、影视等", "sort_order": 4},
        {"name": "运动户外", "description": "运动器材、户外用品等", "sort_order": 5},
        {"name": "美妆护肤", "description": "化妆品、护肤品、个护用品等", "sort_order": 6},
        {"name": "食品饮料", "description": "零食、饮料、生鲜等", "sort_order": 7},
        {"name": "母婴用品", "description": "婴儿用品、玩具、奶粉等", "sort_order": 8},
        {"name": "汽车用品", "description": "汽车配件、装饰、保养等", "sort_order": 9},
        {"name": "办公用品", "description": "文具、办公设备、耗材等", "sort_order": 10},
    ]
    
    categories = []
    for data in categories_data:
        category = await Category.create(**data)
        categories.append(category)
    
    # 2. 初始化商品 (10条)
    products_data = [
        {
            "name": "iPhone 15 Pro", "sku": "IP15P001", "price": Decimal("7999.00"), 
            "original_price": Decimal("8999.00"), "stock": 50, "category": categories[0],
            "description": "苹果最新旗舰手机，搭载A17 Pro芯片", "brand": "Apple", "rating": Decimal("4.8")
        },
        {
            "name": "Nike Air Max 270", "sku": "NK270001", "price": Decimal("899.00"),
            "original_price": Decimal("1099.00"), "stock": 30, "category": categories[1],
            "description": "Nike经典气垫跑鞋，舒适透气", "brand": "Nike", "rating": Decimal("4.6")
        },
        {
            "name": "宜家北欧餐桌", "sku": "IKEA001", "price": Decimal("1299.00"),
            "stock": 15, "category": categories[2],
            "description": "简约北欧风格餐桌，实木材质", "brand": "宜家", "rating": Decimal("4.5")
        },
        {
            "name": "《AI编程实战》", "sku": "BOOK001", "price": Decimal("89.00"),
            "stock": 100, "category": categories[3],
            "description": "深入浅出的AI编程教程", "brand": "人民邮电出版社", "rating": Decimal("4.7")
        },
        {
            "name": "哑铃健身套装", "sku": "FIT001", "price": Decimal("299.00"),
            "stock": 25, "category": categories[4],
            "description": "可调节重量哑铃，适合家庭健身", "brand": "力量之源", "rating": Decimal("4.4")
        },
        {
            "name": "兰蔻护肤套装", "sku": "LAN001", "price": Decimal("599.00"),
            "original_price": Decimal("799.00"), "stock": 40, "category": categories[5],
            "description": "兰蔻经典护肤三件套", "brand": "兰蔻", "rating": Decimal("4.9")
        },
        {
            "name": "有机坚果礼盒", "sku": "NUT001", "price": Decimal("168.00"),
            "stock": 60, "category": categories[6],
            "description": "精选有机坚果，健康美味", "brand": "三只松鼠", "rating": Decimal("4.3")
        },
        {
            "name": "婴儿有机奶粉", "sku": "MILK001", "price": Decimal("358.00"),
            "stock": 80, "category": categories[7],
            "description": "进口有机奶粉，营养丰富", "brand": "美赞臣", "rating": Decimal("4.8")
        },
        {
            "name": "汽车香水摆件", "sku": "CAR001", "price": Decimal("39.00"),
            "stock": 200, "category": categories[8],
            "description": "车载香水摆件，持久留香", "brand": "车仆", "rating": Decimal("4.2")
        },
        {
            "name": "办公文具套装", "sku": "OFF001", "price": Decimal("129.00"),
            "stock": 150, "category": categories[9],
            "description": "办公必备文具套装", "brand": "晨光", "rating": Decimal("4.5")
        },
    ]
    
    products = []
    for data in products_data:
        product = await Product.create(**data)
        products.append(product)
    
    # 3. 初始化客户 (10条)
    customers_data = [
        {"username": "张三", "email": "zhangsan@example.com", "phone": "13800138001", "first_name": "三", "last_name": "张"},
        {"username": "李四", "email": "lisi@example.com", "phone": "13800138002", "first_name": "四", "last_name": "李"},
        {"username": "王五", "email": "wangwu@example.com", "phone": "13800138003", "first_name": "五", "last_name": "王"},
        {"username": "赵六", "email": "zhaoliu@example.com", "phone": "13800138004", "first_name": "六", "last_name": "赵"},
        {"username": "钱七", "email": "qianqi@example.com", "phone": "13800138005", "first_name": "七", "last_name": "钱"},
        {"username": "孙八", "email": "sunba@example.com", "phone": "13800138006", "first_name": "八", "last_name": "孙"},
        {"username": "周九", "email": "zhoujiu@example.com", "phone": "13800138007", "first_name": "九", "last_name": "周"},
        {"username": "吴十", "email": "wushi@example.com", "phone": "13800138008", "first_name": "十", "last_name": "吴"},
        {"username": "郑十一", "email": "zhengshiyi@example.com", "phone": "13800138009", "first_name": "十一", "last_name": "郑"},
        {"username": "王十二", "email": "wangshier@example.com", "phone": "13800138010", "first_name": "十二", "last_name": "王"},
    ]
    
    customers = []
    for data in customers_data:
        # 简单的密码哈希
        data["password_hash"] = hashlib.md5("123456".encode()).hexdigest()
        customer = await Customer.create(**data)
        customers.append(customer)
    
    # 4. 初始化订单 (10条)
    now = datetime.now()
    orders_data = [
        {
            "order_number": "ORD202401001", "customer": customers[0], "status": OrderStatus.DELIVERED,
            "subtotal": Decimal("7999.00"), "total_amount": Decimal("7999.00"),
            "shipping_name": "张三", "shipping_phone": "13800138001", "shipping_address": "北京市朝阳区xxx街道xxx号",
            "paid_at": now - timedelta(days=5), "delivered_at": now - timedelta(days=1)
        },
        {
            "order_number": "ORD202401002", "customer": customers[1], "status": OrderStatus.SHIPPED,
            "subtotal": Decimal("899.00"), "total_amount": Decimal("899.00"),
            "shipping_name": "李四", "shipping_phone": "13800138002", "shipping_address": "上海市浦东新区xxx路xxx号",
            "paid_at": now - timedelta(days=3), "shipped_at": now - timedelta(days=1)
        },
        {
            "order_number": "ORD202401003", "customer": customers[2], "status": OrderStatus.PAID,
            "subtotal": Decimal("1299.00"), "total_amount": Decimal("1299.00"),
            "shipping_name": "王五", "shipping_phone": "13800138003", "shipping_address": "广州市天河区xxx大道xxx号",
            "paid_at": now - timedelta(days=2)
        },
        {
            "order_number": "ORD202401004", "customer": customers[3], "status": OrderStatus.PENDING,
            "subtotal": Decimal("89.00"), "total_amount": Decimal("89.00"),
            "shipping_name": "赵六", "shipping_phone": "13800138004", "shipping_address": "深圳市南山区xxx路xxx号"
        },
        {
            "order_number": "ORD202401005", "customer": customers[4], "status": OrderStatus.DELIVERED,
            "subtotal": Decimal("299.00"), "total_amount": Decimal("299.00"),
            "shipping_name": "钱七", "shipping_phone": "13800138005", "shipping_address": "杭州市西湖区xxx街xxx号",
            "paid_at": now - timedelta(days=7), "delivered_at": now - timedelta(days=3)
        },
        {
            "order_number": "ORD202401006", "customer": customers[5], "status": OrderStatus.SHIPPED,
            "subtotal": Decimal("599.00"), "total_amount": Decimal("599.00"),
            "shipping_name": "孙八", "shipping_phone": "13800138006", "shipping_address": "南京市鼓楼区xxx路xxx号",
            "paid_at": now - timedelta(days=4), "shipped_at": now - timedelta(days=2)
        },
        {
            "order_number": "ORD202401007", "customer": customers[6], "status": OrderStatus.DELIVERED,
            "subtotal": Decimal("168.00"), "total_amount": Decimal("168.00"),
            "shipping_name": "周九", "shipping_phone": "13800138007", "shipping_address": "武汉市武昌区xxx街xxx号",
            "paid_at": now - timedelta(days=6), "delivered_at": now - timedelta(days=2)
        },
        {
            "order_number": "ORD202401008", "customer": customers[7], "status": OrderStatus.PAID,
            "subtotal": Decimal("358.00"), "total_amount": Decimal("358.00"),
            "shipping_name": "吴十", "shipping_phone": "13800138008", "shipping_address": "成都市锦江区xxx路xxx号",
            "paid_at": now - timedelta(days=1)
        },
        {
            "order_number": "ORD202401009", "customer": customers[8], "status": OrderStatus.DELIVERED,
            "subtotal": Decimal("39.00"), "total_amount": Decimal("39.00"),
            "shipping_name": "郑十一", "shipping_phone": "13800138009", "shipping_address": "西安市雁塔区xxx大道xxx号",
            "paid_at": now - timedelta(days=8), "delivered_at": now - timedelta(days=4)
        },
        {
            "order_number": "ORD202401010", "customer": customers[9], "status": OrderStatus.SHIPPED,
            "subtotal": Decimal("129.00"), "total_amount": Decimal("129.00"),
            "shipping_name": "王十二", "shipping_phone": "13800138010", "shipping_address": "重庆市渝北区xxx街xxx号",
            "paid_at": now - timedelta(days=3), "shipped_at": now - timedelta(days=1)
        },
    ]

    orders = []
    for data in orders_data:
        order = await Order.create(**data)
        orders.append(order)

    # 5. 初始化促销活动 (10条)
    promotions_data = [
        {
            "name": "新年大促", "description": "新年特惠，全场8折", "type": PromotionType.DISCOUNT,
            "discount_value": Decimal("0.8"), "min_order_amount": Decimal("100.00"),
            "start_date": now - timedelta(days=10), "end_date": now + timedelta(days=20)
        },
        {
            "name": "满减活动", "description": "满500减50", "type": PromotionType.FIXED_AMOUNT,
            "discount_value": Decimal("50.00"), "min_order_amount": Decimal("500.00"),
            "start_date": now - timedelta(days=5), "end_date": now + timedelta(days=15)
        },
        {
            "name": "免运费", "description": "全场免运费", "type": PromotionType.FREE_SHIPPING,
            "discount_value": Decimal("0.00"), "min_order_amount": Decimal("99.00"),
            "start_date": now - timedelta(days=3), "end_date": now + timedelta(days=10)
        },
        {
            "name": "买一送一", "description": "指定商品买一送一", "type": PromotionType.BUY_ONE_GET_ONE,
            "discount_value": Decimal("0.5"), "min_order_amount": Decimal("0.00"),
            "start_date": now - timedelta(days=7), "end_date": now + timedelta(days=7)
        },
        {
            "name": "春季特惠", "description": "春季商品7折优惠", "type": PromotionType.DISCOUNT,
            "discount_value": Decimal("0.7"), "min_order_amount": Decimal("200.00"),
            "start_date": now - timedelta(days=15), "end_date": now + timedelta(days=30)
        },
        {
            "name": "会员专享", "description": "会员专享满300减30", "type": PromotionType.FIXED_AMOUNT,
            "discount_value": Decimal("30.00"), "min_order_amount": Decimal("300.00"),
            "start_date": now - timedelta(days=20), "end_date": now + timedelta(days=40)
        },
        {
            "name": "电子产品促销", "description": "电子产品9折", "type": PromotionType.DISCOUNT,
            "discount_value": Decimal("0.9"), "min_order_amount": Decimal("1000.00"),
            "start_date": now - timedelta(days=12), "end_date": now + timedelta(days=18)
        },
        {
            "name": "服装清仓", "description": "服装类商品6折", "type": PromotionType.DISCOUNT,
            "discount_value": Decimal("0.6"), "min_order_amount": Decimal("150.00"),
            "start_date": now - timedelta(days=8), "end_date": now + timedelta(days=12)
        },
        {
            "name": "图书优惠", "description": "图书满100减20", "type": PromotionType.FIXED_AMOUNT,
            "discount_value": Decimal("20.00"), "min_order_amount": Decimal("100.00"),
            "start_date": now - timedelta(days=6), "end_date": now + timedelta(days=25)
        },
        {
            "name": "母婴用品特价", "description": "母婴用品8.5折", "type": PromotionType.DISCOUNT,
            "discount_value": Decimal("0.85"), "min_order_amount": Decimal("200.00"),
            "start_date": now - timedelta(days=4), "end_date": now + timedelta(days=16)
        },
    ]

    promotions = []
    for data in promotions_data:
        promotion = await Promotion.create(**data)
        promotions.append(promotion)

    # 6. 初始化优惠券 (10条)
    coupons_data = [
        {
            "code": "WELCOME10", "name": "新用户优惠券", "description": "新用户专享10元优惠",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("10.00"),
            "min_order_amount": Decimal("50.00"), "start_date": now - timedelta(days=30),
            "end_date": now + timedelta(days=60), "usage_limit": 1000
        },
        {
            "code": "SAVE20", "name": "满减券", "description": "满200减20",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("20.00"),
            "min_order_amount": Decimal("200.00"), "start_date": now - timedelta(days=15),
            "end_date": now + timedelta(days=30), "usage_limit": 500
        },
        {
            "code": "PERCENT15", "name": "85折优惠券", "description": "全场85折",
            "type": CouponType.PERCENTAGE, "discount_value": Decimal("0.15"),
            "min_order_amount": Decimal("100.00"), "start_date": now - timedelta(days=10),
            "end_date": now + timedelta(days=20), "usage_limit": 200
        },
        {
            "code": "FREESHIP", "name": "免运费券", "description": "免运费优惠",
            "type": CouponType.FREE_SHIPPING, "discount_value": Decimal("0.00"),
            "min_order_amount": Decimal("99.00"), "start_date": now - timedelta(days=20),
            "end_date": now + timedelta(days=40), "usage_limit": 1000
        },
        {
            "code": "VIP50", "name": "VIP专享券", "description": "VIP用户专享50元优惠",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("50.00"),
            "min_order_amount": Decimal("500.00"), "start_date": now - timedelta(days=25),
            "end_date": now + timedelta(days=35), "usage_limit": 100
        },
        {
            "code": "SPRING30", "name": "春季优惠券", "description": "春季特惠30元",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("30.00"),
            "min_order_amount": Decimal("300.00"), "start_date": now - timedelta(days=12),
            "end_date": now + timedelta(days=25), "usage_limit": 300
        },
        {
            "code": "TECH10", "name": "数码产品券", "description": "数码产品9折",
            "type": CouponType.PERCENTAGE, "discount_value": Decimal("0.1"),
            "min_order_amount": Decimal("1000.00"), "start_date": now - timedelta(days=8),
            "end_date": now + timedelta(days=15), "usage_limit": 150
        },
        {
            "code": "BOOK5", "name": "图书优惠券", "description": "图书类5元优惠",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("5.00"),
            "min_order_amount": Decimal("50.00"), "start_date": now - timedelta(days=18),
            "end_date": now + timedelta(days=32), "usage_limit": 800
        },
        {
            "code": "BEAUTY25", "name": "美妆优惠券", "description": "美妆产品满200减25",
            "type": CouponType.FIXED_AMOUNT, "discount_value": Decimal("25.00"),
            "min_order_amount": Decimal("200.00"), "start_date": now - timedelta(days=14),
            "end_date": now + timedelta(days=28), "usage_limit": 250
        },
        {
            "code": "FAMILY15", "name": "家庭用品券", "description": "家庭用品85折",
            "type": CouponType.PERCENTAGE, "discount_value": Decimal("0.15"),
            "min_order_amount": Decimal("150.00"), "start_date": now - timedelta(days=22),
            "end_date": now + timedelta(days=38), "usage_limit": 400
        },
    ]

    coupons = []
    for data in coupons_data:
        coupon = await Coupon.create(**data)
        coupons.append(coupon)

    # 7. 初始化购物车 (10条)
    carts = []
    for i, customer in enumerate(customers):
        cart = await Cart.create(customer=customer)
        carts.append(cart)

        # 为每个购物车添加1-3个商品
        import random
        num_items = random.randint(1, 3)
        selected_products = random.sample(products, num_items)

        for product in selected_products:
            quantity = random.randint(1, 3)
            await CartItem.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

    print("电商数据初始化完成！")
    print(f"- 商品分类: {len(categories)} 条")
    print(f"- 商品: {len(products)} 条")
    print(f"- 客户: {len(customers)} 条")
    print(f"- 订单: {len(orders)} 条")
    print(f"- 促销活动: {len(promotions)} 条")
    print(f"- 优惠券: {len(coupons)} 条")
    print(f"- 购物车: {len(carts)} 条")
