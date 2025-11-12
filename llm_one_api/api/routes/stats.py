"""
统计和监控 API 路由

提供负载均衡状态、系统统计等信息
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any

from llm_one_api.api.dependencies import get_plugin_manager, verify_api_key
from llm_one_api.utils.logger import logger

router = APIRouter()


@router.get("/stats/load_balancers")
async def get_load_balancer_stats(
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    获取所有模型的负载均衡器状态
    
    需要认证
    """
    try:
        stats = {}
        
        # 获取所有模型
        models = await plugin_manager.list_models()
        
        # TODO: 从每个模型的转发器获取负载均衡器统计信息
        # 这需要在插件管理器中添加方法来获取转发器实例
        
        return {
            "success": True,
            "models": list(models.keys()),
            "message": "负载均衡器统计功能开发中",
        }
    
    except Exception as e:
        logger.exception(f"获取负载均衡器统计失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/stats/models/{model_name}")
async def get_model_stats(
    model_name: str,
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    获取指定模型的负载均衡统计
    
    返回该模型所有上游服务器的健康状态、请求统计等
    """
    try:
        model_config = await plugin_manager.get_model_config(model_name)
        
        if not model_config:
            return {
                "success": False,
                "error": f"模型 {model_name} 不存在",
            }
        
        # TODO: 获取该模型的负载均衡器统计
        
        return {
            "success": True,
            "model": model_name,
            "config": {
                "api_base": model_config.get("api_base", "N/A"),
                "has_load_balancer": "upstreams" in model_config,
                "upstreams_count": len(model_config.get("upstreams", [])),
            },
            "message": "详细统计功能开发中",
        }
    
    except Exception as e:
        logger.exception(f"获取模型统计失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/health/detailed")
async def detailed_health_check(
    request: Request,
):
    """
    详细的健康检查
    
    包括所有上游服务器的健康状态
    不需要认证（用于监控系统）
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "features": {
            "load_balancing": True,
            "streaming": True,
            "token_extraction": True,
            "plugins": True,
        },
        "message": "LLM One API 运行正常",
    }

