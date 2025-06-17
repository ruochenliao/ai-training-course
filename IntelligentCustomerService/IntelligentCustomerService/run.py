import uvicorn
from uvicorn.config import LOGGING_CONFIG

def init_memory_service():
    """初始化记忆服务"""
    try:
        from app.utils.init_memory_db import init_memory_database
        print("🧠 正在初始化记忆服务...")
        init_memory_database()
        print("✅ 记忆服务初始化完成")
    except Exception as e:
        print(f"⚠️ 记忆服务初始化失败: {e}")
        print("   系统将继续运行，但记忆功能可能不可用")

if __name__ == "__main__":
    # 初始化记忆服务
    init_memory_service()

    # 修改默认日志配置
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

    print("🚀 启动智能客服系统...")
    uvicorn.run("app:app", host="0.0.0.0", port=9999, reload=True, log_config=LOGGING_CONFIG)
