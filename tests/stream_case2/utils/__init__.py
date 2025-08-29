"""
工具函数模块
"""

from .logger import logger
from .xml_parser import XMLParser, XMLValidationError

__all__ = ["logger", "XMLParser", "XMLValidationError"]

