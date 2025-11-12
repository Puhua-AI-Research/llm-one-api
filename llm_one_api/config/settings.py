"""
配置加载和管理

使用 pydantic-settings 从配置文件和环境变量加载配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置（可以是嵌套的 server 字段，也可以是直接的字段）
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")
    workers: int = Field(default=4, description="工作进程数")
    log_level: str = Field(default="info", description="日志级别")
    
    # 插件配置
    plugins: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auth": "default_auth",
            "model_route": "default_router",
            "stats": ["log"],
        },
        description="插件配置"
    )
    
    # 认证配置
    auth: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_auth": {
                "api_keys": ["sk-test-key"]
            }
        },
        description="认证配置"
    )
    
    # 模型配置
    models: Dict[str, Any] = Field(
        default_factory=lambda: {
            "gpt-3.5-turbo": {
                "api_base": "https://api.openai.com/v1",
                "api_key": "your-openai-key",
                "timeout": 60,
            }
        },
        description="模型配置"
    )
    
    # 统计配置
    stats: Dict[str, Any] = Field(
        default_factory=lambda: {
            "log": {
                "format": "json"
            }
        },
        description="统计配置"
    )
    
    # 限流配置
    rate_limit: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": False,
            "requests_per_minute": 60,
        },
        description="限流配置"
    )
    
    class Config:
        env_prefix = "LLM_ONE_API_"
        case_sensitive = False
        extra = "allow"  # 允许额外的字段（如 server, logging 等）


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    Returns:
        配置对象
    """
    # 检查是否指定了配置文件
    config_path = os.environ.get("LLM_ONE_API_CONFIG")
    
    if config_path and Path(config_path).exists():
        logger.info(f"从配置文件加载配置: {config_path}")
        config_data = load_config_file(config_path)
        return Settings(**config_data)
    
    # 检查默认配置文件位置
    default_paths = [
        Path("config.yaml"),
        Path("config.yml"),
        Path.home() / ".llm-one-api" / "config.yaml",
        Path("/etc/llm-one-api/config.yaml"),
    ]
    
    for path in default_paths:
        if path.exists():
            logger.info(f"从默认位置加载配置: {path}")
            config_data = load_config_file(str(path))
            return Settings(**config_data)
    
    # 使用默认配置
    logger.info("使用默认配置")
    return Settings()


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    从 YAML 文件加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
            if not config_data:
                return {}
            
            # 处理嵌套的 server 配置
            if 'server' in config_data and isinstance(config_data['server'], dict):
                server_config = config_data.pop('server')
                # 将 server 下的配置提升到顶层
                config_data.setdefault('host', server_config.get('host', '0.0.0.0'))
                config_data.setdefault('port', server_config.get('port', 8000))
                config_data.setdefault('workers', server_config.get('workers', 4))
                config_data.setdefault('log_level', server_config.get('log_level', 'info'))
            
            return config_data
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


def reload_settings():
    """重新加载配置（清除缓存）"""
    get_settings.cache_clear()

