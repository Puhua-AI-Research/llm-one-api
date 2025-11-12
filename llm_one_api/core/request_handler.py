"""
请求处理器

负责处理和转换请求参数
"""

from typing import Dict, Any

from llm_one_api.models.request import (
    ChatCompletionRequest,
    CompletionRequest,
    EmbeddingRequest,
)
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class RequestHandler:
    """请求处理器"""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
    
    def process_chat_request(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """
        处理聊天请求
        
        Args:
            request: 聊天请求对象
            
        Returns:
            处理后的请求字典
        """
        # 转换为字典
        request_dict = request.model_dump(exclude_none=True)
        
        # 如果有适配器，可以在这里进行格式转换
        adapter_type = self.model_config.get("adapter")
        if adapter_type and adapter_type != "openai":
            # TODO: 调用适配器进行格式转换
            pass
        
        logger.debug(f"处理后的请求: {request_dict}")
        return request_dict
    
    def process_completion_request(self, request: CompletionRequest) -> Dict[str, Any]:
        """
        处理文本补全请求
        
        Args:
            request: 补全请求对象
            
        Returns:
            处理后的请求字典
        """
        request_dict = request.model_dump(exclude_none=True)
        
        adapter_type = self.model_config.get("adapter")
        if adapter_type and adapter_type != "openai":
            # TODO: 调用适配器进行格式转换
            pass
        
        logger.debug(f"处理后的请求: {request_dict}")
        return request_dict
    
    def process_embedding_request(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """
        处理嵌入请求
        
        Args:
            request: 嵌入请求对象
            
        Returns:
            处理后的请求字典
        """
        request_dict = request.model_dump(exclude_none=True)
        
        adapter_type = self.model_config.get("adapter")
        if adapter_type and adapter_type != "openai":
            # TODO: 调用适配器进行格式转换
            pass
        
        logger.debug(f"处理后的请求: {request_dict}")
        return request_dict

