"""
Chat Completions API 路由

实现 /v1/chat/completions 接口，兼容 OpenAI API
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional

from llm_one_api.models.request import ChatCompletionRequest
from llm_one_api.models.response import ChatCompletionResponse
from llm_one_api.api.dependencies import get_plugin_manager, verify_api_key
from llm_one_api.core.request_handler import RequestHandler
from llm_one_api.core.forwarder import StreamForwarder, NonStreamForwarder
from llm_one_api.utils.logger import setup_logger
from llm_one_api.utils.exceptions import LLMOneAPIError

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/chat/completions")
async def create_chat_completion(
    request_data: ChatCompletionRequest,
    request: Request,
    plugin_manager=Depends(get_plugin_manager),
    auth_result=Depends(verify_api_key),
):
    """
    创建聊天补全
    
    兼容 OpenAI /v1/chat/completions 接口
    支持流式和非流式响应
    """
    try:
        logger.info(f"收到 chat completion 请求: model={request_data.model}, stream={request_data.stream}")
        
        # 获取模型路由配置
        model_config = await plugin_manager.get_model_config(request_data.model)
        if not model_config:
            return JSONResponse(
                status_code=404,
                content={"error": {"message": f"模型 {request_data.model} 未配置", "type": "model_not_found"}}
            )
        
        # 处理请求
        handler = RequestHandler(model_config)
        processed_request = handler.process_chat_request(request_data)
        
        # 流式响应
        if request_data.stream:
            forwarder = StreamForwarder(model_config, plugin_manager)
            stream_generator = forwarder.forward_chat_stream(processed_request, auth_result)
            return StreamingResponse(
                stream_generator,
                media_type="text/event-stream",
            )
        
        # 非流式响应
        else:
            forwarder = NonStreamForwarder(model_config, plugin_manager)
            response = await forwarder.forward_chat(processed_request, auth_result)
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

