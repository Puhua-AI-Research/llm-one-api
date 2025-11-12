"""
模型路由插件接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    api_base: str
    api_key: str
    adapter: str = "openai"  # 适配器类型：openai, anthropic, etc.
    timeout: int = 60
    max_retries: int = 3
    
    # 元数据（可选信息统一放这里）
    # 常用字段：
    #   - max_tokens: 模型最大 token 数
    #   - max_input_tokens: 最大输入 token 数
    #   - max_output_tokens: 最大输出 token 数
    #   - price_per_1k_prompt_tokens: 输入价格（美元/1K tokens）
    #   - price_per_1k_completion_tokens: 输出价格（美元/1K tokens）
    #   - 其他自定义字段...
    metadata: Optional[Dict[str, Any]] = None


class ModelRoutePlugin(ABC):
    """模型路由插件接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模型路由插件
        
        Args:
            config: 插件配置
        """
        self.config = config
    
    @abstractmethod
    async def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        获取模型对应的配置（中转地址、密钥等）
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置，如果模型不存在返回 None
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用的模型
        
        Returns:
            模型字典，key 为模型名称，value 为模型信息
        """
        pass
    
    async def initialize(self):
        """插件初始化（可选）"""
        pass
    
    async def cleanup(self):
        """插件清理（可选）"""
        pass

