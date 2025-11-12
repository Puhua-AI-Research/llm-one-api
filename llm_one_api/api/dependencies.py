"""
FastAPI 依赖注入

提供常用的依赖项，如插件管理器、配置等
"""

from fastapi import Request, Depends, HTTPException, status
from typing import Optional

from llm_one_api.plugins.manager import PluginManager
from llm_one_api.config.settings import Settings, get_settings


def get_plugin_manager(request: Request) -> PluginManager:
    """获取插件管理器"""
    return request.app.state.plugin_manager


def get_current_settings() -> Settings:
    """获取当前配置"""
    return get_settings()


async def verify_api_key(request: Request) -> dict:
    """
    验证 API Key（通过认证中间件）
    
    中间件会将认证结果存储在 request.state.auth_result
    """
    if not hasattr(request.state, "auth_result"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    if not request.state.auth_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=request.state.auth_result.get("message", "Authentication failed"),
        )
    
    return request.state.auth_result

