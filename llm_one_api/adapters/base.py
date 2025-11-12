"""
适配器基类

定义适配器接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAdapter(ABC):
    """适配器基类"""
    
    @abstractmethod
    def convert_request(self, openai_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 OpenAI 格式的请求转换为目标格式
        
        Args:
            openai_request: OpenAI 格式的请求
            
        Returns:
            目标格式的请求
        """
        pass
    
    @abstractmethod
    def convert_response(self, provider_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        将提供商的响应转换为 OpenAI 格式
        
        Args:
            provider_response: 提供商的原始响应
            
        Returns:
            OpenAI 格式的响应
        """
        pass
    
    @abstractmethod
    def convert_stream_chunk(self, provider_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        将流式响应块转换为 OpenAI 格式
        
        Args:
            provider_chunk: 提供商的流式数据块
            
        Returns:
            OpenAI 格式的流式数据块
        """
        pass

