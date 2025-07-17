# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, or_ # Import 'or_' for complex queries
from datetime import datetime, timedelta
import random

import models, schemas

# --- Product CRUD ---

def get_product(db: Session, product_id: int):
    """根据ID获取单个商品"""
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str):
    """根据SKU获取单个商品"""
    return db.query(models.Product).filter(models.Product.sku == sku).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    """获取商品列表（分页）"""
    return db.query(models.Product).offset(skip).limit(limit).all()

def search_products(db: Session, query: str, skip: int = 0, limit: int = 20):
    """根据名称或描述搜索商品"""
    search_term = f"%{query}%" # 准备LIKE查询的搜索词
    return db.query(models.Product)\
             .filter(or_(models.Product.name.ilike(search_term),
                         models.Product.description.ilike(search_term)))\
             .offset(skip)\
             .limit(limit)\
             .all()

def create_product(db: Session, product: schemas.ProductCreate):
    """创建新商品"""
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# --- Category CRUD ---

def get_category(db: Session, category_id: int):
    """根据ID获取单个分类"""
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """获取分类列表"""
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    """创建新分类"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# --- Order CRUD ---

def get_order(db: Session, order_id: int):
    """根据ID获取单个订单"""
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_order_by_number(db: Session, order_number: str):
    """根据订单号获取订单"""
    return db.query(models.Order).filter(models.Order.order_number == order_number).first()

def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    """获取用户的订单列表"""
    return db.query(models.Order).filter(models.Order.user_id == user_id)\
             .order_by(models.Order.order_date.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()

def create_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    """创建新订单"""
    # 生成订单号：ORD + 年月日 + 4位随机数
    now = datetime.now()
    random_num = random.randint(1000, 9999)
    order_number = f"ORD{now.strftime('%Y%m%d')}{random_num}"
    
    db_order = models.Order(
        order_number=order_number,
        user_id=order.user_id,
        shipping_address_id=order.shipping_address_id,
        billing_address_id=order.billing_address_id,
        status=models.OrderStatusEnum.PENDING,
        total_amount=0.0,  # 初始化为0，后续会根据商品计算
        order_date=now
    )
    db.add(db_order)
    db.flush()  # 获取order_id
    
    # 创建订单项
    for item in order.items:
        product = get_product(db, item.product_id)
        if not product:
            raise ValueError(f"商品ID {item.product_id} 不存在")
            
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_unit=product.price
        )
        db.add(db_item)
        db_order.total_amount += product.price * item.quantity
    
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: models.OrderStatusEnum):
    """更新订单状态"""
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if db_order:
        db_order.status = status
        db.commit()
        db.refresh(db_order)
    return db_order

# --- OrderItem CRUD ---

def create_order_item(db: Session, order_item: schemas.OrderItemCreate):
    """创建订单商品项"""
    db_order_item = models.OrderItem(**order_item.dict())
    db.add(db_order_item)
    db.commit()
    db.refresh(db_order_item)
    return db_order_item

def cancel_order(db: Session, order_number: str):
    """
    Cancels an order if it's in a cancellable state and restores stock.
    Returns the updated order or raises an exception.
    """
    db_order = get_order_by_number(db, order_number=order_number) # Uses the optimized query with joinedload

    if not db_order:
        raise ValueError("Order not found.")

    # Define cancellable statuses
    cancellable_statuses = [
        models.OrderStatusEnum.PENDING,
        models.OrderStatusEnum.PROCESSING,
        # Add other statuses if applicable, e.g., 'Awaiting Payment'
    ]

    if db_order.status not in cancellable_statuses:
        raise ValueError(f"Order cannot be cancelled. Current status: {db_order.status.value}")

    if db_order.status == models.OrderStatusEnum.CANCELLED:
         raise ValueError("Order is already cancelled.") # Avoid re-cancelling

    # --- Start Transaction (Implicit with commit/rollback) ---
    try:
        # Restore stock for each item in the order
        if not db_order.items: # Ensure items were loaded
             raise ValueError("Order items not loaded correctly for stock restoration.")

        for item in db_order.items:
            product = item.product # Access product loaded via joinedload
            if not product:
                 # Fallback if joinedload didn't work or product was deleted
                 product = get_product(db, item.product_id)
                 if not product:
                      print(f"Warning: Product ID {item.product_id} not found during stock restoration for order {order_number}. Skipping.")
                      continue # Skip if product doesn't exist anymore

            # Increase stock quantity
            product.stock_quantity += item.quantity
            print(f"Restored stock for Product ID {product.id} (SKU: {product.sku}): +{item.quantity}, New Stock: {product.stock_quantity}")

        # Update order status to Cancelled
        db_order.status = models.OrderStatusEnum.CANCELLED

        # Commit transaction (stock update and status change)
        db.commit()
        db.refresh(db_order) # Refresh to get the final state
        return db_order

    except Exception as e:
        db.rollback() # Rollback transaction on error
        print(f"Error cancelling order {order_number}: {e}")
        # Re-raise a more specific error if needed, or the original one
        raise ValueError(f"Failed to cancel order due to an internal error: {e}")

# --- Shipment CRUD ---

def get_shipment_by_order_id(db: Session, order_id: int):
    """根据订单ID获取物流信息"""
    return db.query(models.Shipment).filter(models.Shipment.order_id == order_id).first()

def create_shipment(db: Session, shipment: schemas.ShipmentCreate):
    """创建物流信息"""
    db_shipment = models.Shipment(**shipment.dict())
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

# --- Promotion CRUD ---

def get_active_promotions(db: Session):
    """获取当前有效的促销活动"""
    now = datetime.now() # 确保时区感知的比较
    return db.query(models.Promotion)\
             .filter(models.Promotion.is_active == True,
                     models.Promotion.start_date <= now,
                     models.Promotion.end_date >= now)\
             .all()

def create_promotion(db: Session, promotion: schemas.PromotionCreate):
    """创建新促销活动"""
    db_promotion = models.Promotion(**promotion.dict())
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

# --- Policy CRUD ---

def get_policy(db: Session, policy_type: models.PolicyTypeEnum):
    """获取指定类型的最新政策"""
    return db.query(models.Policy)\
             .filter(models.Policy.policy_type == policy_type)\
             .order_by(models.Policy.last_updated.desc())\
             .first()

def get_policies(db: Session):
    """获取所有政策"""
    return db.query(models.Policy).all()

def create_policy(db: Session, policy: schemas.PolicyCreate):
    """创建新政策"""
    db_policy = models.Policy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

# --- Return Request CRUD ---

def create_return_request(db: Session, return_request: schemas.ReturnRequestCreate):
    """创建退货请求"""
    db_return = models.ReturnRequest(**return_request.dict())
    db.add(db_return)
    # 更新订单状态
    update_order_status(db, db_return.order_id, models.OrderStatusEnum.RETURN_REQUESTED)
    db.commit()
    db.refresh(db_return)
    return db_return

def get_return_request(db: Session, return_id: int):
    """根据ID获取退货请求"""
    return db.query(models.ReturnRequest).filter(models.ReturnRequest.id == return_id).first()

def check_return_eligibility(db: Session, order_number: str, product_sku: str):
    """检查商品是否符合退货条件"""
    order = get_order_by_number(db, order_number)
    product = get_product_by_sku(db, product_sku)
    policy = get_policy(db, models.PolicyTypeEnum.RETURN)

    if not order or not product or not policy:
        return {"is_eligible": False, "reason": "订单或商品信息未找到，或退货政策未配置。"}

    # 检查商品是否在订单中
    item_in_order = False
    for item in order.items:
        if item.product_id == product.id:
            item_in_order = True
            break
    if not item_in_order:
        return {"is_eligible": False, "reason": f"商品 (SKU: {product_sku}) 不在订单 {order_number} 中。"}

    # 简化的资格检查：基于订单日期和固定的退货窗口（例如30天）
    return_window_days = 30 # 示例：30天退货窗口
    if order.order_date + timedelta(days=return_window_days) < datetime.now(order.order_date.tzinfo):
         return {
            "is_eligible": False,
            "reason": f"已超过 {return_window_days} 天退货期限。",
            "policy_summary": policy.content[:200] + "..." # 显示政策摘要
         }

    return {
        "is_eligible": True,
        "reason": None,
        "policy_summary": policy.content[:200] + "..."
    }

# --- Feedback CRUD ---

def create_feedback(db: Session, feedback: schemas.FeedbackCreate):
    """创建用户反馈"""
    db_feedback = models.Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def get_feedback(db: Session, skip: int = 0, limit: int = 100):
    """获取反馈列表"""
    return db.query(models.Feedback).offset(skip).limit(limit).all()

# --- User CRUD ---

def get_user(db: Session, user_id: int):
    """根据ID获取用户"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    """根据邮箱获取用户"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """创建新用户"""
    # 在实际应用中，这里应该对密码进行哈希处理
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # hashed_password = pwd_context.hash(user.password)
    hashed_password = user.password + "_hashed" # 示例：使用真实的哈希库！
    db_user = models.User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Address CRUD ---

def create_address(db: Session, address: schemas.AddressCreate):
    """创建新地址"""
    db_address = models.Address(**address.dict())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def get_addresses_by_user(db: Session, user_id: int):
    """获取用户的所有地址"""
    return db.query(models.Address).filter(models.Address.user_id == user_id).all()

def get_address(db: Session, address_id: int):
    """根据ID获取地址"""
    return db.query(models.Address).filter(models.Address.id == address_id).first()
