"""
认证插件接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AuthResult:
    """认证结果"""
    success: bool
    user_id: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuthPlugin(ABC):
    """认证插件接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化认证插件
        
        Args:
            config: 插件配置
        """
        self.config = config
    
    @abstractmethod
    async def authenticate(self, api_key: str) -> AuthResult:
        """
        验证 API Key 是否有效
        
        Args:
            api_key: API 密钥
            
        Returns:
            认证结果
        """
        pass
    
    async def initialize(self):
        """插件初始化（可选）"""
        pass
    
    async def cleanup(self):
        """插件清理（可选）"""
        pass

