#!/usr/bin/env python3
"""
自动研究智能体完整验证程序
测试从创建根问题到生成解决方案的完整流程
添加了中断处理功能
"""
import asyncio
import json
import os
import sys
import time
import signal
import threading
import select
import fcntl
import termios
from typing import Dict, Any, List, Optional
import requests
from sseclient import SSEClient
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
base_url = "http://127.0.0.1:8008"
public_session = requests.Session()
public_session.trust_env = False

class StreamMessageClient:
    """流式消息客户端"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.current_project_name: str = "未命名"  # 当前工程名称
        self.current_snapshot: Dict[str, Any] = {}

    def get_snapshot_by_id(self, snapshot_id: str):
        """
        根据快照ID获取快照内容，并打印主要结构信息，便于调试和验证。

        Args:
            snapshot_id (str): 快照ID

        Returns:
            dict: 快照的完整数据（如果获取成功），否则返回空字典
        """
        try:
            resp = public_session.get(f"{base_url}/research-tree/snapshots/{snapshot_id}")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return data
            else:
                print(f"❌ 获取快照失败: HTTP {resp.status_code}")
                return {}
        except Exception as e:
            print(f"❌ 获取快照时出错: {e}")
            return {}

    def get_current_snapshot_id(self):
        """更新当前快照"""
        for msg in self.messages[::-1]:
            snapshot_id = msg.get("snapshot_id")
            if snapshot_id:
                #print("最新snapshot_id: ", snapshot_id)
                return snapshot_id
        print("无带snapshot_id的消息")
        return ""

    def get_current_snapshot(self):
        """更新当前快照"""
        #print("!!!获取当前snapshot!!!")
        snapshot_id = self.get_current_snapshot_id()
        #print("当前保存snapshot: ", self.current_snapshot)
        if snapshot_id and self.current_snapshot.get("id") != snapshot_id:
            #print("发现当前存储落后，现有snapshot：")
            #print(self.current_snapshot)
            self.current_snapshot = self.get_snapshot_by_id(snapshot_id)
            #print("更新后的snapshot:")
            #print(self.current_snapshot)
        elif not snapshot_id:
            self.current_snapshot = {}
        return self.current_snapshot

    def get_snapshot_id_by_message_index(self, message_index: int) -> Optional[str]:
        """
        根据消息编号获取对应的snapshot_id
        如果该消息没有snapshot_id，则向前回溯找到最近的存在snapshot_id的消息
        
        Args:
            message_index (int): 消息编号（从1开始）
            
        Returns:
            Optional[str]: 找到的snapshot_id，如果没有找到则返回None
        """
        if message_index < 1 or message_index > len(self.messages):
            return None
            
        # 从指定消息开始向前查找
        for i in range(message_index - 1, -1, -1):
            msg = self.messages[i]
            snapshot_id = msg.get("snapshot_id")
            if snapshot_id:
                return snapshot_id
                
        return None

    def get_all_solution_titles(self):
        """递归遍历所有解决方案节点，获取标题"""
        def find_solution_titles(nodes):
            for node in nodes:
                if node.get("type") == "solution":
                    yield node.get("title")
                if node.get("children"):
                    yield from find_solution_titles(node.get("children"))
        return list(find_solution_titles(self.get_current_snapshot().get("roots", [])))

    def get_all_implementaion_problem_titles(self):
        """递归遍历所有实现问题节点，获取标题"""
        def find_implementaion_problem_titles(nodes):
            for node in nodes:
                if node.get("type") == "problem" and node.get("problem_type") == "implementation":
                    yield node.get("title")
                if node.get("children"):
                    yield from find_implementaion_problem_titles(node.get("children"))
        return list(find_implementaion_problem_titles(self.get_current_snapshot().get("roots", [])))

    def get_node_id_by_title(self, title: str) -> str:
        """根据标题递归获取节点ID"""
        def find_node(nodes):
            for node in nodes:
                if node.get("title") == title:
                    return node.get("id")
                if node.get("children"):
                    result = find_node(node.get("children"))
                    if result:
                        return result
            return None
        return find_node(self.get_current_snapshot().get("roots", []))

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """根据ID递归获取节点"""
        def find_node(nodes):
            for node in nodes:
                if node.get("id") == node_id:
                    return node
                if node.get("children"):
                    result = find_node(node.get("children"))
                    if result:
                        return result
            return None
        return find_node(self.get_current_snapshot().get("roots", []))

    def get_parent_node_id(self, node_id: str) -> Optional[str]:
        """获取节点的父节点ID"""
        def find_parent(nodes, target_id, parent_id=None):
            for node in nodes:
                if node.get("id") == target_id:
                    return parent_id
                if node.get("children"):
                    result = find_parent(node.get("children"), target_id, node.get("id"))
                    if result is not None:
                        return result
            return None
        return find_parent(self.get_current_snapshot().get("roots", []), node_id)

    def get_message_sender_info(self, message: Dict[str, Any]) -> str:
        """获取消息发送者信息"""
        if message.get("role") != "assistant":
            return "用户"
        
        publisher_id = message.get("publisher")
        if not publisher_id:
            return "系统消息"
        
        # 获取发布者节点
        publisher_node = self.get_node_by_id(publisher_id)
        if not publisher_node:
            return "未知专家"
        
        # 如果是解决方案节点，获取其父问题节点
        if publisher_node.get("type") == "solution":
            parent_problem_id = self.get_parent_node_id(publisher_id)
            if parent_problem_id:
                parent_problem = self.get_node_by_id(parent_problem_id)
                if parent_problem:
                    return f"「{parent_problem.get('title', '未知问题')}」问题的负责专家"
        
        # 如果是问题节点，直接使用
        if publisher_node.get("type") == "problem":
            return f"「{publisher_node.get('title', '未知问题')}」问题的负责专家"
        
        return "未知专家"

    def save_current_project(self, project_name: str = None) -> bool:
        """
        保存当前工程
        
        Args:
            project_name: 工程名称，如果为None则直接保存，否则为另存为
            
        Returns:
            是否保存成功
        """
        try:
            if project_name is None:
                # 直接保存当前工程
                print(f"💾 保存当前工程: {self.current_project_name}")
                response = public_session.post(f"{base_url}/projects/save")
            else:
                # 另存为
                print(f"💾 另存为工程: {project_name}")
                response = public_session.post(f"{base_url}/projects/save-as", params={"new_project_name": project_name})
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # 更新当前工程名称
                    self.current_project_name = result.get("project_name", self.current_project_name)
                    print(f"✅ 工程保存成功: {self.current_project_name}")
                    return True
                else:
                    print(f"❌ 工程保存失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 保存请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 保存工程失败: {e}")
            return False

    async def create_new_project(self, project_name: str) -> bool:
        """
        创建新工程
        
        Args:
            project_name: 工程名称
            
        Returns:
            是否创建成功
        """
        try:
            print(f"🔨 创建新工程: {project_name}")
            
            # 调用后端接口创建工程
            response = public_session.post(f"{base_url}/projects", params={"project_name": project_name})
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 工程创建成功: {project_name}")
                    
                    # 同步新工程的数据到前端
                    print("🔄 正在同步新工程数据...")
                    sync_success = await self.sync_project_data()
                    if sync_success:
                        print(f"✅ 新工程初始化完成: {self.current_project_name}")
                        return True
                    else:
                        print("❌ 新工程数据同步失败")
                        return False
                else:
                    print(f"❌ 工程创建失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 创建请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 创建工程失败: {e}")
            return False

    async def load_project(self, project_name: str) -> bool:
        """
        加载指定工程
        
        Args:
            project_name: 工程名称
            
        Returns:
            是否加载成功
        """
        try:
            print(f"📂 加载工程: {project_name}")
            
            # 调用后端接口切换工程
            response = public_session.get(f"{base_url}/projects/{project_name}")
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 工程切换成功: {project_name}")
                    
                    # 同步工程数据到前端
                    print("🔄 正在同步工程数据...")
                    sync_success = await self.sync_project_data()
                    if sync_success:
                        print(f"✅ 工程加载完成: {self.current_project_name}")
                        return True
                    else:
                        print("❌ 工程数据同步失败")
                        return False
                else:
                    print(f"❌ 工程加载失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 加载请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 加载工程失败: {e}")
            return False

    def list_projects(self) -> List[Dict[str, str]]:
        """
        获取工程列表
        
        Returns:
            工程列表
        """
        try:
            response = public_session.get(f"{base_url}/projects")
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("projects", [])
                else:
                    print(f"❌ 获取工程列表失败: {result.get('message')}")
                    return []
            else:
                print(f"❌ 获取工程列表请求失败: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 获取工程列表失败: {e}")
            return []

    def print_project_list(self):
        """打印工程列表"""
        projects = self.list_projects()
        print(f"\n📁 工程列表 (共 {len(projects)} 个):")
        for i, project in enumerate(projects, 1):
            created = project.get("created_at", "未知")[:19] if project.get("created_at") else "未知"
            updated = project.get("updated_at", "未知")[:19] if project.get("updated_at") else "未知"
            current_flag = " (当前)" if project["project_name"] == self.current_project_name else ""
            print(f"{i:2d}. {project['project_name']}{current_flag}")
            print(f"     创建: {created}")
            print(f"     更新: {updated}")

    def handle_save_project(self) -> None:
        """处理保存工程操作"""
        print("\n💾 保存工程")
        print("1. 直接保存当前工程")
        print("2. 另存为")
        
        choice = input("请选择操作 (1/2): ").strip()
        
        if choice == "1":
            # 直接保存
            if self.save_current_project():
                print("✅ 工程保存成功")
            else:
                print("❌ 工程保存失败")
        elif choice == "2":
            # 另存为
            project_name = input("请输入新工程名称: ").strip()
            if project_name:
                if self.save_current_project(project_name):
                    print(f"✅ 工程另存为成功: {project_name}")
                else:
                    print("❌ 工程另存为失败")
            else:
                print("❌ 工程名称不能为空")
        else:
            print("❌ 无效的选择")

    async def handle_create_project(self) -> None:
        """处理创建新工程操作"""
        print("\n🔨 创建新工程")
        
        # 输入新工程名称
        project_name = input("请输入新工程名称: ").strip()
        
        if not project_name:
            print("❌ 工程名称不能为空")
            return
        
        # 检查工程名称是否已存在
        existing_projects = self.list_projects()
        existing_names = [p["project_name"] for p in existing_projects]
        
        if project_name in existing_names:
            print(f"❌ 工程名称 '{project_name}' 已存在，请选择其他名称")
            return
        
        # 创建新工程
        if await self.create_new_project(project_name):
            print(f"✅ 工程创建成功: {project_name}")
            print(f"📁 当前工程已切换为: {self.current_project_name}")
        else:
            print(f"❌ 工程创建失败: {project_name}")

    async def handle_load_project(self) -> None:
        """处理加载工程操作"""
        print("\n📂 加载工程")
        
        # 显示工程列表
        self.print_project_list()
        
        # 选择要加载的工程
        choice = input("请输入要加载的工程编号: ").strip()
        
        if choice.isdigit():
            project_index = int(choice) - 1
            projects = self.list_projects()
            
            if 0 <= project_index < len(projects):
                project_name = projects[project_index]["project_name"]
                if await self.load_project(project_name):
                    print(f"✅ 工程加载成功: {project_name}")
                else:
                    print(f"❌ 工程加载失败: {project_name}")
            else:
                print("❌ 工程编号超出范围")
        else:
            print("❌ 请输入有效的数字")

    async def handle_rollback_to_message(self) -> None:
        """处理回退到指定消息操作"""
        print("\n🔄 回退到指定消息")
        
        if not self.messages:
            print("❌ 当前没有消息，无法执行回退操作")
            input("按回车键继续...")
            return
        
        while True:
            try:
                message_index_input = input("\n请输入要回退到的消息编号（该消息之后的消息将被删除）: ").strip()
                if message_index_input.lower() == 'q':
                    print("❌ 取消回退操作")
                    return
                
                message_index = int(message_index_input)
                if 1 <= message_index <= len(self.messages):
                    target_message = self.messages[message_index - 1]
                    target_message_id = target_message.get("id")
                    
                    # 确认操作
                    messages_to_delete_count = len(self.messages) - message_index
                    if messages_to_delete_count == 0:
                        print("⚠️ 该消息已经是最后一条消息，无需回退")
                        return
                    
                    print(f"\n⚠️ 确认回退操作：")
                    print(f"   回退到消息: [{target_message.get('role', 'N/A')}] {target_message.get('title', 'N/A')}")
                    print(f"   将删除 {messages_to_delete_count} 条后续消息")
                    
                    confirm = input("确认执行回退操作？(y/N): ").strip().lower()
                    if confirm != 'y':
                        print("❌ 取消回退操作")
                        return
                    
                    # 调用后端API执行回退
                    try:
                        response = public_session.post(f"{base_url}/agents/messages/rollback-to/{target_message_id}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"✅ {result['message']}")
                            print(f"📊 删除了 {result['deleted_count']} 条消息")
                            if result.get('target_snapshot_id'):
                                print(f"📸 快照已回退到: {result['target_snapshot_id']}")
                            else:
                                print("📸 未找到可回退的快照")
                            
                            # 重新同步数据
                            print("🔄 正在同步最新数据...")
                            await self.sync_project_data()
                            print("✅ 数据同步完成")
                            
                        else:
                            error_detail = response.json().get("detail", "未知错误") if response.headers.get("content-type", "").startswith("application/json") else response.text
                            print(f"❌ 回退操作失败: {error_detail}")
                            
                    except Exception as e:
                        print(f"❌ 回退操作出错: {e}")
                    
                    break
                    
                else:
                    print(f"❌ 消息编号必须在 1 到 {len(self.messages)} 之间")
                    continue
                    
            except ValueError:
                print("❌ 请输入有效的数字，或输入 'q' 取消")
                continue
        
        input("按回车键继续...")

    def get_snapshot_document(self, snapshot: Dict[str, Any]):
        """
        打印快照树状结构，仅显示标题与状态
        """
        if "roots" not in snapshot:
            return "⚠️ 该快照无内容"

        def render(node, depth, parent_problem=None):
            indent = "  " * depth
            # 判断节点类型
            if node.get("type") == "problem":
                # 问题节点
                problem_type = node.get("problem_type", "未知类型")
                line = f"{indent}- [P] {node.get('title', '无标题')} ({problem_type})"
                lines = [line]
                for c in node.get("children", []):
                    lines.extend(render(c, depth + 1, node))
                return lines
            elif node.get("type") == "solution":
                # 解决方案节点
                status_flag = ""
                if parent_problem is not None:
                    # 判断是否为选中方案
                    if parent_problem.get("selected_solution_id") == node.get("id"):
                        status_flag = "(正启用)"
                    else:
                        status_flag = "(已弃用)"
                
                state = node.get("state", "未知状态")
                line = f"{indent}- [S] {node.get('title', '无标题')} {status_flag} [{state}]"
                lines = [line]
                for c in node.get("children", []):
                    lines.extend(render(c, depth + 1, None))
                return lines
            else:
                # 未知类型
                line = f"{indent}- [未知节点] {node.get('title', '无标题')}"
                return [line]

        lines = []
        for r in snapshot.get("roots", []):
            lines.extend(render(r, 0, None))
        result = "📚 快照树状结构：\n" + "\n".join(lines)
        return result
        
    async def sync_project_data(self) -> bool:
        """
        同步工程数据，包括消息历史和工程信息
        
        Returns:
            是否同步成功
        """
        try:
            print("🔄 正在同步工程数据...")
            
            # 获取工程完整数据（包括消息历史和工程信息）
            response = public_session.get(f"{base_url}/projects/current/full-data")
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    full_data = response_data.get("data", {})
                    
                    # 获取消息历史（完全保留原有格式）
                    history_messages = full_data.get("messages", [])
                    incomplete_message_id = full_data.get("incomplete_message_id")
                    
                    # 获取工程信息
                    project_info = full_data.get("project_info", {})
                    current_snapshot_id = full_data.get("current_snapshot_id")
                    
                    # 更新工程信息
                    self.current_project_name = project_info.get("project_name", "未命名")
                    
                    # 重置消息列表
                    self.messages = []
                    
                    # 将历史消息转换为内部格式（完全保留原有逻辑）
                    for msg in history_messages:
                        self.messages.append({
                            "id": msg.get("id"),
                            "role": msg.get("role"),
                            "publisher": msg.get("publisher"),
                            "status": msg.get("status"),
                            "title": msg.get("title"),
                            "thinking": msg.get("thinking", ""),
                            "content": msg.get("content", ""),
                            "action_title": msg.get("action_title", ""),
                            "action_params": msg.get("action_params", {}),
                            "snapshot_id": msg.get("snapshot_id", ""),
                            "visible_node_ids": msg.get("visible_node_ids", []),
                            "created_at": msg.get("created_at", ""),
                            "updated_at": msg.get("updated_at", "")
                        })
                    self.get_current_snapshot()
                    print(f"✅ 工程数据同步成功: {self.current_project_name}")
                    print(f"📊 消息数量: {len(self.messages)}")
                    print(f"📊 快照数量: {project_info.get('snapshot_count', 0)}")
                    
                    # 处理未完成的消息
                    if incomplete_message_id:
                        print(f"⚠️ 发现未完成消息: {incomplete_message_id}")
                        print("🔄 开始继续传输未完成消息...")
                        await self.continue_incomplete_message(incomplete_message_id)
                    else:
                        print("✅ 没有未完成的消息")
                    
                    return True
                else:
                    print(f"❌ 获取工程数据失败: {response_data.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 获取工程数据失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 同步工程数据时出错: {e}")
            return False
        
    async def initialize(self):
        """初始化客户端，获取工程完整数据"""
        print("🔄 正在初始化SSE客户端...")
        success = await self.sync_project_data()
        if not success:
            print("❌ 初始化失败")
            raise Exception("初始化SSE客户端失败")
    
    async def continue_incomplete_message(self, incomplete_message_id: str):
        """继续未完成的消息传输"""
        if not incomplete_message_id:
            return
            
        try:
            print(f"🔄 连接到继续传输接口: {incomplete_message_id}")
            
            # 调用继续传输接口
            response = public_session.get(
                f"{base_url}/agents/messages/continue/{incomplete_message_id}",
                headers={"Accept": "text/event-stream"},
                stream=True
            )
            
            if response.status_code == 200:
                print("✅ 继续传输连接成功，开始接收SSE流...")
                await self.handle_sse_stream(response)
            else:
                print(f"❌ 继续传输失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 继续传输时出错: {e}")


    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
        #print("\n" * 3)
        
    def print_messages(self):
        """打印消息列表"""
        output_text = ""
        output_text += "="*80 + "\n"
        output_text += f"📁 当前工程: {self.current_project_name}\n"
        output_text += "="*80 + "\n"
        output_text += self.get_snapshot_document(self.get_current_snapshot()) + "\n"
        output_text += "=" * 80 + "\n"
        output_text += "SSE客户端 - 消息列表" + "\n"
        output_text += "=" * 80 + "\n"
        output_text += f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output_text += f"消息总数: {len(self.messages)}\n"
        output_text += "=" * 80 + "\n"
        for i, msg in enumerate(self.messages, 1):
            output_text += f"\n[{i}] 消息ID: {msg.get('id', 'N/A')}\n"
            output_text += f"    角色: {msg.get('role', 'N/A')}\n"
            sender_info = self.get_message_sender_info(msg)
            output_text += f"    发送者: {sender_info}\n"
            output_text += f"    标题: {msg.get('title', 'N/A')}\n"
            output_text += f"    状态: {msg.get('status', 'N/A')}\n"
            if msg.get('status') == "generating" and msg.get('thinking'):
                output_text += f"    思考: {msg.get('thinking', 'N/A')}\n"
            output_text += f"    内容: {msg.get('content', 'N/A')}\n"
            if msg.get('action_title'):
                output_text += f"    行动: {msg.get('action_title')}\n"
            if msg.get('snapshot_id'):
                output_text += f"    快照: {msg.get('snapshot_id')}\n"
            if msg.get('visible_node_ids'):
                output_text += f"    可见节点: {msg.get('visible_node_ids')}\n"
            output_text += "-" * 80 + "\n"

        output_text += f"\n最新消息时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        self.clear_screen()
        print(output_text)
        
    async def handle_sse_stream(self, response):
        """处理SSE流"""
        try:
            # 使用SSEClient处理SSE流
            client = SSEClient(response)
            
            print("开始接收SSE事件...")
            print("💡 提示: 按 'q' 键可以中断连接")
            
            
            # 保存原始终端设置
            old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                # 设置非阻塞模式
                tty = termios.tcgetattr(sys.stdin)
                tty[3] &= ~termios.ICANON
                tty[3] &= ~termios.ECHO
                termios.tcsetattr(sys.stdin, termios.TCSANOW, tty)
                
                for event in client.events():
                    # 检查键盘输入
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        if key.lower() == 'q':
                            print("\n🛑 用户按下 'q' 键，正在发送中断请求...")
                            await self._send_interrupt_request()
                            print("⏳ 等待SSE连接结束...")
                            await asyncio.sleep(3)
                    
                    #print(f"📡 收到事件: {event.event}")
                    
                    if event.event == "patch":
                        # 处理patch事件
                        patch_data = json.loads(event.data)
                        await self.handle_patch(patch_data)
                        
                    elif event.event == "error":
                        # 处理错误事件
                        error_data = json.loads(event.data)
                        print(f"❌ 收到错误事件: {error_data}")
                        break

                    elif event.event == "finished":
                        # 处理完成事件
                        finished_data = json.loads(event.data)
                        print(f"✅ 收到完成事件: {finished_data}")
                        break
                        
                    # 实时打印消息列表
                    self.print_messages()
                    
            finally:
                # 恢复终端设置
                termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
                    
        except Exception as e:
            print(f"❌ 处理SSE流时出错: {e}")
            raise e
    


    async def handle_patch(self, patch_data: Dict[str, Any]):
        """
        处理patch数据
        
        参考project_manager.py的逻辑，实现完整的消息处理流程：
        1. 处理回溯操作
        2. 创建新消息
        3. 更新现有消息
        """
        try:
            if patch_data.get("snapshot", {}):
                self.current_snapshot = patch_data["snapshot"]["data"]
            # 处理回溯操作
            if patch_data.get("rollback", False):
                message_id = patch_data.get("message_id")
                if not message_id:
                    print("❌ 回溯操作必须指定message_id")
                    await asyncio.sleep(5)
                else:
                    await self._handle_rollback(message_id)
            else:
                # 检查消息是否存在
                message_id = patch_data.get("message_id")

                if message_id == "-":
                    await self._update_all_messages(patch_data)
                else:
                    existing_message = self._get_message_by_id(message_id)

                    if existing_message is None:
                        await self._create_message_from_patch(patch_data)
                    else:
                        # 消息存在，更新消息
                        await self._update_existing_message(patch_data)
        except Exception as e:
            print(f"❌ 处理patch时出错: {e}")
            raise e
    
    async def _create_message_from_patch(self, patch_data: Dict[str, Any]) -> str:
        """
        从补丁创建新消息
        
        Args:
            patch_data: 补丁数据字典
            
        Returns:
            创建的消息ID
        """
        # 检查是否有消息正在生成
        generating_msg = self._get_incomplete_message()
        if generating_msg:
            print(f"⚠️ 存在正在生成的消息: {generating_msg['id']}")
            await asyncio.sleep(5)
        
        # 检查role属性是否存在
        role = patch_data.get("role")
        if role is None:
            print("⚠️ 创建新消息时必须指定role属性")
            await asyncio.sleep(5)
        
        # 创建新消息
        message = {
            "id": patch_data.get("message_id"),
            "role": role,
            "publisher": patch_data.get("publisher", None),
            "status": "completed" if patch_data.get("finished", False) else "generating",
            "title": patch_data.get("title", ""),
            "thinking": patch_data.get("thinking_delta", ""),
            "content": patch_data.get("content_delta", ""),
            "action_title": patch_data.get("action_title", ""),
            "action_params": patch_data.get("action_params", {}),
            "snapshot_id": patch_data.get("snapshot_id", ""),
            "visible_node_ids": patch_data.get("visible_node_ids", []),
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 存储消息
        self.messages.append(message)
        
    
    async def _update_existing_message(self, patch_data: Dict[str, Any]) -> str:
        """
        更新现有消息
        
        Args:
            patch_data: 补丁数据字典
            
        Returns:
            消息ID
        """
        message_id = patch_data.get("message_id")
        message = self._get_message_by_id(message_id)
        
        if message is None:
            print(f"❌ 消息不存在: {message_id}")
            await asyncio.sleep(5)
            return None
        
        # 应用补丁
        self._apply_patch_to_message(patch_data, message)
        
        return message_id

        
    async def _update_all_messages(self, patch_data: Dict[str, Any]) -> str:
        """
        更新所有消息
        """
        for message in self.messages:
            if message["status"] == "generating":
                self._apply_patch_to_message(patch_data, message)
        return self.messages[-1]["id"] if self.messages else ""
    
    
    async def _handle_rollback(self, message_id: str) -> str:
        """
        处理消息回溯
        
        Args:
            message_id: 要回溯到的消息ID（包括该消息在内的后续消息都会被删除）
            
        Returns:
            回溯后剩余的最新消息ID
        """
        # 找到消息在列表中的位置
        rollback_index = -1
        for i, msg in enumerate(self.messages):
            if msg["id"] == message_id:
                rollback_index = i
                break
        
        if rollback_index == -1:
            print(f"⚠️ 回溯消息不存在: {message_id}")
            await asyncio.sleep(5)
            return self.messages[-1]["id"] if self.messages else ""
        
        # 删除从该位置开始的所有消息
        messages_to_remove = self.messages[rollback_index+1:]
        self.messages = self.messages[:rollback_index+1]
        target_message = self.messages[rollback_index]
        target_message["status"] = "generating"
        target_message["content"] = ""
        target_message["thinking"] = ""
        target_message["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"🔄 回溯消息: 删除了 {len(messages_to_remove)} 条消息")
        await asyncio.sleep(3)
        
        # 返回剩余的最新消息ID
        return self.messages[-1]["id"] if self.messages else ""
    
    def _apply_patch_to_message(self, patch_data: Dict[str, Any], message: Dict[str, Any]) -> None:
        """
        将补丁应用到消息上
        
        Args:
            patch_data: 补丁数据字典
            message: 要更新的消息字典
        """
        # 增量更新
        if patch_data.get("thinking_delta"):
            message["thinking"] += patch_data["thinking_delta"]
        if patch_data.get("content_delta"):
            message["content"] += patch_data["content_delta"]
            
        # 替换更新
        if patch_data.get("title") is not None:
            message["title"] = patch_data["title"]
        if patch_data.get("action_title") is not None:
            message["action_title"] = patch_data["action_title"]
        if patch_data.get("action_params") is not None:
            message["action_params"] = patch_data["action_params"]
        if patch_data.get("snapshot_id") is not None:
            message["snapshot_id"] = patch_data["snapshot_id"]
        if patch_data.get("visible_node_ids") is not None:
            message["visible_node_ids"] = patch_data["visible_node_ids"]
            
        # 更新状态
        if patch_data.get("finished", False):
            message["status"] = "completed"
            
        # 更新时间戳
        message["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            消息字典，如果不存在返回None
        """
        for message in self.messages:
            if message["id"] == message_id:
                return message
        return None
    
    def _get_incomplete_message(self) -> Optional[Dict[str, Any]]:
        """
        获取未完成的消息
        
        Returns:
            状态为generating的消息，如果没有则返回None
        """
        for message in self.messages:
            if message["status"] == "generating":
                return message
        return None
    
    async def _send_interrupt_request(self):
        """发送中断连接请求"""
        try:
            print("🔄 正在发送中断请求...")
            response = public_session.post(f"{base_url}/agents/messages/stop")
            if response.status_code == 200:
                print("✅ 中断请求发送成功")
            else:
                print(f"❌ 中断请求失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 发送中断请求时出错: {e}")
    
    
    def print_final_summary(self):
        """打印最终总结"""
        print("\n" + "=" * 80)
        print("测试完成总结")
        print("=" * 80)
        
        print(f"总消息数: {len(self.messages)}")
        
        user_messages = [msg for msg in self.messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in self.messages if msg.get("role") == "assistant"]
        
        print(f"用户消息: {len(user_messages)}")
        print(f"智能体消息: {len(assistant_messages)}")
        
        print("\n消息详情:")
        for i, msg in enumerate(self.messages, 1):
            print(f"  {i}. [{msg.get('role', 'N/A')}] {msg.get('title', 'N/A')}")
            if msg.get('action_title'):
                print(f"     行动: {msg.get('action_title')}")
            if msg.get('snapshot_id'):
                print(f"     快照: {msg.get('snapshot_id')}")
        
        print("=" * 80)


def create_root_problem() -> str:
    """通过HTTP接口创建根研究问题"""
    print("正在通过HTTP接口创建根研究问题...")
    title = input("请输入根问题标题: (如果为空，默认为'周扫红外搜索系统对空中小目标（飞机、导弹、无人机）的检测与告警技术')")
    if not title:
        title = "周扫红外搜索系统对空中小目标（飞机、导弹、无人机）的检测与告警技术"
    significance = input("请输入研究意义: (如果为空，默认为'空')")
    criteria = input("请输入验收标准: (如果为空，默认为'空')")
    # 创建根问题请求
    request_data = {
        "title": title,
        "significance": significance,
        "criteria": criteria
    }
    
    try:
        # 通过HTTP接口创建根问题
        response = public_session.post(
            f"{base_url}/research-tree/problems/root",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            snapshot = response_data["data"]
            problem_id = snapshot["roots"][-1]["id"]
            print(f"✅ 根问题创建成功，ID: {problem_id}")
            print(f"   标题: {request_data['title']}")
            print(f"   快照ID: {snapshot['id']}")
            return request_data, response_data
        else:
            print(f"❌ 根问题创建失败: HTTP {response.status_code}")
            print(f"   响应内容: {response.text}")
            return request_data, None
            
    except public_session.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端服务正在运行")
        print(f"   尝试连接: {base_url}")
        return request_data, None
    except Exception as e:
        print(f"❌ 创建根问题时出错: {e}")
        return request_data, None


async def call_agent(sse_client: StreamMessageClient):
    """测试调用智能体"""
    while True:
        agent_select = input("【可选智能体列表】\n1. 自动研究智能体\n2. 自动对话智能体\n请选择智能体: ")
        if agent_select in ["1", "2"]:
            break
        else:
            print("❌ 输入的智能体名称不正确，请重新输入")

    if agent_select == "1":
        agent_name = "auto_research_agent"
        print("="*80)
        print("自动研究智能体")
        print("="*80)
        while True:
            print("【实施问题列表】")
            implementaion_problem_titles = sse_client.get_all_implementaion_problem_titles()    
            for i, problem_title in enumerate(implementaion_problem_titles, 1):
                print(f"{i}. {problem_title}")
            problem_select = input("请指定一个实施问题: ")
            if problem_select.isdigit():
                problem_select = int(problem_select)
                if 1 <= problem_select <= len(implementaion_problem_titles):
                    problem_title = implementaion_problem_titles[problem_select - 1]
                    break
                else:
                    print("❌ 输入的实施问题编号不正确，请重新输入")
                    continue
            else:
                print("❌ 输入的实施问题编号不正确，请重新输入")
                continue
        problem_id = sse_client.get_node_id_by_title(problem_title)
        other_params = {"problem_id": problem_id}
        content = input("请输入要求: ")
        title = "自动生成解决方案"
    else:
        agent_name = "user_chat_agent"
        print("="*80)
        print("自动对话智能体")
        print("="*80)
        while True:
            print("【解决方案列表】")
            solution_titles = sse_client.get_all_solution_titles()
            for i, solution_title in enumerate(solution_titles, 1):
                print(f"{i}. {solution_title}")
            solution_select = input("请指定一个解决方案: ")
            if solution_select.isdigit():
                solution_select = int(solution_select)
                if 1 <= solution_select <= len(solution_titles):
                    solution_title = solution_titles[solution_select - 1]
                    break
                else:
                    print("❌ 输入的解决方案编号不正确，请重新输入")
                    continue
            else:
                print("❌ 输入的解决方案编号不正确，请重新输入")
                continue
        solution_id = sse_client.get_node_id_by_title(solution_title)
        other_params = {"solution_id": solution_id}
        content = input("请输入要求: ")
        title = "自动对话解决方案"
    # 准备请求数据
    request_data = {
        "content": content,
        "title": title,
        "agent_name": agent_name,
        "other_params": other_params
    }
    
    print("发送请求到智能体接口...")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求启动智能体
        response = public_session.post(
            f"{base_url}/agents/messages",
            json=request_data,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        print("✅ 请求发送成功，开始接收SSE流...")
      
        await sse_client.handle_sse_stream(response)
        
    except Exception as e:
        print(f"❌ 测试智能体时出错: {e}")
        raise e


async def main():
    """主函数"""
    sse_client = StreamMessageClient()
    await sse_client.initialize()
    while True:
        sse_client.print_messages()
        print("\n" + "="*80)
        print("【可选操作列表】")
        print("1. 创建根问题")
        print("2. 调用智能体")
        print("3. 创建新工程")
        print("4. 保存当前工程")
        print("5. 加载已有工程")
        print("6. 根据消息编号查看快照")
        print("7. 回退到指定消息")
        print("8. 退出")
        print("="*80)
        
        operation_select = input("请选择操作: ")
        
        if operation_select == "1":
            request_data, response_data = create_root_problem()
            if response_data:
                await sse_client.initialize()
        elif operation_select == "2":
            await call_agent(sse_client)
        elif operation_select == "3":
            await sse_client.handle_create_project()
        elif operation_select == "4":
            sse_client.handle_save_project()
        elif operation_select == "5":
            await sse_client.handle_load_project()
        elif operation_select == "6":
            while True:
                try:
                    message_index_input = input("\n请输入要查看的消息编号: ")
                    if message_index_input.lower() == 'q':
                        break
                    
                    message_index = int(message_index_input)
                    if 1 <= message_index <= len(sse_client.messages):
                        # 获取并打印对应的snapshot
                        snapshot_id = sse_client.get_snapshot_id_by_message_index(message_index)
                        snapshot = sse_client.get_snapshot_by_id(snapshot_id)
                        output_text = sse_client.get_snapshot_document(snapshot)
                        print(output_text)
                        break
                    else:
                        print(f"❌ 消息编号必须在 1 到 {len(sse_client.messages)} 之间")
                        continue
                except ValueError:
                    print("❌ 请输入有效的数字，或输入 'q' 退出")
                    continue
            
            input("按回车键继续...")
        elif operation_select == "7":
            await sse_client.handle_rollback_to_message()
        elif operation_select == "8":
            break
        else:
            print("❌ 无效的选择，请重新输入")

if __name__ == "__main__":
    # 检查依赖
    try:
        import requests
        import sseclient
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请安装: pip install requests sseclient-py")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(main())