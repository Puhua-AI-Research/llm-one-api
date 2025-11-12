"""
FastAPI 应用实例

创建并配置 FastAPI 应用，注册路由和中间件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from llm_one_api import __version__
from llm_one_api.api.routes import chat, completions, embeddings, models, stats
from llm_one_api.middleware.auth import AuthMiddleware
from llm_one_api.middleware.logging import LoggingMiddleware
from llm_one_api.middleware.rate_limit import RateLimitMiddleware
from llm_one_api.plugins.manager import PluginManager
from llm_one_api.config.settings import get_settings
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 LLM One API 正在启动...")
    
    # 加载配置
    settings = get_settings()
    logger.info(f"📝 配置加载完成")
    
    # 初始化插件系统
    plugin_manager = PluginManager(settings)
    await plugin_manager.load_plugins()
    app.state.plugin_manager = plugin_manager
    logger.info(f"🔌 插件系统初始化完成")
    
    logger.info(f"✅ LLM One API v{__version__} 启动成功")
    
    yield
    
    # 关闭时
    logger.info("🛑 LLM One API 正在关闭...")
    await plugin_manager.cleanup()
    logger.info("👋 LLM One API 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="LLM One API",
    description="统一的大模型中转服务，兼容 OpenAI API",
    version=__version__,
    lifespan=lifespan,
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 添加自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

# 添加限流中间件（如果启用）
settings = get_settings()
if settings.rate_limit.get("enabled", False):
    requests_per_minute = settings.rate_limit.get("requests_per_minute", 60)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=requests_per_minute)
    logger.info(f"🚦 限流已启用: {requests_per_minute} 请求/分钟")


# 注册路由
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(completions.router, prefix="/v1", tags=["completions"])
app.include_router(embeddings.router, prefix="/v1", tags=["embeddings"])
app.include_router(models.router, prefix="/v1", tags=["models"])
app.include_router(stats.router, prefix="/v1", tags=["stats"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "LLM One API",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

