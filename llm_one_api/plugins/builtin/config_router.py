"""
配置文件路由插件

从配置文件读取模型路由信息
"""

from typing import Dict, Any, Optional

from llm_one_api.plugins.interfaces.model_route import ModelRoutePlugin, ModelConfig
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfigRouterPlugin(ModelRoutePlugin):
    """配置文件路由插件"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.models = config  # config 就是 models 配置
        logger.info(f"配置文件路由插件初始化，共 {len(self.models)} 个模型")
    
    async def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        从配置中获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置
        """
        model_conf = self.models.get(model_name)
        
        if not model_conf:
            logger.warning(f"模型 {model_name} 未在配置中找到")
            return None
        
        try:
            # 检查是否是负载均衡配置（upstreams 数组）
            if "upstreams" in model_conf and isinstance(model_conf["upstreams"], list):
                # 负载均衡配置：使用第一个上游的信息创建 ModelConfig
                # 完整的 upstreams 信息会被 forwarder 使用
                first_upstream = model_conf["upstreams"][0]
                
                # 从第一个 upstream 或顶层获取 metadata
                metadata = first_upstream.get("metadata", {}) or model_conf.get("metadata", {}) or {}
                
                # 将可选配置字段放入 metadata
                optional_fields = [
                    "max_tokens",
                    "max_input_tokens", 
                    "max_output_tokens",
                    "price_per_1k_prompt_tokens",
                    "price_per_1k_completion_tokens",
                ]
                
                # 从 upstream 中提取可选字段
                for field in optional_fields:
                    if field in first_upstream:
                        metadata[field] = first_upstream[field]
                    elif field in model_conf:
                        metadata[field] = model_conf[field]
                
                config = ModelConfig(
                    model_name=model_name,
                    api_base=first_upstream.get("api_base", ""),
                    api_key=first_upstream.get("api_key", ""),
                    adapter=first_upstream.get("adapter") or model_conf.get("adapter", "openai"),
                    timeout=first_upstream.get("timeout") or model_conf.get("timeout", 60),
                    max_retries=first_upstream.get("max_retries") or model_conf.get("max_retries", 3),
                    metadata=metadata if metadata else None,
                )
                
                logger.debug(
                    f"获取负载均衡模型配置: {model_name} -> {len(model_conf['upstreams'])} 个上游, "
                    f"第一个: {config.api_base}"
                )
            else:
                # 单个上游配置
                # 构建 metadata，包含所有可选信息
                metadata = model_conf.get("metadata", {}) or {}
                
                # 将可选配置字段放入 metadata
                optional_fields = [
                    "max_tokens",
                    "max_input_tokens", 
                    "max_output_tokens",
                    "price_per_1k_prompt_tokens",
                    "price_per_1k_completion_tokens",
                ]
                
                for field in optional_fields:
                    if field in model_conf:
                        metadata[field] = model_conf[field]
                
                config = ModelConfig(
                    model_name=model_name,
                    api_base=model_conf.get("api_base", ""),
                    api_key=model_conf.get("api_key", ""),
                    adapter=model_conf.get("adapter", "openai"),
                    timeout=model_conf.get("timeout", 60),
                    max_retries=model_conf.get("max_retries", 3),
                    metadata=metadata if metadata else None,
                )
                
                logger.debug(
                    f"获取模型配置: {model_name} -> {config.api_base}, "
                    f"metadata={config.metadata}"
                )
            
            return config
        
        except Exception as e:
            logger.error(f"解析模型配置失败 {model_name}: {e}")
            return None
    
    async def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有配置的模型
        
        Returns:
            模型字典
        """
        result = {}
        
        for model_name, model_conf in self.models.items():
            result[model_name] = {
                "api_base": model_conf.get("api_base"),
                "adapter": model_conf.get("adapter", "openai"),
                "owned_by": model_conf.get("owned_by", "system"),
            }
        
        return result
    
    async def initialize(self):
        """初始化插件"""
        if not self.models:
            logger.warning("⚠️  未配置任何模型")
        else:
            logger.info(f"可用模型: {', '.join(self.models.keys())}")
    
    async def cleanup(self):
        """清理插件"""
        pass

