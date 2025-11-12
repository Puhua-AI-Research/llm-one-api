"""
日志中间件

记录每个请求的详细信息
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        """
        记录请求日志
        """
        start_time = time.time()
        
        # 记录请求开始
        logger.info(
            f"请求开始 | 方法={request.method} | 路径={request.url.path} | "
            f"客户端={request.client.host if request.client else 'unknown'}"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求结束
        logger.info(
            f"请求完成 | 方法={request.method} | 路径={request.url.path} | "
            f"状态码={response.status_code} | 耗时={process_time:.3f}s"
        )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

