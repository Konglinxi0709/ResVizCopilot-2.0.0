"""
共享管理器
供所有路由模块使用，确保数据一致性
"""
from backend.database.database_manager import DatabaseManager
from backend.project_manager import ProjectManager

# 创建全局共享的数据库管理器实例
shared_database_manager = DatabaseManager()
shared_project_manager = ProjectManager(shared_database_manager)

# 导出实例
__all__ = ['shared_database_manager', 'shared_project_manager']
