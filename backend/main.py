"""
ResVizCopilot 2.0 后端主应用
集成研究树数据库和智能体流式传输系统
启动：
export PYTHONPATH=/root/autodl-tmp/ResVizCopilot-2.0.0:$PYTHONPATH && nohup python -m uvicorn backend.main:app --host 127.0.0.1 --port 8008 --reload > backend/fastapi.log 2>&1 &
disown
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.research_tree import router as research_tree_router
from backend.routers.agents import router as agents_router
from backend.routers.projects import router as projects_router
from backend.config import settings
from backend.utils.logger import logger

# 创建FastAPI应用
app = FastAPI(
    title="ResVizCopilot 2.0 Backend",
    description="科研智能体项目后端API，支持研究树管理、智能体流式交互和工程管理",
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
app.include_router(research_tree_router, prefix="")
app.include_router(agents_router, prefix="")
app.include_router(projects_router, prefix="")



# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("ResVizCopilot 2.0 后端服务启动")
    logger.info(f"服务地址: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    
# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("ResVizCopilot 2.0 后端服务关闭")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ResVizCopilot 2.0 Backend API",
        "version": "2.0.0",
        "features": [
            "研究树数据库管理",
            "智能体流式交互", 
            "SSE实时传输",
            "XML解析验证",
            "重试机制",
            "快照管理"
        ],
        "endpoints": {
            "research_tree": "/research-tree/*",
            "agents": "/agents/*",
            "health": "/healthz"
        }
    }

@app.get("/healthz")
def healthz():
    """健康检查"""
    return {
        "status": "ok",
        "service": "resviz_copilot_backend",
        "version": "2.0.0"
    }



