from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Customer, CustomerAddress

router = APIRouter()


@router.get("/")
async def get_customers(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词")
):
    """获取客户列表"""
    query = Customer.filter(is_deleted=False)
    
    if keyword:
        query = query.filter(username__icontains=keyword)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    customers = await query.offset(offset).limit(size).order_by("-created_at")
    
    # 转换为字典格式
    items = []
    for customer in customers:
        item = {
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "phone": customer.phone,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "full_name": customer.full_name,
            "gender": customer.gender,
            "is_active": customer.is_active,
            "is_verified": customer.is_verified,
            "last_login": customer.last_login.isoformat() if customer.last_login else None,
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
            "created_at": customer.created_at.isoformat()
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{customer_id}")
async def get_customer(customer_id: int):
    """获取客户详情"""
    customer = await Customer.filter(
        id=customer_id,
        is_deleted=False
    ).prefetch_related("addresses", "orders").first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    return {
        "id": customer.id,
        "username": customer.username,
        "email": customer.email,
        "phone": customer.phone,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "full_name": customer.full_name,
        "avatar": customer.avatar,
        "birth_date": customer.birth_date.isoformat() if customer.birth_date else None,
        "gender": customer.gender,
        "is_active": customer.is_active,
        "is_verified": customer.is_verified,
        "last_login": customer.last_login.isoformat() if customer.last_login else None,
        "total_orders": customer.total_orders,
        "total_spent": float(customer.total_spent),
        "created_at": customer.created_at.isoformat(),
        "addresses": [
            {
                "id": addr.id,
                "name": addr.name,
                "phone": addr.phone,
                "province": addr.province,
                "city": addr.city,
                "district": addr.district,
                "address": addr.address,
                "postal_code": addr.postal_code,
                "is_default": addr.is_default
            } for addr in customer.addresses
        ]
    }


@router.get("/{customer_id}/orders/")
async def get_customer_orders(
    customer_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """获取客户订单列表"""
    # 先检查客户是否存在
    customer = await Customer.filter(id=customer_id, is_deleted=False).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    # 查询订单
    from app.models import Order
    query = Order.filter(customer_id=customer_id, is_deleted=False)
    
    total = await query.count()
    offset = (page - 1) * size
    orders = await query.offset(offset).limit(size).prefetch_related("items__product").order_by("-created_at")
    
    items = []
    for order in orders:
        item = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "shipping_name": order.shipping_name,
            "shipping_address": order.shipping_address,
            "tracking_number": order.tracking_number,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "created_at": order.created_at.isoformat(),
            "items_count": len(order.items),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price)
                } for item in order.items
            ]
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
        "customer": {
            "id": customer.id,
            "username": customer.username,
            "full_name": customer.full_name
        }
    }
