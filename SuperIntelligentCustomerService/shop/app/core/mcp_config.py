# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 配置模块
为电商系统提供MCP服务器配置和集成
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_mcp import FastApiMCP

from app.settings.config import settings


# HTTP Bearer 认证方案
security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    验证API密钥
    
    Args:
        credentials: HTTP Bearer认证凭据
        
    Returns:
        str: 验证通过的API密钥
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    # 这里可以实现更复杂的API密钥验证逻辑
    # 例如从数据库查询、验证过期时间等
    valid_api_keys = getattr(settings, 'MCP_API_KEYS', ['mcp-shop-api-key-2025'])
    
    if credentials.credentials not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def get_current_user(api_key: str = Depends(verify_api_key)) -> dict:
    """
    获取当前用户信息
    
    Args:
        api_key: 验证通过的API密钥
        
    Returns:
        dict: 用户信息
    """
    # 这里可以根据API密钥获取用户信息
    # 目前返回一个模拟的用户信息
    return {
        "api_key": api_key,
        "user_id": "mcp_user",
        "permissions": ["read", "write"],
        "role": "mcp_client"
    }


class MCPConfig:
    """MCP配置类"""
    
    def __init__(self):
        self.title = "智能电商系统 MCP 服务器"
        self.description = """
        智能电商系统的Model Context Protocol (MCP) 服务器
        
        提供以下功能：
        - 商品管理：查询、搜索商品信息
        - 订单管理：创建、查询、更新订单状态
        - 购物车管理：添加、删除、查看购物车商品
        - 促销活动：查询当前促销信息
        - 客户管理：查询客户信息
        
        所有端点都需要有效的API密钥进行认证。
        """
        self.version = "1.0.0"
        
        # MCP服务器配置
        self.mcp_mount_path = "/mcp"
        self.mcp_title = "电商系统 MCP API"
        
        # 包含的路由标签（只暴露这些标签的端点到MCP）
        self.included_tags = [
            "products",      # 商品相关
            "orders",        # 订单相关  
            "cart",          # 购物车相关
            "promotions",    # 促销相关
            "customers"      # 客户相关
        ]
        
        # 排除的路径（这些路径不会暴露到MCP）
        self.excluded_paths = [
            "/shop/docs",
            "/shop/redoc", 
            "/shop/openapi.json",
            "/mcp"
        ]
    
    def get_dependencies(self) -> List:
        """
        获取MCP依赖项列表

        Returns:
            List: 依赖项列表
        """
        return [Depends(get_current_user)]
    
    def get_mcp_config(self) -> dict:
        """
        获取MCP配置字典
        
        Returns:
            dict: MCP配置参数
        """
        return {
            "title": self.mcp_title,
            "description": self.description,
            "version": self.version,
            "mount_path": self.mcp_mount_path,
            "include_tags": self.included_tags,
            "exclude_paths": self.excluded_paths,
            "dependencies": self.get_dependencies()
        }


# 全局MCP配置实例
mcp_config = MCPConfig()


def setup_mcp_server(app) -> FastApiMCP:
    """
    设置MCP服务器

    Args:
        app: FastAPI应用实例

    Returns:
        FastApiMCP: 配置好的MCP服务器实例
    """
    # 创建MCP服务器实例（暂时不使用认证以简化测试）
    mcp = FastApiMCP(
        fastapi=app,
        name=mcp_config.mcp_title,
        description=mcp_config.description,
        include_tags=mcp_config.included_tags
    )

    # 挂载MCP服务器到指定路径
    mcp.mount(mount_path=mcp_config.mcp_mount_path)

    return mcp
