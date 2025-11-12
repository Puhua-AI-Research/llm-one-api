"""
认证中间件

从请求头中提取 API Key 并进行认证
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    # 不需要认证的路径
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求认证
        
        从 Authorization 头中提取 Bearer Token 并验证
        """
        # 跳过不需要认证的路径
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # 提取 API Key
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            logger.warning(f"请求缺少 Authorization 头: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "缺少 Authorization 头",
                        "type": "authentication_error",
                    }
                }
            )
        
        # 解析 Bearer Token
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Authorization 头格式错误: {auth_header}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Authorization 头格式错误，应为: Bearer <token>",
                        "type": "authentication_error",
                    }
                }
            )
        
        api_key = parts[1]
        
        # 调用插件进行认证
        try:
            plugin_manager = request.app.state.plugin_manager
            auth_result = await plugin_manager.authenticate(api_key)
            
            if not auth_result.success:
                logger.warning(f"认证失败: {auth_result.message}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "message": auth_result.message or "认证失败",
                            "type": "authentication_error",
                        }
                    }
                )
            
            # 将认证结果保存到 request.state 供后续使用
            request.state.auth_result = {
                "success": True,
                "user_id": auth_result.user_id,
                "metadata": auth_result.metadata,
            }
            
            logger.debug(f"认证成功: user_id={auth_result.user_id}")
        
        except Exception as e:
            logger.exception(f"认证过程出错: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "认证服务错误",
                        "type": "internal_error",
                    }
                }
            )
        
        # 继续处理请求
        response = await call_next(request)
        return response

