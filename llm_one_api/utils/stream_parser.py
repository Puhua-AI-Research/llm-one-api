"""
流式响应解析工具

解析 SSE (Server-Sent Events) 格式的流式响应
"""

import json
from typing import Dict, Any, Optional, AsyncIterator


def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
    """
    解析单行 SSE 数据
    
    Args:
        line: SSE 数据行
        
    Returns:
        解析后的数据字典，如果无法解析则返回 None
    """
    # 跳过空行
    if not line.strip():
        return None
    
    # SSE 格式：data: {...}
    if line.startswith("data: "):
        data_str = line[6:].strip()
        
        # 检查是否是结束标记
        if data_str == "[DONE]":
            return {"done": True}
        
        # 解析 JSON
        try:
            data = json.loads(data_str)
            return data
        except json.JSONDecodeError:
            return None
    
    return None


async def stream_with_usage(
    stream: AsyncIterator[str],
) -> AsyncIterator[Dict[str, Any]]:
    """
    从流式响应中提取数据和 usage 信息
    
    Args:
        stream: 原始流式响应
        
    Yields:
        解析后的数据块
    """
    last_usage = None
    
    async for line in stream:
        data = parse_sse_line(line)
        
        if not data:
            continue
        
        # 提取 usage 信息
        if "usage" in data:
            last_usage = data["usage"]
        
        yield data
    
    # 返回最后的 usage 信息
    if last_usage:
        yield {"usage": last_usage, "final": True}


def extract_content_from_chunk(chunk: Dict[str, Any]) -> Optional[str]:
    """
    从流式响应块中提取内容
    
    Args:
        chunk: 响应数据块
        
    Returns:
        提取的内容，如果没有内容返回 None
    """
    # Chat completion 格式
    if "choices" in chunk:
        choices = chunk.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            return delta.get("content")
    
    # Text completion 格式
    if "text" in chunk:
        return chunk.get("text")
    
    return None

