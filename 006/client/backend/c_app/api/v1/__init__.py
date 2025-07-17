from fastapi import APIRouter

from c_app.api.v1.customer import customer
from c_app.api.v1.text2sql import text2sql

v1_router = APIRouter()
v1_router.include_router(customer.router, prefix="/chat", tags=["chat"])
v1_router.include_router(text2sql.router, prefix="/text2sql", tags=["text2sql"])
