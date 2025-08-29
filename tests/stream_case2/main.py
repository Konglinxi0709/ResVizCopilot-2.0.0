"""
Stream Case 2 主应用
优化后的流式传输技术验证案例
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.agents import router as agents_router
from routers.test_endpoints import router as test_router
from utils.logger import logger

# 创建FastAPI应用
app = FastAPI(
    title="Stream Case 2 - 优化版流式传输验证",
    description="基于ProjectManager架构的智能体流式传输技术验证案例",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
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
        "message": "Stream Case 2 - 优化版流式传输验证案例",
        "version": "2.0.0",
        "features": [
            "ProjectManager统一消息管理",
            "智能体抽象基类架构",
            "XML解析和Pydantic验证",
            "回调函数式patch发布",
            "指数回退重试机制",
            "快照对象前端替换"
        ],
        "endpoints": {
            "agents": "/agents/messages",
            "history": "/agents/messages/history",
            "continue": "/agents/messages/continue/{message_id}",
            "stop": "/agents/messages/stop",
            "test": "/test/*"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "stream_case2"}


if __name__ == "__main__":
    logger.info("启动Stream Case 2应用")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

