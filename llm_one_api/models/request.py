"""
请求数据模型

定义 OpenAI API 兼容的请求格式
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union


class ContentPart(BaseModel):
    """多模态内容部分（文本或图片）"""
    type: str = Field(..., description="内容类型: text, image_url")
    text: Optional[str] = Field(None, description="文本内容")
    image_url: Optional[Dict[str, str]] = Field(None, description="图片 URL，格式: {url: ...}")
    
    class Config:
        extra = "allow"  # 允许额外字段，兼容未来扩展


class ChatMessage(BaseModel):
    """聊天消息（支持多模态）"""
    role: str = Field(..., description="角色: system, user, assistant")
    content: Union[str, List[ContentPart]] = Field(
        ..., 
        description="消息内容：字符串（纯文本）或数组（多模态内容，包含文本和图片）"
    )
    name: Optional[str] = Field(None, description="消息发送者名称")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求"""
    model: str = Field(..., description="模型名称")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    temperature: Optional[float] = Field(1.0, ge=0, le=2, description="温度参数")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="核采样参数")
    n: Optional[int] = Field(1, ge=1, description="生成的回复数量")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    max_tokens: Optional[int] = Field(None, description="最大生成 token 数")
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2, description="存在惩罚")
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2, description="频率惩罚")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="logit 偏置")
    user: Optional[str] = Field(None, description="用户标识")


class CompletionRequest(BaseModel):
    """文本补全请求"""
    model: str = Field(..., description="模型名称")
    prompt: Union[str, List[str]] = Field(..., description="提示文本")
    temperature: Optional[float] = Field(1.0, ge=0, le=2, description="温度参数")
    top_p: Optional[float] = Field(1.0, ge=0, le=1, description="核采样参数")
    n: Optional[int] = Field(1, ge=1, description="生成的回复数量")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    max_tokens: Optional[int] = Field(16, description="最大生成 token 数")
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2, description="存在惩罚")
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2, description="频率惩罚")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="logit 偏置")
    user: Optional[str] = Field(None, description="用户标识")
    suffix: Optional[str] = Field(None, description="后缀")
    echo: Optional[bool] = Field(False, description="是否回显提示")
    best_of: Optional[int] = Field(1, description="生成并返回最佳结果")
    logprobs: Optional[int] = Field(None, description="返回 logprobs")


class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    model: str = Field(..., description="模型名称")
    input: Union[str, List[str]] = Field(..., description="输入文本")
    user: Optional[str] = Field(None, description="用户标识")
    encoding_format: Optional[str] = Field("float", description="编码格式")

