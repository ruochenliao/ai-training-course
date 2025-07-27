from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Promotion, Coupon, CouponUsage

router = APIRouter(tags=["promotions"])


@router.get("/")
async def get_promotions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用")
):
    """获取促销活动列表"""
    query = Promotion.filter(is_deleted=False)
    
    if is_active is not None:
        query = query.filter(is_active=is_active)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    promotions = await query.offset(offset).limit(size).order_by("-created_at")
    
    # 转换为字典格式
    items = []
    for promotion in promotions:
        item = {
            "id": promotion.id,
            "name": promotion.name,
            "description": promotion.description,
            "type": promotion.type,
            "discount_value": float(promotion.discount_value),
            "min_order_amount": float(promotion.min_order_amount),
            "max_discount_amount": float(promotion.max_discount_amount) if promotion.max_discount_amount else None,
            "start_date": promotion.start_date.isoformat(),
            "end_date": promotion.end_date.isoformat(),
            "is_active": promotion.is_active,
            "usage_limit": promotion.usage_limit,
            "used_count": promotion.used_count,
            "is_available": promotion.is_available,
            "created_at": promotion.created_at.isoformat()
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{promotion_id}")
async def get_promotion(promotion_id: int):
    """获取促销活动详情"""
    promotion = await Promotion.filter(
        id=promotion_id,
        is_deleted=False
    ).first()

    if not promotion:
        raise HTTPException(status_code=404, detail="促销活动不存在")

    return {
        "id": promotion.id,
        "name": promotion.name,
        "description": promotion.description,
        "type": promotion.type,
        "discount_value": float(promotion.discount_value),
        "min_order_amount": float(promotion.min_order_amount),
        "max_discount_amount": float(promotion.max_discount_amount) if promotion.max_discount_amount else None,
        "start_date": promotion.start_date.isoformat(),
        "end_date": promotion.end_date.isoformat(),
        "is_active": promotion.is_active,
        "usage_limit": promotion.usage_limit,
        "used_count": promotion.used_count,
        "is_available": promotion.is_available,
        "created_at": promotion.created_at.isoformat(),
        "updated_at": promotion.updated_at.isoformat()
    }


@router.get("/coupons/")
async def get_coupons(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    code: Optional[str] = Query(None, description="优惠券代码")
):
    """获取优惠券列表"""
    query = Coupon.filter(is_deleted=False)
    
    if is_active is not None:
        query = query.filter(is_active=is_active)
    
    if code:
        query = query.filter(code=code)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    coupons = await query.offset(offset).limit(size).order_by("-created_at")
    
    # 转换为字典格式
    items = []
    for coupon in coupons:
        item = {
            "id": coupon.id,
            "code": coupon.code,
            "name": coupon.name,
            "description": coupon.description,
            "type": coupon.type,
            "discount_value": float(coupon.discount_value),
            "min_order_amount": float(coupon.min_order_amount),
            "max_discount_amount": float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
            "start_date": coupon.start_date.isoformat(),
            "end_date": coupon.end_date.isoformat(),
            "is_active": coupon.is_active,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "user_limit": coupon.user_limit,
            "is_available": coupon.is_available,
            "created_at": coupon.created_at.isoformat()
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/coupons/{coupon_code}")
async def get_coupon_by_code(coupon_code: str):
    """根据优惠券代码获取优惠券信息"""
    coupon = await Coupon.filter(
        code=coupon_code,
        is_deleted=False
    ).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")

    return {
        "id": coupon.id,
        "code": coupon.code,
        "name": coupon.name,
        "description": coupon.description,
        "type": coupon.type,
        "discount_value": float(coupon.discount_value),
        "min_order_amount": float(coupon.min_order_amount),
        "max_discount_amount": float(coupon.max_discount_amount) if coupon.max_discount_amount else None,
        "start_date": coupon.start_date.isoformat(),
        "end_date": coupon.end_date.isoformat(),
        "is_active": coupon.is_active,
        "usage_limit": coupon.usage_limit,
        "used_count": coupon.used_count,
        "user_limit": coupon.user_limit,
        "is_available": coupon.is_available,
        "created_at": coupon.created_at.isoformat()
    }


@router.get("/active/")
async def get_active_promotions():
    """获取当前有效的促销活动"""
    now = datetime.now()
    
    # 获取有效的促销活动
    promotions = await Promotion.filter(
        is_deleted=False,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).all()
    
    # 获取有效的优惠券
    coupons = await Coupon.filter(
        is_deleted=False,
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).all()
    
    return {
        "promotions": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "type": p.type,
                "discount_value": float(p.discount_value),
                "min_order_amount": float(p.min_order_amount)
            } for p in promotions
        ],
        "coupons": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "description": c.description,
                "type": c.type,
                "discount_value": float(c.discount_value),
                "min_order_amount": float(c.min_order_amount)
            } for c in coupons
        ]
    }
