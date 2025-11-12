"""
自定义异常类
"""


class LLMOneAPIError(Exception):
    """LLM One API 基础异常"""
    
    def __init__(self, message: str, status_code: int = 500, error_type: str = "api_error"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(self.message)


class AuthenticationError(LLMOneAPIError):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401, error_type="authentication_error")


class PermissionError(LLMOneAPIError):
    """权限错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403, error_type="permission_error")


class ModelNotFoundError(LLMOneAPIError):
    """模型未找到错误"""
    
    def __init__(self, model_name: str):
        super().__init__(
            f"模型 {model_name} 未配置",
            status_code=404,
            error_type="model_not_found"
        )


class UpstreamError(LLMOneAPIError):
    """上游 API 错误"""
    
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code=status_code, error_type="upstream_error")


class RateLimitError(LLMOneAPIError):
    """限流错误"""
    
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, status_code=429, error_type="rate_limit_exceeded")


class ValidationError(LLMOneAPIError):
    """验证错误"""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_type="validation_error")

