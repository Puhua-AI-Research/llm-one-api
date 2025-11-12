"""
插件接口定义
"""

from llm_one_api.plugins.interfaces.auth import AuthPlugin, AuthResult
from llm_one_api.plugins.interfaces.model_route import ModelRoutePlugin, ModelConfig
from llm_one_api.plugins.interfaces.stats import StatsPlugin, RequestInfo, ResponseInfo

__all__ = [
    "AuthPlugin",
    "AuthResult",
    "ModelRoutePlugin",
    "ModelConfig",
    "StatsPlugin",
    "RequestInfo",
    "ResponseInfo",
]

