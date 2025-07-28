# -*- coding: utf-8 -*-
"""
MCP API模块
"""
from fastapi import APIRouter

from .mcp_api import router

mcp_api_router = APIRouter()
mcp_api_router.include_router(router, tags=["mcp模块"])

__all__ = ["mcp_api_router"]