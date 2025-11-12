"""
Embeddings API 路由

实现 /v1/embeddings 接口，兼容 OpenAI API
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from llm_one_api.models.request import EmbeddingRequest
from llm_one_api.api.dependencies import get_plugin_manager, verify_api_key
from llm_one_api.core.request_handler import RequestHandler
from llm_one_api.core.forwarder import NonStreamForwarder
from llm_one_api.utils.logger import setup_logger
from llm_one_api.utils.exceptions import LLMOneAPIError

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/embeddings")
async def create_embedding(
    request_data: EmbeddingRequest,
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    创建文本嵌入
    
    兼容 OpenAI /v1/embeddings 接口
    """
    try:
        logger.info(f"收到 embedding 请求: model={request_data.model}")
        
        # 获取模型路由配置
        model_config = await plugin_manager.get_model_config(request_data.model)
        if not model_config:
            return JSONResponse(
                status_code=404,
                content={"error": {"message": f"模型 {request_data.model} 未配置", "type": "model_not_found"}}
            )
        
        # 处理请求
        handler = RequestHandler(model_config)
        processed_request = handler.process_embedding_request(request_data)
        
        # Embedding 不支持流式，只有非流式
        forwarder = NonStreamForwarder(model_config, plugin_manager)
        response = await forwarder.forward_embedding(processed_request, auth_result)
        return response
    
    except LLMOneAPIError as e:
        logger.error(f"API 错误: {e}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"message": str(e), "type": e.error_type}}
        )
    
    except Exception as e:
        logger.exception(f"未预期的错误: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "内部服务器错误", "type": "internal_error"}}
        )

