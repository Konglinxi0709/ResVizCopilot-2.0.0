"""
项目管理器
负责数据持久化，管理工程的保存、加载、版本控制等
"""
import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.database.database_manager import DatabaseManager
from backend.message.message_manager import MessageManager
from backend.utils.logger import logger

class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ProjectManager:
    """
    项目管理器
    
    核心职责：
    1. 管理工程的保存和加载
    2. 在程序启动时自动恢复数据
    3. 提供工程级别的管理接口
    4. 确保数据一致性
    """
    
    def __init__(self):
        """初始化项目管理器"""
        self.projects_dir = Path(__file__).parent / "data" / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前工程信息
        self.current_project_name: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        
        # 创建共享的数据库管理器和消息管理器实例
        self.database_manager = DatabaseManager()
        self.message_manager = MessageManager(self.database_manager)
        
        # 自动恢复数据
        self._auto_restore()
    
    def _auto_restore(self) -> None:
        """程序启动时自动恢复数据"""
        try:
            # 查找最新的存档文件
            latest_project = self._find_latest_project()
            
            if latest_project:
                # 加载最新存档
                self.load_project(latest_project)
                logger.info(f"自动恢复工程: {latest_project}")
            else:
                # 创建新的空存档
                self.create_new_project("未命名")
                logger.info("创建新工程: 未命名")
                
        except Exception as e:
            logger.error(f"自动恢复数据失败: {e}")
            # 创建新的空存档作为后备
            self.create_new_project("未命名")
    
    def _find_latest_project(self) -> Optional[str]:
        """查找更新时间最新的工程"""
        project_files = glob.glob(str(self.projects_dir / "*.json"))
        
        if not project_files:
            return None
        
        latest_file = max(project_files, key=os.path.getmtime)
        return Path(latest_file).stem
    
    def _get_project_file_path(self, project_name: str, check_file_name_conflict: bool = True) -> Path:
        """获取工程文件路径，自动处理文件名冲突"""
        base_path = self.projects_dir / f"{project_name}.json"
        
        if not base_path.exists() or not check_file_name_conflict:
            return base_path
        
        # 处理文件名冲突，添加(1)、(2)等后缀
        counter = 1
        while True:
            new_path = self.projects_dir / f"{project_name}({counter}).json"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _save_project_data(self, project_name: str, check_file_name_conflict: bool = True) -> str:
        """保存工程数据到文件，返回实际保存的文件名（不含扩展名）"""
        try:
            # 获取文件路径（处理冲突）
            file_path = self._get_project_file_path(project_name, check_file_name_conflict)
            
            # 获取实际的文件名（不含扩展名）
            actual_project_name = file_path.stem
            
            # 准备保存数据，使用实际的文件名
            project_data = {
                "project_name": actual_project_name,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": datetime.now().isoformat(),
                "messages": {msg_id: msg.model_dump() for msg_id, msg in self.message_manager.messages.items()},
                "message_order": self.message_manager.message_order,
                "snapshot_map": {snapshot_id: snapshot.model_dump() for snapshot_id, snapshot in self.database_manager.snapshot_map.items()},
                "current_snapshot_id": self.database_manager.current_snapshot_id
            }
            
            # 保存到文件，使用自定义编码器
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
            
            # 更新当前工程信息，使用实际的文件名
            self.current_project_name = actual_project_name
            if not self.created_at:
                self.created_at = datetime.now()
            self.updated_at = datetime.now()
            
            logger.info(f"工程保存成功: {file_path}")
            
            return actual_project_name
            
        except Exception as e:
            logger.error(f"保存工程失败: {e}")
            raise
    
    def _load_project_data(self, project_name: str) -> None:
        """从文件加载工程数据"""
        try:
            file_path = self.projects_dir / f"{project_name}.json"
            
            if not file_path.exists():
                raise FileNotFoundError(f"工程文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 验证必要字段
            required_fields = ["messages", "message_order", "snapshot_map", "current_snapshot_id"]
            for field in required_fields:
                if field not in project_data:
                    raise ValueError(f"工程文件缺少必要字段: {field}")
            
            # 恢复消息管理器状态
            self.message_manager.messages.clear()
            self.message_manager.message_order.clear()
            
            # 恢复消息
            for msg_id, msg_data in project_data["messages"].items():
                from backend.message.schemas.message_models import Message
                msg = Message(**msg_data)
                self.message_manager.messages[msg_id] = msg
            
            # 恢复消息顺序
            self.message_manager.message_order = project_data["message_order"]
            
            # 恢复数据库管理器状态
            self.database_manager.snapshot_map.clear()
            
            # 恢复快照
            for snapshot_id, snapshot_data in project_data["snapshot_map"].items():
                from backend.database.schemas.research_tree import Snapshot
                snapshot = Snapshot(**snapshot_data)
                self.database_manager.snapshot_map[snapshot_id] = snapshot
            
            # 设置当前快照
            self.database_manager.current_snapshot_id = project_data["current_snapshot_id"]
            
            # 更新工程信息
            self.current_project_name = project_name
            self.created_at = datetime.fromisoformat(project_data["created_at"]) if project_data["created_at"] else None
            self.updated_at = datetime.fromisoformat(project_data["updated_at"]) if project_data["updated_at"] else None
            
            logger.info(f"工程加载成功: {project_name}")
            
        except Exception as e:
            logger.error(f"加载工程失败: {e}")
            raise
    
    def create_new_project(self, project_name: str) -> Dict[str, Any]:
        """创建新工程"""
        try:
            # 如果当前工程非空，先自动保存
            if self.current_project_name and self._has_data():
                self.save_current_project()
            
            # 清空当前数据
            self._clear_current_data()
            
            # 创建新工程
            self.current_project_name = project_name
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            
            return {
                "success": True,
                "message": f"新工程创建成功: {project_name}",
                "project_name": project_name,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"创建新工程失败: {e}")
            return {
                "success": False,
                "message": f"创建新工程失败: {str(e)}"
            }
    
    def save_current_project(self) -> Dict[str, Any]:
        """保存当前工程"""
        try:
            if not self.current_project_name:
                return {
                    "success": False,
                    "message": "没有当前工程可保存"
                }
            
            saved_project_name = self._save_project_data(self.current_project_name, check_file_name_conflict=False)
            
            return {
                "success": True,
                "message": f"工程保存成功: {self.current_project_name}",
                "project_name": saved_project_name,
                "updated_at": self.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"保存当前工程失败: {e}")
            return {
                "success": False,
                "message": f"保存当前工程失败: {str(e)}"
            }
    
    def save_as_current_project(self, new_project_name: str) -> Dict[str, Any]:
        """将当前工程另存为"""
        try:
            if not self.current_project_name:
                return {
                    "success": False,
                    "message": "没有当前工程可另存为"
                }
            
            # 保存到新名称
            saved_project_name = self._save_project_data(new_project_name)
            
            return {
                "success": True,
                "message": f"工程另存为成功: {new_project_name}",
                "project_name": saved_project_name,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"另存为工程失败: {e}")
            return {
                "success": False,
                "message": f"另存为工程失败: {str(e)}"
            }
    
    def load_project(self, project_name: str) -> Dict[str, Any]:
        """加载指定工程"""
        try:
            self._load_project_data(project_name)
            
            return {
                "success": True,
                "message": f"工程加载成功: {project_name}",
                "project_name": project_name,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"加载工程失败: {e}")
            return {
                "success": False,
                "message": f"加载工程失败: {str(e)}"
            }
    
    def list_projects(self) -> Dict[str, Any]:
        """获取工程列表"""
        try:
            project_files = glob.glob(str(self.projects_dir / "*.json"))
            projects = []
            
            for file_path in project_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    projects.append({
                        "project_name": Path(file_path).stem,
                        "created_at": project_data.get("created_at"),
                        "updated_at": project_data.get("updated_at"),
                        "file_path": file_path
                    })
                except Exception as e:
                    logger.warning(f"读取工程文件失败: {file_path}, 错误: {e}")
                    continue
            
            # 按更新时间排序
            projects.sort(key=lambda x: x["updated_at"] or "", reverse=True)
            
            return {
                "success": True,
                "message": f"获取工程列表成功，共 {len(projects)} 个工程",
                "projects": projects
            }
            
        except Exception as e:
            logger.error(f"获取工程列表失败: {e}")
            return {
                "success": False,
                "message": f"获取工程列表失败: {str(e)}"
            }
    
    def delete_project(self, project_name: str) -> Dict[str, Any]:
        """删除指定工程"""
        try:
            file_path = self.projects_dir / f"{project_name}.json"
            
            if not file_path.exists():
                return {
                    "success": False,
                    "message": f"工程不存在: {project_name}"
                }
            
            # 如果删除的是当前工程，清空当前状态
            if self.current_project_name == project_name:
                self._clear_current_data()
            
            # 删除文件
            file_path.unlink()
            
            return {
                "success": True,
                "message": f"工程删除成功: {project_name}"
            }
            
        except Exception as e:
            logger.error(f"删除工程失败: {e}")
            return {
                "success": False,
                "message": f"删除工程失败: {str(e)}"
            }
    
    def _has_data(self) -> bool:
        """检查当前是否有数据"""
        return (len(self.message_manager.messages) > 0 or 
                len(self.database_manager.snapshot_map) > 1)  # 除了初始空快照
    
    def _clear_current_data(self) -> None:
        """清空当前数据"""
        self.message_manager.messages.clear()
        self.message_manager.message_order.clear()
        self.database_manager.snapshot_map.clear()
        self.database_manager._init_empty_snapshot()
    
    def get_current_project_info(self) -> Dict[str, Any]:
        """获取当前工程信息"""
        return {
            "project_name": self.current_project_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.message_manager.messages),
            "snapshot_count": len(self.database_manager.snapshot_map)
        }

# 创建全局唯一的项目管理器实例
shared_project_manager = ProjectManager()

# 导出实例（保持向后兼容）
shared_database_manager = shared_project_manager.database_manager
shared_message_manager = shared_project_manager.message_manager

__all__ = [
    'shared_project_manager',
    'shared_database_manager', 
    'shared_message_manager'
]
