"""
配置管理模块
使用环境变量和默认值管理应用配置
"""
import os
from typing import Optional
from dotenv import load_dotenv  # 新增：用于加载.env文件

# 加载.env文件中的环境变量
load_dotenv()


class Settings:
    """应用配置类"""
    
    # DeepSeek API 配置 - 不再包含默认API密钥
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    print(DEEPSEEK_API_KEY)
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    # 代理配置
    HTTP_PROXY: Optional[str] = os.getenv("HTTP_PROXY", None)
    HTTPS_PROXY: Optional[str] = os.getenv("HTTPS_PROXY", None)
    NO_PROXY: Optional[str] = os.getenv("NO_PROXY", None)
    
    # 模型配置
    DEEPSEEK_REASONER_MODEL: str = os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-reasoner")
    DEEPSEEK_V3_MODEL: str = os.getenv("DEEPSEEK_V3_MODEL", "deepseek-chat")
    
    # 服务配置
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8008"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # LLM配置
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "4000"))
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    @classmethod
    def validate(cls) -> None:
        """验证配置"""
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is required")
        if not cls.DEEPSEEK_BASE_URL:
            raise ValueError("DEEPSEEK_BASE_URL is required")
    
    @classmethod
    def get_proxy_config(cls) -> dict:
        """获取代理配置字典"""
        proxy_config = {}
        
        # 设置环境变量，让httpx库自动使用
        if cls.HTTP_PROXY:
            proxy_config["http_proxy"] = cls.HTTP_PROXY
        if cls.HTTPS_PROXY:
            proxy_config["https_proxy"] = cls.HTTPS_PROXY
        if cls.NO_PROXY:
            proxy_config["no_proxy"] = cls.NO_PROXY
            
        return proxy_config


# 创建全局配置实例
settings = Settings()

# 验证配置
try:
    settings.validate()
except ValueError as e:
    print(f"配置验证失败: {e}")
    print("请设置相应的环境变量或在此文件中修改默认值")