"""
日志统计插件

将请求和响应统计信息记录到日志
"""

import json
from typing import Dict, Any

from llm_one_api.plugins.interfaces.stats import StatsPlugin, RequestInfo, ResponseInfo
from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class LogStatsPlugin(StatsPlugin):
    """日志统计插件"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_format = config.get("format", "json")  # json 或 text
    
    async def record_request(self, request_info: RequestInfo):
        """
        记录请求信息到日志
        
        Args:
            request_info: 请求信息
        """
        if self.log_format == "json":
            log_data = {
                "event": "request",
                "request_id": request_info.request_id,
                "user_id": request_info.user_id,
                "model": request_info.model,
                "endpoint": request_info.endpoint,
                "stream": request_info.stream,
                "timestamp": request_info.timestamp.isoformat(),
            }
            logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            logger.info(
                f"请求 | ID={request_info.request_id} | "
                f"用户={request_info.user_id} | 模型={request_info.model} | "
                f"接口={request_info.endpoint} | 流式={request_info.stream}"
            )
    
    async def record_response(self, response_info: Dict[str, Any]):
        """
        记录响应信息到日志
        
        Args:
            response_info: 响应信息字典（简化版本）
        """
        token_usage = response_info.get("token_usage", {})
        metadata = response_info.get("metadata", {})  # 直接获取传递的 metadata
        
        
        if self.log_format == "json":
            # JSON 格式：包含完整的 token 详细信息
            log_data = {
                "event": "response",
                "model": response_info.get("model"),
                "user": response_info.get("user"),
                "endpoint": response_info.get("endpoint"),
                "stream": response_info.get("stream", False),
                "duration": response_info.get("duration", 0),
                "timestamp": response_info.get("timestamp"),
                "tokens": {
                    "prompt_tokens": token_usage.get("prompt_tokens", 0),
                    "completion_tokens": token_usage.get("completion_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0),
                }
            }
            
            # 添加模型限制信息
            if metadata:
                log_data["metadata"] = metadata

            
            logger.info(json.dumps(log_data, ensure_ascii=False, default=str))
        else:
            # 文本格式：清晰显示输入和输出 token
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            
            msg = (
                f"📊 响应统计 | "
                f"模型={response_info.get('model')} | "
                f"用户={response_info.get('user')} | "
                f"耗时={response_info.get('duration', 0):.2f}s | "
                f"输入Token={prompt_tokens} | "
                f"输出Token={completion_tokens} | "
                f"总Token={total_tokens} | "
                f"流式={response_info.get('stream')}"
            )
            
            logger.info(msg)
    
    async def initialize(self):
        """初始化插件"""
        logger.info(f"日志统计插件初始化，日志格式: {self.log_format}")
    
    async def cleanup(self):
        """清理插件"""
        pass

