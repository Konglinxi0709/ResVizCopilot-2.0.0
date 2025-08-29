"""
路由处理模块
"""

from .agents import router as agents_router
from .test_endpoints import router as test_router

__all__ = ["agents_router", "test_router"]

