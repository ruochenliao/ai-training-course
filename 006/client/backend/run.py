import uvicorn

if __name__ == "__main__":
    # 使用uvicorn启动FastAPI应用
    uvicorn.run(
        "c_app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    ) 