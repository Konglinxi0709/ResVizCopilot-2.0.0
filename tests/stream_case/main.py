"""
FastAPI应用入口
流式传输技术验证案例主应用
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.agents import router as agents_router
from routers.test_endpoints import router as test_router
from utils.logger import logger

# 创建FastAPI应用
app = FastAPI(
    title="流式传输技术验证案例",
    description="验证智能体协程与SSE传输解耦的架构设计",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(agents_router)
app.include_router(test_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "流式传输技术验证案例",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/healthz")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info("启动流式传输技术验证案例")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
