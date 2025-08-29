"""
XML解析器测试
测试XML解析和Pydantic验证功能
"""
import pytest
from pydantic import BaseModel, Field
from typing import Optional

from backend.utils.xml_parser import XMLParser, XMLValidationError


class TestData(BaseModel):
    """测试用的数据模型"""
    title: str = Field(description="标题")
    content: str = Field(description="内容")
    number: Optional[int] = Field(default=None, description="数字")


class TestXMLParser:
    """XML解析器测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.parser = XMLParser()
        print("\n=== 开始XML解析器测试 ===")
    
    def test_xml_to_dict_simple(self):
        """测试简单XML转字典"""
        xml_text = """
        <data>
            <title>测试标题</title>
            <content>测试内容</content>
            <number>123</number>
        </data>
        """
        
        print(f"输入XML: {xml_text.strip()}")
        result = self.parser.xml_to_dict(xml_text)
        print(f"解析结果: {result}")
        
        expected = {
            'title': '测试标题',
            'content': '测试内容',
            'number': '123'
        }
        
        assert result == expected
        print("✅ 简单XML解析测试通过")
    
    def test_xml_to_dict_nested(self):
        """测试嵌套XML转字典"""
        xml_text = """
        <data>
            <title>父标题</title>
            <item>
                <name>子项目1</name>
                <value>值1</value>
            </item>
            <item>
                <name>子项目2</name>
                <value>值2</value>
            </item>
        </data>
        """
        
        print(f"输入嵌套XML: {xml_text.strip()}")
        result = self.parser.xml_to_dict(xml_text)
        print(f"解析结果: {result}")
        
        assert result['title'] == '父标题'
        assert isinstance(result['item'], list)
        assert len(result['item']) == 2
        assert result['item'][0]['name'] == '子项目1'
        print("✅ 嵌套XML解析测试通过")
    
    def test_validate_with_pydantic_success(self):
        """测试Pydantic验证成功"""
        data = {
            'title': '测试标题',
            'content': '测试内容',
            'number': 123
        }
        
        print(f"输入数据: {data}")
        result = self.parser.validate_with_pydantic(data, TestData)
        print(f"验证结果: {result}")
        print(f"结果类型: {type(result)}")
        
        assert isinstance(result, TestData)
        assert result.title == '测试标题'
        assert result.content == '测试内容'
        assert result.number == 123
        print("✅ Pydantic验证成功测试通过")
    
    def test_validate_with_pydantic_failure(self):
        """测试Pydantic验证失败"""
        data = {
            'title': '测试标题',
            # 缺少必需的content字段
            'number': 'invalid_number'  # 无效的数字
        }
        
        print(f"输入无效数据: {data}")
        
        with pytest.raises(XMLValidationError) as exc_info:
            self.parser.validate_with_pydantic(data, TestData)
        
        print(f"预期的验证错误: {exc_info.value}")
        print("✅ Pydantic验证失败测试通过")
    
    def test_parse_and_validate_complete(self):
        """测试完整的解析和验证流程"""
        xml_text = """
        <data>
            <title>完整测试</title>
            <content>这是完整的解析和验证测试</content>
            <number>456</number>
        </data>
        """
        
        print(f"输入XML: {xml_text.strip()}")
        result = self.parser.parse_and_validate(xml_text, TestData)
        print(f"最终结果: {result}")
        print(f"结果类型: {type(result)}")
        
        assert isinstance(result, TestData)
        assert result.title == '完整测试'
        assert result.content == '这是完整的解析和验证测试'
        assert result.number == 456
        print("✅ 完整解析验证测试通过")
    
    def test_extract_xml_from_content(self):
        """测试从内容中提取XML片段"""
        content = """
        这是一些普通文本。
        
        <action>
            <type>create_problem</type>
            <title>从内容中提取的问题</title>
        </action>
        
        还有一些其他文本。
        """
        
        print(f"输入内容: {content.strip()}")
        result = self.parser.extract_xml_from_content(content, "action")
        print(f"提取的XML片段: {result}")
        
        assert result is not None
        assert "<action>" in result
        assert "</action>" in result
        assert "create_problem" in result
        print("✅ XML片段提取测试通过")
    
    def test_extract_xml_not_found(self):
        """测试未找到XML片段的情况"""
        content = "这里没有任何XML内容，只是普通文本。"
        
        print(f"输入无XML内容: {content}")
        result = self.parser.extract_xml_from_content(content, "action")
        print(f"提取结果: {result}")
        
        assert result is None
        print("✅ XML片段未找到测试通过")
    
    def test_invalid_xml_format(self):
        """测试无效XML格式"""
        invalid_xml = "<data><title>未闭合标签<content>测试</content></data>"
        
        print(f"输入无效XML: {invalid_xml}")
        
        with pytest.raises(XMLValidationError) as exc_info:
            self.parser.xml_to_dict(invalid_xml)
        
        print(f"预期的XML错误: {exc_info.value}")
        print("✅ 无效XML格式测试通过")


if __name__ == "__main__":
    # 运行测试
    test_parser = TestXMLParser()
    
    print("🧪 开始运行XML解析器测试套件")
    
    try:
        test_parser.setup_method()
        test_parser.test_xml_to_dict_simple()
        print()
        
        test_parser.setup_method()  
        test_parser.test_xml_to_dict_nested()
        print()
        
        test_parser.setup_method()
        test_parser.test_validate_with_pydantic_success() 
        print()
        
        test_parser.setup_method()
        test_parser.test_validate_with_pydantic_failure()
        print()
        
        test_parser.setup_method()
        test_parser.test_parse_and_validate_complete()
        print()
        
        test_parser.setup_method()
        test_parser.test_extract_xml_from_content()
        print()
        
        test_parser.setup_method()
        test_parser.test_extract_xml_not_found()
        print()
        
        test_parser.setup_method()
        test_parser.test_invalid_xml_format()
        
        print("\n🎉 所有XML解析器测试都通过了！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
