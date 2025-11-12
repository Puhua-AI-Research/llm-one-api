"""
CORS 中间件配置

注：实际上 FastAPI 已经内置了 CORSMiddleware，这里只是作为配置示例
"""

from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app, allowed_origins: list = None):
    """
    配置 CORS 中间件
    
    Args:
        app: FastAPI 应用实例
        allowed_origins: 允许的域名列表，默认允许所有
    """
    if allowed_origins is None:
        allowed_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

