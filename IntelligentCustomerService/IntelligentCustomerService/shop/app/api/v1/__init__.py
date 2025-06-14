from fastapi import APIRouter

from .cart import router as cart_router
from .customers import router as customers_router
from .orders import router as orders_router
from .products import router as products_router
from .promotions import router as promotions_router

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(cart_router, prefix="/cart", tags=["cart"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
api_router.include_router(promotions_router, prefix="/promotions", tags=["promotions"])
