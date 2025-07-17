from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Cart, CartItem, Customer, Product

router = APIRouter()


@router.get("/")
async def get_carts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    customer_id: Optional[int] = Query(None, description="客户ID")
):
    """获取购物车列表"""
    query = Cart.filter(is_deleted=False)
    
    if customer_id:
        query = query.filter(customer_id=customer_id)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    carts = await query.offset(offset).limit(size).prefetch_related("customer", "items__product").order_by("-created_at")
    
    # 转换为字典格式
    items = []
    for cart in carts:
        # 计算购物车统计信息
        total_quantity = sum(item.quantity for item in cart.items)
        total_amount = sum(item.subtotal for item in cart.items)
        
        item = {
            "id": cart.id,
            "session_id": cart.session_id,
            "created_at": cart.created_at.isoformat(),
            "customer": {
                "id": cart.customer.id,
                "username": cart.customer.username,
                "email": cart.customer.email
            } if cart.customer else None,
            "items": [
                {
                    "id": cart_item.id,
                    "quantity": cart_item.quantity,
                    "subtotal": float(cart_item.subtotal),
                    "product": {
                        "id": cart_item.product.id,
                        "name": cart_item.product.name,
                        "price": float(cart_item.product.price),
                        "stock": cart_item.product.stock,
                        "is_in_stock": cart_item.product.is_in_stock
                    } if cart_item.product else None
                } for cart_item in cart.items
            ],
            "total_quantity": total_quantity,
            "total_amount": float(total_amount)
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{cart_id}")
async def get_cart(cart_id: int):
    """获取购物车详情"""
    cart = await Cart.filter(
        id=cart_id,
        is_deleted=False
    ).prefetch_related("customer", "items__product").first()

    if not cart:
        raise HTTPException(status_code=404, detail="购物车不存在")

    # 计算购物车统计信息
    total_quantity = sum(item.quantity for item in cart.items)
    total_amount = sum(item.subtotal for item in cart.items)
    available_items = sum(1 for item in cart.items if item.product and item.product.is_in_stock)

    return {
        "id": cart.id,
        "session_id": cart.session_id,
        "created_at": cart.created_at.isoformat(),
        "updated_at": cart.updated_at.isoformat(),
        "customer": {
            "id": cart.customer.id,
            "username": cart.customer.username,
            "email": cart.customer.email,
            "phone": cart.customer.phone,
            "full_name": cart.customer.full_name
        } if cart.customer else None,
        "items": [
            {
                "id": cart_item.id,
                "quantity": cart_item.quantity,
                "subtotal": float(cart_item.subtotal),
                "is_available": cart_item.product.is_in_stock if cart_item.product else False,
                "product": {
                    "id": cart_item.product.id,
                    "name": cart_item.product.name,
                    "sku": cart_item.product.sku,
                    "price": float(cart_item.product.price),
                    "original_price": float(cart_item.product.original_price) if cart_item.product.original_price else None,
                    "stock": cart_item.product.stock,
                    "brand": cart_item.product.brand,
                    "is_in_stock": cart_item.product.is_in_stock,
                    "is_active": cart_item.product.is_active
                } if cart_item.product else None
            } for cart_item in cart.items
        ],
        "total_quantity": total_quantity,
        "total_amount": float(total_amount),
        "available_items": available_items,
        "unavailable_items": len(cart.items) - available_items
    }


@router.get("/customer/{customer_id}")
async def get_customer_cart(customer_id: int):
    """获取客户的购物车"""
    # 先检查客户是否存在
    customer = await Customer.filter(id=customer_id, is_deleted=False).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    
    # 查找客户的购物车
    cart = await Cart.filter(
        customer_id=customer_id,
        is_deleted=False
    ).prefetch_related("items__product").first()
    
    if not cart:
        # 如果没有购物车，创建一个新的
        cart = await Cart.create(customer=customer)
        await cart.fetch_related("items__product")
    
    # 计算购物车统计信息
    total_quantity = sum(item.quantity for item in cart.items)
    total_amount = sum(item.subtotal for item in cart.items)
    available_items = sum(1 for item in cart.items if item.product and item.product.is_in_stock)

    return {
        "id": cart.id,
        "customer": {
            "id": customer.id,
            "username": customer.username,
            "full_name": customer.full_name
        },
        "items": [
            {
                "id": cart_item.id,
                "quantity": cart_item.quantity,
                "subtotal": float(cart_item.subtotal),
                "is_available": cart_item.product.is_in_stock if cart_item.product else False,
                "product": {
                    "id": cart_item.product.id,
                    "name": cart_item.product.name,
                    "sku": cart_item.product.sku,
                    "price": float(cart_item.product.price),
                    "stock": cart_item.product.stock,
                    "brand": cart_item.product.brand,
                    "is_in_stock": cart_item.product.is_in_stock
                } if cart_item.product else None
            } for cart_item in cart.items
        ],
        "summary": {
            "total_items": len(cart.items),
            "total_quantity": total_quantity,
            "total_amount": float(total_amount),
            "available_items": available_items,
            "unavailable_items": len(cart.items) - available_items
        }
    }
