from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Product, Category, ProductImage

router = APIRouter(tags=["products"])


@router.get("/")
async def get_products(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_featured: Optional[bool] = Query(None, description="是否推荐商品")
):
    """获取商品列表"""
    query = Product.filter(is_deleted=False, is_active=True)
    
    if category_id:
        query = query.filter(category_id=category_id)
    
    if keyword:
        query = query.filter(name__icontains=keyword)
    
    if is_featured is not None:
        query = query.filter(is_featured=is_featured)
    
    # 计算总数
    total = await query.count()
    
    # 分页查询
    offset = (page - 1) * size
    products = await query.offset(offset).limit(size).prefetch_related("category", "images")
    
    # 转换为字典格式
    items = []
    for product in products:
        item = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "short_description": product.short_description,
            "sku": product.sku,
            "price": float(product.price),
            "original_price": float(product.original_price) if product.original_price else None,
            "stock": product.stock,
            "brand": product.brand,
            "tags": product.tags,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "rating": float(product.rating),
            "review_count": product.review_count,
            "sales_count": product.sales_count,
            "view_count": product.view_count,
            "is_in_stock": product.is_in_stock,
            "is_low_stock": product.is_low_stock,
            "category": {
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None,
            "images": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "alt_text": img.alt_text,
                    "is_primary": img.is_primary
                } for img in product.images
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


@router.get("/{product_id}")
async def get_product(product_id: int):
    """获取商品详情"""
    product = await Product.filter(
        id=product_id,
        is_deleted=False,
        is_active=True
    ).prefetch_related("category", "images").first()

    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 增加浏览量
    await Product.filter(id=product_id).update(view_count=product.view_count + 1)

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "short_description": product.short_description,
        "sku": product.sku,
        "price": float(product.price),
        "original_price": float(product.original_price) if product.original_price else None,
        "stock": product.stock,
        "weight": float(product.weight) if product.weight else None,
        "dimensions": product.dimensions,
        "brand": product.brand,
        "tags": product.tags,
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "rating": float(product.rating),
        "review_count": product.review_count,
        "sales_count": product.sales_count,
        "view_count": product.view_count,
        "is_in_stock": product.is_in_stock,
        "is_low_stock": product.is_low_stock,
        "category": {
            "id": product.category.id,
            "name": product.category.name,
            "description": product.category.description
        } if product.category else None,
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "alt_text": img.alt_text,
                "sort_order": img.sort_order,
                "is_primary": img.is_primary
            } for img in product.images
        ]
    }


@router.get("/categories/")
async def get_categories():
    """获取商品分类"""
    categories = await Category.filter(is_deleted=False, is_active=True).order_by("sort_order")
    
    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "sort_order": category.sort_order,
            "is_active": category.is_active
        } for category in categories
    ]


@router.get("/search/")
async def search_products(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """搜索商品"""
    query = Product.filter(
        is_deleted=False,
        is_active=True,
        name__icontains=keyword
    )
    
    total = await query.count()
    offset = (page - 1) * size
    products = await query.offset(offset).limit(size).prefetch_related("category")
    
    items = []
    for product in products:
        item = {
            "id": product.id,
            "name": product.name,
            "short_description": product.short_description,
            "sku": product.sku,
            "price": float(product.price),
            "original_price": float(product.original_price) if product.original_price else None,
            "stock": product.stock,
            "brand": product.brand,
            "rating": float(product.rating),
            "sales_count": product.sales_count,
            "is_in_stock": product.is_in_stock,
            "category": {
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
        "keyword": keyword
    }
