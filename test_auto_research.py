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
from typing import Dict, Any, List, Optional
import requests
from sseclient import SSEClient

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class AutoResearchTester:
    """自动研究智能体测试器"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8008"
        self.messages: List[Dict[str, Any]] = []
        self.is_running = True
        self.sse_task = None
        
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def print_messages(self):
        """打印消息列表"""
        self.clear_screen()
        print("=" * 80)
        print("自动研究智能体测试 - 消息列表")
        print("=" * 80)
        print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"消息总数: {len(self.messages)}")
        print("=" * 80)
        
        for i, msg in enumerate(self.messages, 1):
            print(f"\n[{i}] 消息ID: {msg.get('id', 'N/A')}")
            print(f"    角色: {msg.get('role', 'N/A')}")
            print(f"    发送者: {msg.get('publisher', 'N/A')}")
            print(f"    标题: {msg.get('title', 'N/A')}")
            print(f"    状态: {msg.get('status', 'N/A')}")
            if msg.get('status') != "completed":
                print(f"    思考: {msg.get('thinking', 'N/A')}")
            print(f"    内容: {msg.get('content', 'N/A')}")
            if msg.get('action_title'):
                print(f"    行动: {msg.get('action_title')}")
            if msg.get('snapshot_id'):
                print(f"    快照: {msg.get('snapshot_id')}")
            if msg.get('visible_node_ids'):
                print(f"    可见节点: {msg.get('visible_node_ids')}")
            print("-" * 80)
        
        print(f"\n最新消息时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def create_root_problem(self) -> str:
        """通过HTTP接口创建根研究问题"""
        print("正在通过HTTP接口创建根研究问题...")
        
        # 创建根问题请求
        request_data = {
            "title": "周扫红外搜索系统对空中小目标（飞机、导弹、无人机）的检测与告警技术",
            "significance": "",  # 空的研究意义
            "criteria": ""      # 空的验收标准
        }
        
        try:
            # 通过HTTP接口创建根问题
            response = requests.post(
                f"{self.base_url}/research-tree/problems/root",
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
                return problem_id
            else:
                print(f"❌ 根问题创建失败: HTTP {response.status_code}")
                print(f"   响应内容: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到后端服务，请确保后端服务正在运行")
            print(f"   尝试连接: {self.base_url}")
            return None
        except Exception as e:
            print(f"❌ 创建根问题时出错: {e}")
            return None
    
    async def test_auto_research_agent(self, problem_id: str):
        """测试自动研究智能体"""
        print(f"\n正在测试自动研究智能体，问题ID: {problem_id}")
        
        # 准备请求数据
        request_data = {
            "content": f"",
            "title": "自动生成解决方案",
            "agent_name": "auto_research_agent",
            "other_params": {
                "problem_id": problem_id
            }
        }
        
        print("发送请求到智能体接口...")
        print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        try:
            # 发送POST请求启动智能体
            response = requests.post(
                f"{self.base_url}/agents/messages",
                json=request_data,
                headers={"Content-Type": "application/json"},
                stream=True
            )
            
            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return
            
            print("✅ 请求发送成功，开始接收SSE流...")
            
            # 处理SSE流
            await self.handle_sse_stream(response)
            
        except Exception as e:
            print(f"❌ 测试智能体时出错: {e}")
    
    async def handle_sse_stream(self, response):
        """处理SSE流"""
        try:
            # 使用SSEClient处理SSE流
            client = SSEClient(response)
            
            print("开始接收SSE事件...")
            
            for event in client.events():
                if not self.is_running:
                    print("测试已中断，停止接收SSE事件")
                    break
                    
                print(f"📡 收到事件: {event.event}")
                
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
                    
        except Exception as e:
            print(f"❌ 处理SSE流时出错: {e}")
    


    async def handle_patch(self, patch_data: Dict[str, Any]):
        """
        处理patch数据
        
        参考project_manager.py的逻辑，实现完整的消息处理流程：
        1. 处理回溯操作
        2. 创建新消息
        3. 更新现有消息
        """
        try:
            # 处理回溯操作
            if patch_data.get("rollback", False):
                message_id = patch_data.get("message_id")
                if not message_id:
                    print("❌ 回溯操作必须指定message_id")
                    return
                await self._handle_rollback(message_id)
                return
            
            # 检查消息是否存在
            message_id = patch_data.get("message_id")
            existing_message = self._get_message_by_id(message_id)
            
            if existing_message is None:
                await self._create_message_from_patch(patch_data)
            else:
                # 消息存在，更新消息
                await self._update_existing_message(patch_data)
                
        except Exception as e:
            print(f"❌ 处理patch时出错: {e}")
    
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
        
        # 检查role属性是否存在
        role = patch_data.get("role")
        if role is None:
            print("⚠️ 创建新消息时必须指定role属性")
        
        # 创建新消息
        message = {
            "id": patch_data.get("message_id"),
            "role": role,
            "publisher": patch_data.get("publisher", None),
            "status": "generating",
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
            return None
        
        # 应用补丁
        self._apply_patch_to_message(patch_data, message)
        
        print(f"📝 更新消息: {message_id}")
        if message["status"] == "completed":
            print("✅ 消息完成")
        
        return message_id
    
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
    
    def stop_agent(self):
        """发送停止智能体请求"""
        print("\n正在发送停止智能体请求...")
        try:
            response = requests.post(f"{self.base_url}/agents/messages/stop")
            if response.status_code == 200:
                print("✅ 智能体停止请求已发送")
            else:
                print(f"❌ 停止智能体失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 发送停止请求时出错: {e}")
    
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
    
    async def run_test(self):
        """运行完整测试"""
        print("🚀 开始自动研究智能体完整测试")
        print("=" * 80)
        
        # 1. 创建根研究问题
        problem_id = self.create_root_problem()
        if not problem_id:
            print("❌ 无法创建根问题，测试终止")
            return
        
        print(f"\n✅ 根问题创建成功，ID: {problem_id}")
        
        # 2. 测试自动研究智能体
        self.sse_task = asyncio.create_task(self.test_auto_research_agent(problem_id))
        try:
            await self.sse_task
        except asyncio.CancelledError:
            print("测试任务被取消")
        
        # 3. 打印最终总结
        self.print_final_summary()
        
        print("\n🎉 测试完成！")


async def main():
    """主函数"""
    tester = AutoResearchTester()
    
    # 设置信号处理
    def signal_handler(sig, frame):
        print(f"\n接收到信号 {sig}，正在停止测试...")
        tester.is_running = False
        tester.stop_agent()
        
        while tester.is_running:
            time.sleep(1)
        
        # 打印最终总结
        tester.print_final_summary()
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    try:
        await tester.run_test()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        signal_handler(signal.SIGINT, None)


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