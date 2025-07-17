from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from c_app.api import api_router
from c_app.core.config import settings
app = FastAPI(
    title="但问智能体API",
    description="但问智能体综合应用平台后端API",
    version="0.1.0",
)

# 设置CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "但问智能体API服务正常运行"}

if __name__ == "__main__":
    import uvicorn
    print("启动服务器，WebSocket支持已启用...")
    uvicorn.run("c_app.main:c_app", host="0.0.0.0", port=8000, reload=True, ws="websockets")