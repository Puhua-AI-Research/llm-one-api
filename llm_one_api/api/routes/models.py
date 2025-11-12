"""
Models API 路由

实现 /v1/models 接口，兼容 OpenAI API
"""

from fastapi import APIRouter, Request, Depends
from typing import List

from llm_one_api.api.dependencies import get_plugin_manager, verify_api_key
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/models")
async def list_models(
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    列出所有可用的模型
    
    兼容 OpenAI /v1/models 接口
    """
    try:
        # 从插件管理器获取所有可用模型
        models = await plugin_manager.list_models()
        
        # 转换为 OpenAI 格式
        data = [
            {
                "id": model_name,
                "object": "model",
                "created": 1677610602,  # 固定时间戳
                "owned_by": model_info.get("owned_by", "system"),
            }
            for model_name, model_info in models.items()
        ]
        
        return {
            "object": "list",
            "data": data,
        }
    
    except Exception as e:
        logger.exception(f"获取模型列表失败: {e}")
        return {
            "object": "list",
            "data": [],
        }


@router.get("/models/{model_id}")
async def retrieve_model(
    model_id: str,
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    获取指定模型的详细信息
    
    兼容 OpenAI /v1/models/{model_id} 接口
    """
    try:
        model_config = await plugin_manager.get_model_config(model_id)
        
        if not model_config:
            return {
                "error": {
                    "message": f"模型 {model_id} 不存在",
                    "type": "model_not_found",
                }
            }
        
        return {
            "id": model_id,
            "object": "model",
            "created": 1677610602,
            "owned_by": model_config.get("owned_by", "system"),
        }
    
    except Exception as e:
        logger.exception(f"获取模型信息失败: {e}")
        return {
            "error": {
                "message": "内部服务器错误",
                "type": "internal_error",
            }
        }

