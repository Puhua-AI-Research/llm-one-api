"""
Token 计数工具

使用 tiktoken 库计算文本的 token 数量
"""

from typing import List, Dict, Any, Optional


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    计算文本的 token 数量
    
    Args:
        text: 文本内容
        model: 模型名称
        
    Returns:
        token 数量
    """
    try:
        import tiktoken
        
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 如果模型不支持，使用默认编码器
            encoding = tiktoken.get_encoding("cl100k_base")
        
        tokens = encoding.encode(text)
        return len(tokens)
    
    except ImportError:
        # 如果没有安装 tiktoken，使用粗略估算
        # 英文：1 token ≈ 4 字符
        # 中文：1 token ≈ 1.5-2 字符
        return max(len(text) // 4, 1)


def count_chat_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    """
    计算聊天消息的 token 数量
    
    Args:
        messages: 消息列表
        model: 模型名称
        
    Returns:
        token 数量
    """
    try:
        import tiktoken
        
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        # 根据 OpenAI 的计算方式
        # 每条消息有固定开销：4 tokens (role, content, name)
        # 整个对话有固定开销：3 tokens
        num_tokens = 3
        
        for message in messages:
            num_tokens += 4  # 每条消息的固定开销
            for key, value in message.items():
                if value:
                    num_tokens += len(encoding.encode(str(value)))
        
        return num_tokens
    
    except ImportError:
        # 粗略估算
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return max(total_chars // 4, 1)


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-3.5-turbo",
) -> float:
    """
    估算请求的成本（美元）
    
    Args:
        prompt_tokens: 提示 token 数
        completion_tokens: 补全 token 数
        model: 模型名称
        
    Returns:
        成本（美元）
    """
    # 价格表（截至 2024 年，单位：美元/1K tokens）
    PRICING = {
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    }
    
    # 查找价格
    pricing = PRICING.get(model)
    if not pricing:
        # 使用默认价格（GPT-3.5）
        pricing = PRICING["gpt-3.5-turbo"]
    
    # 计算成本
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    
    return prompt_cost + completion_cost

