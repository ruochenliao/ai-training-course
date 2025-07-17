# marker_example.py
from fastapi import FastAPI, Depends, HTTPException, Query, Path, Body, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone

# Import modules from the current directory (.)
import crud, models, schemas, database

# Create database tables if they don't exist (for demonstration)
# In production, use Alembic for migrations.
try:
    models.Base.metadata.create_all(bind=database.engine)
    print("Database tables created successfully (if they didn't exist).")
except Exception as e:
    print(f"Error creating database tables: {e}")

# Initialize FastAPI c_app
app = FastAPI(
    title="电商客服智能体后端 API",
    description="提供电商业务相关的查询和操作接口，供客服智能体调用。",
    version="1.0.0",
)


# --- Dependency ---
# Defined in database.py: get_db

# --- API Endpoints ---

# == Products ==
@app.get("/products/{product_id}", response_model=schemas.Product, tags=["商品 (Products)"], summary="获取商品详情")
def read_product(product_id: int = Path(..., title="商品 ID", ge=1), db: Session = Depends(database.get_db)):
    """
    根据商品 ID 获取详细信息，包括名称、描述、价格、库存、规格等。
    供智能体查询特定商品信息使用。
    """
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@app.get("/products/", response_model=List[schemas.ProductSearchResult], tags=["商品 (Products)"], summary="搜索商品")
def search_products(
        query: str = Query(..., min_length=2, title="搜索关键词", description="在商品名称或描述中搜索"),
        skip: int = Query(0, ge=0, title="跳过数量"),
        limit: int = Query(10, ge=1, le=100, title="返回数量限制"),
        db: Session = Depends(database.get_db)
):
    """
    根据关键词搜索商品，返回匹配商品列表（基础信息）。
    供智能体根据用户描述推荐或查找商品。
    """
    products = crud.search_products(db, query=query, skip=skip, limit=limit)
    return products


# == Orders ==
@app.get("/orders/status/{order_number}", response_model=schemas.OrderStatusResult, tags=["订单 (Orders)"],
         summary="查询订单状态和物流")
def read_order_status(
        order_number: str = Path(..., title="订单号", description="用户提供的订单编号"),
        # Add basic verification if needed, e.g., last 4 digits of phone
        # verification_token: Optional[str] = Query(None, title="验证信息")
        db: Session = Depends(database.get_db)
):
    """
    根据订单号查询订单状态和基本的物流跟踪信息。
    供智能体回答用户关于"我的订单到哪了"的询问。
    *注意：实际应用中需要验证用户身份才能查询订单。*
    """
    db_order = crud.get_order_by_number(db, order_number=order_number)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Fetch shipment info if available
    shipment = crud.get_shipment_by_order_id(db, order_id=db_order.id)
    tracking_url = None
    if shipment and shipment.tracking_number and shipment.carrier:
        # Example: Generate a dummy tracking URL
        tracking_url = f"https://track.example.com/{shipment.carrier.lower()}/{shipment.tracking_number}"

    return schemas.OrderStatusResult(
        order_number=db_order.order_number,
        status=db_order.status,
        estimated_delivery_date=shipment.estimated_delivery_date if shipment else None,
        tracking_number=shipment.tracking_number if shipment else None,
        tracking_url=tracking_url
    )

@app.post("/orders/{order_number}/cancel", response_model=schemas.OrderCancelResult, tags=["订单 (Orders)"], summary="取消订单")
def cancel_order_endpoint(
    order_number: str = Path(..., title="订单号", description="要取消的订单编号"),
    db: Session = Depends(database.get_db)
):
    """
    尝试取消指定订单号的订单。
    - 只有处于特定状态（如 'pending', 'processing'）的订单才能被取消。
    - 成功取消后会恢复订单中商品的库存。
    *注意：实际应用中需要验证用户身份及权限。*
    """
    try:
        cancelled_order = crud.cancel_order(db=db, order_number=order_number)
        return schemas.OrderCancelResult(
            order_number=cancelled_order.order_number,
            status=cancelled_order.status,
            message="订单已成功取消，库存已恢复。"
        )
    except ValueError as e:
        # Handle specific errors from crud.cancel_order
        error_detail = str(e)
        if "Order not found" in error_detail:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=error_detail)
        elif "cannot be cancelled" in error_detail or "already cancelled" in error_detail:
            # Use 409 Conflict or 400 Bad Request for state issues
            raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=error_detail)
        else:
            # Catch other ValueErrors (like internal errors during cancellation)
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=error_detail)
    except Exception as e:
        # Catch unexpected errors
        print(f"Unexpected error cancelling order {order_number}: {e}")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="取消订单时发生内部错误。")


# == Promotions ==
@app.get("/promotions/active", response_model=List[schemas.Promotion], tags=["促销活动 (Promotions)"],
         summary="获取当前有效活动")
def read_active_promotions(db: Session = Depends(database.get_db)):
    """
    获取当前所有有效的促销活动信息列表。
    供智能体告知用户当前的优惠活动。
    """
    promotions = crud.get_active_promotions(db)
    return promotions


# == Policies ==
@app.get("/policies/{policy_type}", response_model=schemas.Policy, tags=["店铺政策 (Policies)"],
         summary="获取指定类型的政策")
def read_policy(
        policy_type: schemas.PolicyTypeEnum = Path(..., title="政策类型", description="例如: return, shipping"),
        db: Session = Depends(database.get_db)
):
    """
    获取指定类型的最新店铺政策内容（如退货政策、运费政策）。
    供智能体向用户解释相关规定。
    """
    policy = crud.get_policy(db, policy_type=policy_type)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy type '{policy_type.value}' not found or not configured.")
    return policy


# == Returns ==
@app.post("/returns/check-eligibility", response_model=schemas.ReturnEligibilityResult, tags=["退换货 (Returns)"],
          summary="检查商品退货资格")
def check_return_eligibility(
        eligibility_check: schemas.ReturnEligibilityCheck = Body(...),
        db: Session = Depends(database.get_db)
):
    """
    根据订单号和商品SKU检查该商品是否符合退货条件。
    供智能体判断用户是否可以退货，并告知原因或政策摘要。
    """
    result = crud.check_return_eligibility(db, order_number=eligibility_check.order_number,
                                           product_sku=eligibility_check.product_sku)
    return result


@app.post("/returns/", response_model=schemas.ReturnRequest, status_code=201, tags=["退换货 (Returns)"],
          summary="提交退货请求")
def create_return_request(
        return_request: schemas.ReturnRequestCreate = Body(...),
        db: Session = Depends(database.get_db)
):
    """
    （模拟）提交一个退货请求。实际系统需要更复杂的流程。
    供智能体在用户确认退货意向后，（如果系统允许）帮助用户发起初步请求。
    *注意：需要用户身份验证。*
    """
    # Add user validation here in a real c_app
    # Check eligibility again before creating
    eligibility = crud.check_return_eligibility(db,
                                                order_number=crud.get_order(db, return_request.order_id).order_number,
                                                product_sku=crud.get_product(db, return_request.product_id).sku)
    if not eligibility["is_eligible"]:
        raise HTTPException(status_code=400, detail=f"Item not eligible for return: {eligibility['reason']}")

    created_request = crud.create_return_request(db=db, return_request=return_request)
    return created_request


# == Feedback ==
@app.post("/feedback/", response_model=schemas.Feedback, status_code=201, tags=["用户反馈 (Feedback)"],
          summary="提交用户反馈")
def create_feedback(
        feedback: schemas.FeedbackCreate = Body(...),
        db: Session = Depends(database.get_db)
):
    """
    接收并存储用户的投诉、建议或表扬。
    供智能体记录用户的反馈信息。
    """
    created_feedback = crud.create_feedback(db=db, feedback=feedback)
    return created_feedback


# --- Root Endpoint ---
@app.get("/", tags=["通用 (General)"], summary="API 健康检查")
def read_root():
    """API 根路径，用于简单的健康检查。"""
    return {"message": "欢迎使用电商客服智能体后端 API"}


# --- Example: Add initial data (Optional, better done via a script) ---
@app.on_event("startup")
async def startup_event():
    """(Optional) Add some initial data on startup if DB is empty."""
    db = next(database.get_db())
    try:
        # 检查并添加默认政策
        policies = crud.get_policies(db)
        if not policies:
            print("添加默认政策...")
            # 退货政策
            crud.create_policy(db, schemas.PolicyCreate(
                policy_type=models.PolicyTypeEnum.RETURN,
                content="支持7天无理由退货（特殊商品除外）。商品需保持完好，配件齐全，不影响二次销售。请通过订单页面申请。",
                version="1.0"
            ))
            # 运费政策
            crud.create_policy(db, schemas.PolicyCreate(
                policy_type=models.PolicyTypeEnum.SHIPPING,
                content="默认使用顺丰快递，满99元包邮。发货时间为付款后48小时内。偏远地区运费另计。",
                version="1.0"
            ))
            # 支付政策
            crud.create_policy(db, schemas.PolicyCreate(
                policy_type=models.PolicyTypeEnum.PAYMENT,
                content="支持支付宝、微信支付、银行卡等多种支付方式。支付成功后请保留支付凭证。",
                version="1.0"
            ))
            # 隐私政策
            crud.create_policy(db, schemas.PolicyCreate(
                policy_type=models.PolicyTypeEnum.PRIVACY,
                content="我们承诺保护您的个人信息安全，不会将您的信息用于其他用途。",
                version="1.0"
            ))
            # 服务条款
            crud.create_policy(db, schemas.PolicyCreate(
                policy_type=models.PolicyTypeEnum.TERMS,
                content="使用本平台即表示您同意我们的服务条款。请仔细阅读并遵守相关规定。",
                version="1.0"
            ))

        # 检查并添加商品分类
        categories = crud.get_categories(db)
        if not categories:
            print("添加商品分类...")
            # 电子产品分类
            electronics = crud.create_category(db, schemas.CategoryCreate(
                name="电子产品",
                description="包括手机、电脑、智能设备等消费类电子产品"
            ))
            # 家居用品分类
            home = crud.create_category(db, schemas.CategoryCreate(
                name="家居用品",
                description="包括家具、装饰、厨具等家居用品"
            ))
            # 服装分类
            clothing = crud.create_category(db, schemas.CategoryCreate(
                name="服装",
                description="包括男装、女装、童装等各类服装"
            ))

            # 添加商品
            print("添加商品...")
            # 电子产品
            crud.create_product(db, schemas.ProductCreate(
                name="华为Mate 60 Pro",
                description="最新款华为旗舰手机，搭载麒麟9000S芯片，支持5G网络",
                price=6999.00,
                stock_quantity=100,
                category_id=electronics.id,
                sku="PH-HW-M60P",
                image_url="https://placehold.co/600x400/EEE/31343C?text=华为Mate60",
                specifications='{"处理器": "麒麟9000S", "内存": "12GB", "存储": "512GB", "屏幕": "6.8英寸"}'
            ))
            crud.create_product(db, schemas.ProductCreate(
                name="小米智能手表",
                description="支持心率监测、血氧检测、GPS定位等功能",
                price=1299.00,
                stock_quantity=50,
                category_id=electronics.id,
                sku="SW-XM-001",
                image_url="https://placehold.co/600x400/EEE/31343C?text=小米手表",
                specifications='{"屏幕": "1.4寸 AMOLED", "电池": "3天", "防水": "IP68"}'
            ))
            # 家居用品
            crud.create_product(db, schemas.ProductCreate(
                name="北欧风格沙发",
                description="简约现代风格，舒适耐用，适合小户型",
                price=2999.00,
                stock_quantity=20,
                category_id=home.id,
                sku="SOFA-NB-001",
                image_url="https://placehold.co/600x400/EEE/31343C?text=北欧沙发",
                specifications='{"材质": "布艺", "尺寸": "2.2米", "颜色": "米白色"}'
            ))
            # 服装
            crud.create_product(db, schemas.ProductCreate(
                name="男士休闲西装",
                description="商务休闲两用，修身版型，舒适透气",
                price=899.00,
                stock_quantity=30,
                category_id=clothing.id,
                sku="CL-M-SUIT-001",
                image_url="https://placehold.co/600x400/EEE/31343C?text=男士西装",
                specifications='{"材质": "羊毛", "尺码": "M/L/XL", "颜色": "深蓝色"}'
            ))

        # 检查并添加用户
        users = crud.get_users(db)
        if not users:
            print("添加用户...")
            # 创建测试用户
            user1 = crud.create_user(db, schemas.UserCreate(
                email="zhangsan@example.com",
                password="password123",
                full_name="张三"
            ))
            user2 = crud.create_user(db, schemas.UserCreate(
                email="lisi@example.com",
                password="password123",
                full_name="李四"
            ))

            # 为用户添加地址
            print("添加用户地址...")
            # 张三的地址
            crud.create_address(db, schemas.AddressCreate(
                user_id=user1.id,
                address_line1="北京市朝阳区建国路88号",
                address_line2="华贸中心1号楼",
                city="北京",
                state="北京",
                postal_code="100022",
                country="CN",
                is_default_shipping=True,
                is_default_billing=True
            ))
            # 李四的地址
            crud.create_address(db, schemas.AddressCreate(
                user_id=user2.id,
                address_line1="上海市浦东新区陆家嘴环路1000号",
                address_line2="环球金融中心",
                city="上海",
                state="上海",
                postal_code="200120",
                country="CN",
                is_default_shipping=True,
                is_default_billing=True
            ))

            # 创建订单
            print("添加订单...")
            # 张三的订单
            order1 = crud.create_order(db, schemas.OrderCreate(
                user_id=user1.id,
                shipping_address_id=1,
                billing_address_id=1,
                items=[schemas.OrderItemCreate(
                    product_id=1,  # 华为手机
                    quantity=1
                )]
            ))

            # 李四的订单
            order2 = crud.create_order(db, schemas.OrderCreate(
                user_id=user2.id,
                shipping_address_id=2,
                billing_address_id=2,
                items=[schemas.OrderItemCreate(
                    product_id=3,  # 沙发
                    quantity=1
                )]
            ))

            from datetime import datetime, timedelta, timezone
            # 添加物流信息
            print("添加物流信息...")
            crud.create_shipment(db, schemas.ShipmentCreate(
                order_id=order1.id,
                carrier="顺丰快递",
                tracking_number="SF1234567890",
                shipped_date=datetime.now(timezone.utc) - timedelta(days=3),
                estimated_delivery_date=datetime.now(timezone.utc) + timedelta(days=2),
                actual_delivery_date=datetime.now(timezone.utc) - timedelta(days=1),
                status="已签收"
            ))

        # 检查并添加促销活动
        promotions = crud.get_active_promotions(db)
        if not promotions:
            print("添加促销活动...")
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)

            # 新用户优惠
            crud.create_promotion(db, schemas.PromotionCreate(
                code="WELCOME10",
                description="新用户专享：首单9折优惠",
                discount_percentage=10.0,
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=30),
                is_active=True,
                minimum_spend=0
            ))

            # 满减活动
            crud.create_promotion(db, schemas.PromotionCreate(
                code="FREESHIP",
                description="满99元包邮",
                discount_amount=0,
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=30),
                is_active=True,
                minimum_spend=99
            ))

        # 添加用户反馈
        feedbacks = crud.get_feedback(db)
        if not feedbacks:
            print("添加用户反馈...")
            crud.create_feedback(db, schemas.FeedbackCreate(
                user_id=1,
                email="zhangsan@example.com",
                feedback_type=models.FeedbackTypeEnum.PRAISE,
                subject="商品质量很好",
                content="手机收到后很满意，运行流畅，拍照效果很好。"
            ))
            crud.create_feedback(db, schemas.FeedbackCreate(
                user_id=2,
                email="lisi@example.com",
                feedback_type=models.FeedbackTypeEnum.SUGGESTION,
                subject="建议增加更多款式",
                content="希望家居用品能增加更多现代简约风格的款式。"
            ))

        print("初始化数据添加完成。")
    finally:
        db.close()


import uvicorn

if __name__ == "__main__":
    # 使用uvicorn启动FastAPI应用
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )

# --- How to Run ---
# 1. Install dependencies: pip install fastapi uvicorn sqlalchemy psycopg2-binary (or appropriate DB driver) python-dotenv passlib[bcrypt]
#    For SQLite (as used here), you might not need a separate driver install with newer Python versions.
# 2. Run the server: uvicorn main:c_app --reload --port 8000
# 3. Access the interactive API docs at http://127.0.0.1:8000/docs
