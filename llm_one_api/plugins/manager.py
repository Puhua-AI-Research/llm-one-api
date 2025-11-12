"""
插件管理器

负责加载、管理和调用插件
"""

import sys
from typing import Dict, Any, List, Optional
from importlib.metadata import entry_points

from llm_one_api.plugins.interfaces import (
    AuthPlugin,
    ModelRoutePlugin,
    StatsPlugin,
    AuthResult,
    ModelConfig,
)
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self, settings):
        """
        初始化插件管理器
        
        Args:
            settings: 应用配置
        """
        self.settings = settings
        self.auth_plugin: Optional[AuthPlugin] = None
        self.model_route_plugin: Optional[ModelRoutePlugin] = None
        self.stats_plugins: List[StatsPlugin] = []
    
    async def load_plugins(self):
        """加载所有插件"""
        logger.info("开始加载插件...")
        
        # 加载认证插件
        await self._load_auth_plugin()
        
        # 加载模型路由插件
        await self._load_model_route_plugin()
        
        # 加载统计插件
        await self._load_stats_plugins()
        
        logger.info("插件加载完成")
    
    async def _load_auth_plugin(self):
        """加载认证插件"""
        plugin_name = self.settings.plugins.get("auth", "simple")
        
        try:
            # 通过 entry_points 查找插件
            if sys.version_info >= (3, 10):
                eps = entry_points(group="llm_one_api.auth")
            else:
                eps = entry_points().get("llm_one_api.auth", [])
            
            for ep in eps:
                if ep.name == plugin_name:
                    plugin_class = ep.load()
                    config = self.settings.auth.get(plugin_name, {})
                    self.auth_plugin = plugin_class(config)
                    await self.auth_plugin.initialize()
                    logger.info(f"✅ 认证插件加载成功: {plugin_name}")
                    return
            
            # 如果没有找到，尝试加载内置插件
            logger.warning(f"未找到认证插件 '{plugin_name}'，尝试加载内置插件")
            await self._load_builtin_auth_plugin(plugin_name)
        
        except Exception as e:
            logger.error(f"❌ 加载认证插件失败: {e}")
            # 使用默认插件
            await self._load_builtin_auth_plugin("simple")
    
    async def _load_builtin_auth_plugin(self, plugin_name: str):
        """加载内置认证插件"""
        try:
            if plugin_name == "simple":
                from llm_one_api.plugins.builtin.simple_auth import SimpleAuthPlugin
                config = self.settings.auth.get("simple", {})
                self.auth_plugin = SimpleAuthPlugin(config)
                await self.auth_plugin.initialize()
                logger.info(f"✅ 内置认证插件加载成功: {plugin_name}")
        except Exception as e:
            logger.error(f"❌ 加载内置认证插件失败: {e}")
    
    async def _load_model_route_plugin(self):
        """加载模型路由插件"""
        plugin_name = self.settings.plugins.get("model_route", "config")
        
        try:
            # 通过 entry_points 查找插件
            if sys.version_info >= (3, 10):
                eps = entry_points(group="llm_one_api.model_route")
            else:
                eps = entry_points().get("llm_one_api.model_route", [])
            
            for ep in eps:
                if ep.name == plugin_name:
                    plugin_class = ep.load()
                    config = self.settings.models
                    self.model_route_plugin = plugin_class(config)
                    await self.model_route_plugin.initialize()
                    logger.info(f"✅ 模型路由插件加载成功: {plugin_name}")
                    return
            
            # 如果没有找到，尝试加载内置插件
            logger.warning(f"未找到模型路由插件 '{plugin_name}'，尝试加载内置插件")
            await self._load_builtin_model_route_plugin(plugin_name)
        
        except Exception as e:
            logger.error(f"❌ 加载模型路由插件失败: {e}")
            await self._load_builtin_model_route_plugin("config")
    
    async def _load_builtin_model_route_plugin(self, plugin_name: str):
        """加载内置模型路由插件"""
        try:
            if plugin_name == "config":
                from llm_one_api.plugins.builtin.config_router import ConfigRouterPlugin
                config = self.settings.models
                logger.debug(f"模型配置内容: {config}")
                
                if not config:
                    logger.error("❌ 模型配置为空！请检查配置文件中的 models 字段")
                    return
                
                self.model_route_plugin = ConfigRouterPlugin(config)
                await self.model_route_plugin.initialize()
                logger.info(f"✅ 内置模型路由插件加载成功: {plugin_name}")
        except Exception as e:
            logger.exception(f"❌ 加载内置模型路由插件失败: {e}")
    
    async def _load_stats_plugins(self):
        """加载统计插件（可以有多个）"""
        plugin_names = self.settings.plugins.get("stats", ["log"])
        
        if isinstance(plugin_names, str):
            plugin_names = [plugin_names]
        
        for plugin_name in plugin_names:
            try:
                # 通过 entry_points 查找插件
                if sys.version_info >= (3, 10):
                    eps = entry_points(group="llm_one_api.stats")
                else:
                    eps = entry_points().get("llm_one_api.stats", [])
                
                for ep in eps:
                    if ep.name == plugin_name:
                        plugin_class = ep.load()
                        config = self.settings.stats.get(plugin_name, {})
                        plugin = plugin_class(config)
                        await plugin.initialize()
                        self.stats_plugins.append(plugin)
                        logger.info(f"✅ 统计插件加载成功: {plugin_name}")
                        break
                else:
                    # 如果没有找到，尝试加载内置插件
                    await self._load_builtin_stats_plugin(plugin_name)
            
            except Exception as e:
                logger.error(f"❌ 加载统计插件失败: {plugin_name} - {e}")
    
    async def _load_builtin_stats_plugin(self, plugin_name: str):
        """加载内置统计插件"""
        try:
            if plugin_name == "log":
                from llm_one_api.plugins.builtin.log_stats import LogStatsPlugin
                config = self.settings.stats.get("log", {})
                plugin = LogStatsPlugin(config)
                await plugin.initialize()
                self.stats_plugins.append(plugin)
                logger.info(f"✅ 内置统计插件加载成功: {plugin_name}")
            elif plugin_name == "memory":
                from llm_one_api.plugins.builtin.memory_stats import MemoryStatsPlugin
                config = self.settings.stats.get("memory", {})
                plugin = MemoryStatsPlugin(config)
                await plugin.initialize()
                self.stats_plugins.append(plugin)
                logger.info(f"✅ 内置统计插件加载成功: {plugin_name}")
        except Exception as e:
            logger.error(f"❌ 加载内置统计插件失败: {plugin_name} - {e}")
    
    async def authenticate(self, api_key: str) -> AuthResult:
        """
        认证 API Key
        
        Args:
            api_key: API 密钥
            
        Returns:
            认证结果
        """
        if not self.auth_plugin:
            return AuthResult(success=False, message="认证插件未加载")
        
        try:
            result = await self.auth_plugin.authenticate(api_key)
            return result
        except Exception as e:
            logger.error(f"认证失败: {e}")
            return AuthResult(success=False, message=f"认证错误: {str(e)}")
    
    async def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置字典
        """
        if not self.model_route_plugin:
            logger.error("❌ 模型路由插件未加载！可能是插件初始化失败")
            return None
        
        try:
            logger.debug(f"尝试获取模型配置: {model_name}")
            model_config = await self.model_route_plugin.get_model_config(model_name)
            
            if model_config:
                # 将 dataclass 转换为字典
                if hasattr(model_config, "__dict__"):
                    config_dict = vars(model_config)
                    
                    # 如果原始配置有 upstreams，添加到返回的字典中（用于负载均衡）
                    if hasattr(self.model_route_plugin, 'models') and model_name in self.model_route_plugin.models:
                        original_config = self.model_route_plugin.models[model_name]
                        if "upstreams" in original_config:
                            config_dict["upstreams"] = original_config["upstreams"]
                            logger.debug(f"添加负载均衡配置: {len(original_config['upstreams'])} 个上游")
                    
                    logger.debug(f"模型配置获取成功: {model_name} -> {config_dict.get('api_base')}")
                    return config_dict
                return model_config
            
            logger.warning(f"⚠️  模型 {model_name} 未在配置中找到")
            return None
        except Exception as e:
            logger.exception(f"❌ 获取模型配置失败: {e}")
            return None
    
    async def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用模型
        
        Returns:
            模型字典
        """
        if not self.model_route_plugin:
            return {}
        
        try:
            return await self.model_route_plugin.list_models()
        except Exception as e:
            logger.error(f"列出模型失败: {e}")
            return {}
    
    async def record_request_stats(self, stats_data: Dict[str, Any]):
        """
        记录请求统计
        
        Args:
            stats_data: 统计数据
        """
        for plugin in self.stats_plugins:
            try:
                # 简化版本：直接传递字典，不使用 dataclass
                await plugin.record_response(stats_data)
            except Exception as e:
                logger.error(f"记录统计失败 ({plugin.__class__.__name__}): {e}")
    
    async def cleanup(self):
        """清理所有插件"""
        logger.info("开始清理插件...")
        
        if self.auth_plugin:
            try:
                await self.auth_plugin.cleanup()
            except Exception as e:
                logger.error(f"清理认证插件失败: {e}")
        
        if self.model_route_plugin:
            try:
                await self.model_route_plugin.cleanup()
            except Exception as e:
                logger.error(f"清理模型路由插件失败: {e}")
        
        for plugin in self.stats_plugins:
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"清理统计插件失败: {e}")
        
        logger.info("插件清理完成")

