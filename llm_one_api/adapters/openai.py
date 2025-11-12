"""
OpenAI 适配器

直接透传，无需转换
"""

from typing import Dict, Any
from llm_one_api.adapters.base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """OpenAI 适配器（直接透传）"""
    
    def convert_request(self, openai_request: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 格式直接返回"""
        return openai_request
    
    def convert_response(self, provider_response: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 格式直接返回"""
        return provider_response
    
    def convert_stream_chunk(self, provider_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 格式直接返回"""
        return provider_chunk

