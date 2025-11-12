"""
简单认证插件

基于配置文件的 API Key 列表进行认证
"""

from typing import Dict, Any

from llm_one_api.plugins.interfaces.auth import AuthPlugin, AuthResult
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class SimpleAuthPlugin(AuthPlugin):
    """简单认证插件"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_keys = set(config.get("api_keys", []))
        logger.info(f"简单认证插件初始化，共 {len(self.api_keys)} 个 API Key")
    
    async def authenticate(self, api_key: str) -> AuthResult:
        """
        验证 API Key 是否在允许列表中
        
        Args:
            api_key: API 密钥
            
        Returns:
            认证结果
        """
        if not api_key:
            return AuthResult(
                success=False,
                message="API Key 不能为空",
            )
        
        if api_key in self.api_keys:
            logger.debug(f"API Key 认证成功: {api_key[:10]}...")
            return AuthResult(
                success=True,
                user_id=api_key[:10],  # 使用前10位作为用户ID
                message="认证成功",
            )
        
        logger.warning(f"API Key 认证失败: {api_key[:10]}...")
        return AuthResult(
            success=False,
            message="无效的 API Key",
        )
    
    async def initialize(self):
        """初始化插件"""
        if not self.api_keys:
            logger.warning("⚠️  未配置任何 API Key，所有请求将被拒绝")
    
    async def cleanup(self):
        """清理插件"""
        pass

