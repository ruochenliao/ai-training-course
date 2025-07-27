from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Order, OrderItem, Customer, OrderStatus

router = APIRouter(tags=["orders"])


@router.get("/")
async def get_orders(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[OrderStatus] = Query(None, description="订单状态")
):
    """获取订单列表"""
    query = Order.filter(is_deleted=False)
    
    if customer_id:
        query = query.filter(customer_id=customer_id)
    
    if status:
        query = query.filter(status=status)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    orders = await query.offset(offset).limit(size).prefetch_related("customer", "items__product").order_by("-created_at")
    
    # 转换为字典格式
    items = []
    for order in orders:
        item = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "subtotal": float(order.subtotal),
            "shipping_fee": float(order.shipping_fee),
            "discount_amount": float(order.discount_amount),
            "total_amount": float(order.total_amount),
            "shipping_name": order.shipping_name,
            "shipping_phone": order.shipping_phone,
            "shipping_address": order.shipping_address,
            "tracking_number": order.tracking_number,
            "shipping_company": order.shipping_company,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "created_at": order.created_at.isoformat(),
            "customer": {
                "id": order.customer.id,
                "username": order.customer.username,
                "email": order.customer.email,
                "phone": order.customer.phone
            } if order.customer else None,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_sku": item.product_sku,
                    "price": float(item.price),
                    "quantity": item.quantity,
                    "total_price": float(item.total_price),
                    "product": {
                        "id": item.product.id,
                        "name": item.product.name
                    } if item.product else None
                } for item in order.items
            ]
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{order_id}")
async def get_order(order_id: int):
    """获取订单详情"""
    order = await Order.filter(
        id=order_id,
        is_deleted=False
    ).prefetch_related("customer", "items__product").first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "subtotal": float(order.subtotal),
        "shipping_fee": float(order.shipping_fee),
        "discount_amount": float(order.discount_amount),
        "total_amount": float(order.total_amount),
        "shipping_name": order.shipping_name,
        "shipping_phone": order.shipping_phone,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "shipping_company": order.shipping_company,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "customer": {
            "id": order.customer.id,
            "username": order.customer.username,
            "email": order.customer.email,
            "phone": order.customer.phone,
            "full_name": order.customer.full_name
        } if order.customer else None,
        "items": [
            {
                "id": item.id,
                "product_name": item.product_name,
                "product_sku": item.product_sku,
                "price": float(item.price),
                "quantity": item.quantity,
                "total_price": float(item.total_price),
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "price": float(item.product.price),
                    "stock": item.product.stock
                } if item.product else None
            } for item in order.items
        ]
    }


@router.get("/number/{order_number}")
async def get_order_by_number(order_number: str):
    """根据订单号查询订单"""
    order = await Order.filter(
        order_number=order_number,
        is_deleted=False
    ).prefetch_related("customer", "items__product").first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "subtotal": float(order.subtotal),
        "shipping_fee": float(order.shipping_fee),
        "discount_amount": float(order.discount_amount),
        "total_amount": float(order.total_amount),
        "shipping_name": order.shipping_name,
        "shipping_phone": order.shipping_phone,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "shipping_company": order.shipping_company,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "customer": {
            "id": order.customer.id,
            "username": order.customer.username,
            "phone": order.customer.phone,
            "full_name": order.customer.full_name
        } if order.customer else None,
        "items": [
            {
                "id": item.id,
                "product_name": item.product_name,
                "product_sku": item.product_sku,
                "price": float(item.price),
                "quantity": item.quantity,
                "total_price": float(item.total_price)
            } for item in order.items
        ]
    }
