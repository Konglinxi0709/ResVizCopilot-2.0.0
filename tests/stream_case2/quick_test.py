#!/usr/bin/env python3
"""
快速验证重构后的系统功能
"""
import asyncio
from core.simple_agent_validators import CreateResearchProblemOutput
from core.simple_agent_prompts import PromptStrategy
from utils.xml_parser import XMLParser

def test_validators():
    """测试验证器"""
    print("=== 测试验证器 ===")
    
    valid_data = {
        "title": "create_research_problem",
        "params": {
            "title": "AI研究测试",
            "significance": "这是一个重要的研究方向，具有重大意义和价值",
            "criteria": "需要满足创新性、可行性和实用性要求"
        }
    }
    
    try:
        validator = CreateResearchProblemOutput(**valid_data)
        print(f"✓ 验证器测试通过: {validator.title}")
        return True
    except Exception as e:
        print(f"✗ 验证器测试失败: {e}")
        return False

def test_prompt_strategy():
    """测试提示词策略"""
    print("\n=== 测试提示词策略 ===")
    
    strategy = PromptStrategy()
    test_cases = [
        ("请创建一个研究问题", "有验证器"),
        ("查询现有问题", "有验证器"),
        ("你好", "无验证器")
    ]
    
    success = True
    for user_input, expected in test_cases:
        prompt, validator = strategy.get_prompt_and_validator(user_input)
        has_validator = "有验证器" if validator else "无验证器"
        
        if has_validator == expected:
            print(f"✓ '{user_input}' -> {has_validator}")
        else:
            print(f"✗ '{user_input}' -> {has_validator} (期望 {expected})")
            success = False
    
    return success

def test_xml_parsing():
    """测试XML解析"""
    print("\n=== 测试XML解析 ===")
    
    xml_content = '''<action>
<title>create_research_problem</title>
<params>
<title>测试研究问题</title>
<significance>这是一个测试用的研究问题，具有重要意义</significance>
<criteria>需要满足基本的研究标准和要求</criteria>
</params>
</action>'''
    
    try:
        parser = XMLParser()
        data_dict = parser.xml_to_dict(xml_content)
        validated = parser.validate_with_pydantic(data_dict, CreateResearchProblemOutput)
        print(f"✓ XML解析和验证成功: {validated.params.title}")
        return True
    except Exception as e:
        print(f"✗ XML解析失败: {e}")
        return False

async def test_llm_output():
    """测试LLM输出"""
    print("\n=== 测试LLM输出 ===")
    
    from core.llm_client import MockLLMClient
    from models.message import Patch
    
    collected_content = ""
    
    async def callback(patch):
        nonlocal collected_content
        if patch.content_delta:
            collected_content += patch.content_delta
    
    try:
        client = MockLLMClient(callback)
        
        # 测试chat类型
        result1 = await client.stream_generate("你好", "test1")
        print(f"✓ Chat输出: {len(result1)} 字符")
        
        # 重置
        collected_content = ""
        
        # 测试create_problem类型  
        result2 = await client.stream_generate("请创建一个研究问题", "test2")
        print(f"✓ Create问题输出: {len(result2)} 字符")
        
        # 验证XML提取
        parser = XMLParser()
        xml_fragment = parser.extract_xml_from_content(result2, "action")
        if xml_fragment:
            print("✓ 成功提取XML片段")
            return True
        else:
            print("✗ 未找到XML片段")
            return False
            
    except Exception as e:
        print(f"✗ LLM输出测试失败: {e}")
        return False

def main():
    """主函数"""
    print("ResVizCopilot 2.0 智能体重构验证")
    print("=" * 50)
    
    tests = [
        ("验证器", test_validators),
        ("提示词策略", test_prompt_strategy), 
        ("XML解析", test_xml_parsing),
        ("LLM输出", lambda: asyncio.run(test_llm_output()))
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n测试 {name}...")
        if test_func():
            passed += 1
        
    print(f"\n{'=' * 50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构成功！")
        return True
    else:
        print("❌ 部分测试失败，需要检查")
        return False

if __name__ == "__main__":
    main()
