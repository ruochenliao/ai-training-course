from fastapi import APIRouter
from .text2sql import router

text2sql_router = APIRouter()
text2sql_router.include_router(router, tags=["Text2SQL"])

__all__ = ["text2sql_router"]