import uvicorn
import platform
import os
from uvicorn.config import LOGGING_CONFIG

if __name__ == "__main__":
    # 修改默认日志配置
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

    # 检测操作系统，在 Windows 上不使用多进程模式
    is_windows = platform.system().lower() == "windows"

    # 在 Windows 上使用单进程模式，在其他系统上使用多进程模式
    workers = 1 if is_windows else os.cpu_count() or 4
    reload = True if is_windows else False

    print(f"Running on {platform.system()} with {workers} worker(s) and reload={reload}")

    # 增加超时时间以支持大文件上传
    uvicorn.run(
        "a_app:app",
        host="0.0.0.0",
        port=9999,
        reload=reload,  # Windows 上使用 reload，其他系统不使用
        log_config=LOGGING_CONFIG,
        timeout_keep_alive=300,  # 5分钟连接保持时间
        timeout_graceful_shutdown=300,  # 5分钟优雅关闭时间
        limit_concurrency=100,  # 并发连接数
        workers=workers,  # 根据操作系统决定工作进程数
    )
