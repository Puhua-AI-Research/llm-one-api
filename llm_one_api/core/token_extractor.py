"""
Token 提取器

从响应中提取 token 使用量信息
支持流式和非流式响应
"""

from typing import Dict, Any, Optional

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class TokenExtractor:
    """Token 提取器"""
    
    @staticmethod
    def extract_from_response(response_data: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """
        从非流式响应中提取 token 使用量
        
        Args:
            response_data: 响应数据
            
        Returns:
            token 使用量字典，包含 prompt_tokens, completion_tokens, total_tokens
        """
        usage = response_data.get("usage", {})
        
        if not usage:
            logger.debug("响应中未找到 usage 字段")
            return None
        
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        
        logger.debug(f"提取的 token 使用量: {token_usage}")
        return token_usage
    
    @staticmethod
    def extract_from_stream_chunk(chunk_data: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """
        从流式响应块中提取 token 使用量
        
        OpenAI 在流式响应的最后一个块中包含 usage 字段
        
        Args:
            chunk_data: 流式响应块
            
        Returns:
            token 使用量字典，如果该块不包含 usage 则返回 None
        """
        usage = chunk_data.get("usage", {})
        
        if not usage:
            return None
        
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        
        logger.debug(f"从流式块中提取的 token 使用量: {token_usage}")
        return token_usage
    
    @staticmethod
    def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        估算文本的 token 数量（使用 tiktoken）
        
        当无法从响应中获取准确的 token 数量时使用
        
        Args:
            text: 文本内容
            model: 模型名称
            
        Returns:
            估算的 token 数量
        """
        try:
            import tiktoken
            
            # 获取对应模型的编码器
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # 如果模型不支持，使用默认编码器
                encoding = tiktoken.get_encoding("cl100k_base")
            
            tokens = encoding.encode(text)
            return len(tokens)
        
        except ImportError:
            # 如果没有安装 tiktoken，使用粗略估算（1 token ≈ 4 字符）
            logger.warning("tiktoken 未安装，使用粗略估算")
            return len(text) // 4
        
        except Exception as e:
            logger.error(f"估算 token 失败: {e}")
            return 0

