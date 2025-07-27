import os
import sys

import uvicorn

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings.config import settings

if __name__ == "__main__":
    print(f"启动电商系统服务...")
    print(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    print(f"API文档: http://{settings.HOST}:{settings.PORT}/shop/docs")
    print(f"数据库: {settings.DATABASE_URL}")
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # 禁用自动重载以便测试
        log_level="info"
    )
