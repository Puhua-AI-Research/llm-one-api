"""
统计插件接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RequestInfo:
    """请求信息"""
    request_id: str
    user_id: Optional[str]
    model: str
    endpoint: str  # chat, completion, embedding
    stream: bool
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResponseInfo:
    """响应信息"""
    request_id: str
    user_id: Optional[str]
    model: str
    endpoint: str
    stream: bool
    timestamp: datetime
    duration: float  # 秒
    token_usage: Optional[Dict[str, int]] = None  # prompt_tokens, completion_tokens, total_tokens
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StatsPlugin(ABC):
    """统计插件接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化统计插件
        
        Args:
            config: 插件配置
        """
        self.config = config
    
    @abstractmethod
    async def record_request(self, request_info: RequestInfo):
        """
        记录请求信息
        
        Args:
            request_info: 请求信息
        """
        pass
    
    @abstractmethod
    async def record_response(self, response_info: ResponseInfo):
        """
        记录响应信息和 token 消耗
        
        Args:
            response_info: 响应信息
        """
        pass
    
    async def initialize(self):
        """插件初始化（可选）"""
        pass
    
    async def cleanup(self):
        """插件清理（可选）"""
        pass

