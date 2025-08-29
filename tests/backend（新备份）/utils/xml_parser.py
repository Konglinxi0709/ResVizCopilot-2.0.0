"""
XML解析工具
支持将XML文本解析为dict，并使用Pydantic验证器验证合法性
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, Type, Optional, Union
from pydantic import BaseModel, ValidationError

from .logger import logger


class XMLValidationError(Exception):
    """XML验证错误"""
    pass


class XMLParser:
    """
    XML解析器
    
    功能：
    1. 将XML文本解析为Python字典
    2. 使用Pydantic验证器验证数据合法性
    3. 支持嵌套结构和列表处理
    """
    
    def __init__(self):
        """初始化XML解析器"""
        logger.info("XML解析器初始化完成")
    
    def xml_to_dict(self, xml_text: str) -> Dict[str, Any]:
        """
        将XML文本解析为字典
        
        Args:
            xml_text: XML文本内容
            
        Returns:
            解析后的字典
            
        Raises:
            XMLValidationError: XML格式错误
        """
        try:
            # 清理XML文本（移除多余的空白字符）
            xml_text = xml_text.strip()
            
            # 解析XML
            root = ET.fromstring(xml_text)
            
            # 转换为字典
            result = self._element_to_dict(root)
            
            logger.debug(f"XML解析成功: {result}")
            return result
            
        except ET.ParseError as e:
            error_msg = f"XML解析失败: {str(e)}"
            logger.error(error_msg)
            raise XMLValidationError(error_msg)
        except Exception as e:
            error_msg = f"XML处理失败: {str(e)}"
            logger.error(error_msg)
            raise XMLValidationError(error_msg)
    
    def _element_to_dict(self, element: ET.Element) -> Union[Dict[str, Any], str, None]:
        """
        将XML元素转换为字典
        
        Args:
            element: XML元素
            
        Returns:
            转换后的字典或字符串
        """
        # 如果元素有子元素
        if len(element) > 0:
            result = {}
            
            for child in element:
                child_data = self._element_to_dict(child)
                
                # 处理重复的标签名（转换为列表）
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            # 如果还有文本内容，添加到结果中
            if element.text and element.text.strip():
                result['_text'] = element.text.strip()
            
            # 添加属性
            if element.attrib:
                result['_attributes'] = element.attrib
            
            return result
        else:
            # 叶子节点，返回文本内容
            text = element.text.strip() if element.text else ""
            
            # 如果有属性，返回字典
            if element.attrib:
                return {
                    '_text': text,
                    '_attributes': element.attrib
                }
            
            # 否则返回文本
            return text if text else None
    
    def validate_with_pydantic(self, data: Dict[str, Any], validator_class: Type[BaseModel]) -> BaseModel:
        """
        使用Pydantic验证器验证数据
        
        Args:
            data: 要验证的数据字典
            validator_class: Pydantic验证器类
            
        Returns:
            验证后的数据对象
            
        Raises:
            XMLValidationError: 验证失败
        """
        try:
            # 使用Pydantic验证器验证数据
            validated_data = validator_class(**data)
            
            logger.debug(f"数据验证成功: {validator_class.__name__}")
            return validated_data
            
        except ValidationError as e:
            error_msg = f"数据验证失败: {str(e)}"
            logger.error(error_msg)
            raise XMLValidationError(error_msg)
        except Exception as e:
            error_msg = f"验证过程出错: {str(e)}"
            logger.error(error_msg)
            raise XMLValidationError(error_msg)
    
    def parse_and_validate(self, xml_text: str, validator_class: Type[BaseModel]) -> BaseModel:
        """
        解析XML并验证数据
        
        Args:
            xml_text: XML文本
            validator_class: Pydantic验证器类
            
        Returns:
            验证后的数据对象
            
        Raises:
            XMLValidationError: 解析或验证失败
        """
        # 第一步：解析XML为字典
        data_dict = self.xml_to_dict(xml_text)
        
        # 第二步：使用Pydantic验证器验证
        validated_data = self.validate_with_pydantic(data_dict, validator_class)
        
        logger.info(f"XML解析和验证完成: {validator_class.__name__}")
        return validated_data
    
    def extract_xml_from_content(self, content: str, tag_name: str) -> Optional[str]:
        """
        从文本内容中提取XML片段
        
        Args:
            content: 文本内容
            tag_name: XML标签名
            
        Returns:
            提取的XML片段，如果没有找到返回None
        """
        try:
            import re
            
            # 构建匹配模式
            pattern = f"<{tag_name}[^>]*>.*?</{tag_name}>"
            
            # 搜索XML片段
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                xml_fragment = match.group(0)
                logger.debug(f"提取到XML片段: {tag_name}")
                return xml_fragment
            else:
                logger.debug(f"未找到XML片段: {tag_name}")
                return None
                
        except Exception as e:
            logger.error(f"提取XML片段失败: {e}")
            return None
