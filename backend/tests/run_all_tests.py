"""
运行所有测试的主脚本
包含XML解析器、消息系统和研究树集成测试
"""
import sys
import traceback
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 导入测试模块
from test_xml_parser import TestXMLParser
from test_message_system import TestMessageModels, TestProjectManager
from test_research_tree_integration import TestResearchTreeIntegration

import asyncio


def run_xml_parser_tests():
    """运行XML解析器测试"""
    print("🔧 开始XML解析器测试")
    print("=" * 50)
    
    test_parser = TestXMLParser()
    
    try:
        test_parser.setup_method()
        test_parser.test_xml_to_dict_simple()
        
        test_parser.setup_method()  
        test_parser.test_xml_to_dict_nested()
        
        test_parser.setup_method()
        test_parser.test_validate_with_pydantic_success() 
        
        test_parser.setup_method()
        test_parser.test_validate_with_pydantic_failure()
        
        test_parser.setup_method()
        test_parser.test_parse_and_validate_complete()
        
        test_parser.setup_method()
        test_parser.test_extract_xml_from_content()
        
        test_parser.setup_method()
        test_parser.test_extract_xml_not_found()
        
        test_parser.setup_method()
        test_parser.test_invalid_xml_format()
        
        print("✅ XML解析器测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ XML解析器测试失败: {e}")
        traceback.print_exc()
        return False


def run_message_system_tests():
    """运行消息系统测试"""
    print("\n📨 开始消息系统测试")
    print("=" * 50)
    
    try:
        # 测试消息模型
        msg_test = TestMessageModels()
        msg_test.setup_method()
        msg_test.test_message_creation()
        
        msg_test.setup_method()
        msg_test.test_patch_application()
        
        msg_test.setup_method()
        msg_test.test_frontend_patch_creation()
        
        # 测试项目管理器（异步）
        async def run_async_tests():
            pm_test = TestProjectManager()
            
            pm_test.setup_method()
            await pm_test.test_publish_patch_create_message()
            
            pm_test.setup_method()
            await pm_test.test_publish_patch_update_message()
            
            pm_test.setup_method()
            await pm_test.test_message_history()
            
            pm_test.setup_method()
            await pm_test.test_incomplete_message()
        
        asyncio.run(run_async_tests())
        
        # 测试同步功能
        pm_test = TestProjectManager()
        pm_test.setup_method()
        pm_test.test_database_action_execution()
        
        pm_test.setup_method()
        pm_test.test_project_status()
        
        print("✅ 消息系统测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 消息系统测试失败: {e}")
        traceback.print_exc()
        return False


def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 开始研究树集成测试")
    print("=" * 50)
    
    try:
        test_suite = TestResearchTreeIntegration()
        
        test_suite.setup_method()
        test_suite.test_root_endpoint()
        
        test_suite.setup_method()
        test_suite.test_health_check()
        
        test_suite.setup_method()
        test_suite.test_get_current_snapshot()
        
        test_suite.setup_method()
        test_suite.test_create_root_problem()
        
        test_suite.setup_method()
        test_suite.test_update_root_problem()
        
        test_suite.setup_method()
        test_suite.test_create_solution()
        
        test_suite.setup_method()
        test_suite.test_set_selected_solution()
        
        test_suite.setup_method()
        test_suite.test_delete_solution()
        
        test_suite.setup_method()
        test_suite.test_delete_root_problem()
        
        test_suite.setup_method()
        test_suite.test_database_state_consistency()
        
        print("✅ 研究树集成测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 研究树集成测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🧪 ResVizCopilot 2.0 后端测试套件")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("XML解析器", run_xml_parser_tests()))
    results.append(("消息系统", run_message_system_tests()))
    results.append(("研究树集成", run_integration_tests()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed}个测试套件通过, {failed}个测试套件失败")
    
    if failed == 0:
        print("\n🎉 所有测试都通过了！系统准备就绪。")
        return True
    else:
        print(f"\n⚠️ 有{failed}个测试套件失败，请检查错误信息。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
