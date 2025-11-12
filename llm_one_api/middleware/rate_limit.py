"""
限流中间件

防止 API 滥用
"""

import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from llm_one_api.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件（简单的内存实现）"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)  # user_id -> [timestamps]
    
    async def dispatch(self, request: Request, call_next):
        """
        检查用户请求频率
        """
        # 获取用户标识（从认证结果或IP）
        user_id = None
        if hasattr(request.state, "auth_result"):
            user_id = request.state.auth_result.get("user_id")
        
        if not user_id:
            user_id = request.client.host if request.client else "unknown"
        
        # 获取当前时间
        now = time.time()
        
        # 清理过期的请求记录（1分钟前的）
        cutoff_time = now - 60
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > cutoff_time
        ]
        
        # 检查是否超过限制
        if len(self.requests[user_id]) >= self.requests_per_minute:
            logger.warning(f"用户 {user_id} 超过请求频率限制")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "请求过于频繁，请稍后再试",
                        "type": "rate_limit_exceeded",
                    }
                }
            )
        
        # 记录本次请求
        self.requests[user_id].append(now)
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[user_id])
        )
        
        return response

