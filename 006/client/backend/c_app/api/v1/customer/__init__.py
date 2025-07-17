from fastapi import APIRouter
from .customer import router

customer_router = APIRouter()
customer_router.include_router(router, tags=["智能客服"])

__all__ = ["customer_router"]