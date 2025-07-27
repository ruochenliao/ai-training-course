from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    APP_TITLE: str = "智能电商系统"
    APP_DESCRIPTION: str = "基于 FastAPI 构建的现代电商平台，专为智能客服场景设计"
    VERSION: str = "1.0.0"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite://shop.db"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # 电商配置
    SHOP_NAME: str = "智能电商"
    SHOP_DESCRIPTION: str = "您的智能购物助手"
    DEFAULT_CURRENCY: str = "CNY"
    
    # AI配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    DEFAULT_MODEL: str = "deepseek-chat"

    # MCP配置
    MCP_ENABLED: bool = True
    MCP_API_KEYS: list = ["mcp-shop-api-key-2025", "demo-api-key"]
    MCP_MOUNT_PATH: str = "/mcp"
    MCP_TITLE: str = "智能电商系统 MCP 服务器"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
