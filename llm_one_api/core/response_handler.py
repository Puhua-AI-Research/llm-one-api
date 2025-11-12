"""
响应处理器

负责处理和转换响应数据
"""

from typing import Dict, Any

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResponseHandler:
    """响应处理器"""
    
    @staticmethod
    def process_response(response_data: Dict[str, Any], adapter_type: str = "openai") -> Dict[str, Any]:
        """
        处理响应数据
        
        Args:
            response_data: 原始响应数据
            adapter_type: 适配器类型
            
        Returns:
            处理后的响应数据
        """
        # 如果不是 OpenAI 格式，需要转换
        if adapter_type and adapter_type != "openai":
            # TODO: 调用适配器进行格式转换
            pass
        
        return response_data
    
    @staticmethod
    def create_error_response(error_message: str, error_type: str = "api_error") -> Dict[str, Any]:
        """
        创建错误响应
        
        Args:
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            错误响应字典
        """
        return {
            "error": {
                "message": error_message,
                "type": error_type,
                "code": None,
            }
        }

