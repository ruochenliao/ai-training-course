# Customer API module
from fastapi import APIRouter

from .customer import router

customer_router = APIRouter()
customer_router.include_router(router, tags=['会话管理'])

__all__ = ["customer_router"]
